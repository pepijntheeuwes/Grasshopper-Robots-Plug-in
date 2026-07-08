# Grasshopper–UR5 Framework for Curved-Layer Robotic FDM

This repository accompanies the MSc thesis *"Manufacturability of Space-Time Topology Optimization (STTO) Curved-Layer Toolpaths on a Multi-Axis Robotic FDM Platform"* (TU Delft, ME56035). It contains the software, configuration files, and CAD models developed to stream STTO-generated, non-planar toolpaths to a UR5 CB3 6-DoF robot and to synchronize extrusion through a Duet 3 MB6HC controller, together with the validation pipeline used to score print accuracy.

This project is a fork of [visose/Robots](https://github.com/visose/Robots), a Grasshopper plugin for programming ABB, KUKA, UR, Staubli, Doosan, and Franka Emika robots. The base plugin has been extended with two additional Universal Robots motion primitives, `moveP` and `servoJ`, to support continuous-velocity, high-density waypoint streaming, which the standard `moveL`/`moveJ` commands cannot handle at the resolution required for curved-layer deposition.

## Repository contents

| Folder | Contents |
| --- | --- |
| [`src/Robots`](src/Robots) and [`src/Robots.Grasshopper`](src/Robots.Grasshopper) | The modified Robots plugin source, including the added `moveP` and `servoJ` UR motion commands used to drive the printhead through the curved-layer toolpath. |
| [`Grasshopper script`](Grasshopper%20script) | The Grasshopper definition (`servoj_ghScript_proxy.gh`) used to convert STTO waypoint data into `servoJ` targets and stream them to the robot, together with `robot_communicator_v2.py`, the companion Python script that runs the laptop-side TCP/IP proxy between the UR controller and the Duet board. |
| [`Robot Program`](Robot%20Program) | An example of the generated URScript output (`GH_program_3Dprinting.script`), showing the `servoJ` streaming program, lookahead time, gain, and payload/TCP configuration produced for a print run. |
| [`Duet config`](Duet%20config) | The Duet 3 MB6HC configuration files (`config.g`), defining the heater, network, and extrusion motor setup used for synchronized filament deposition. |
| [`Non-planar model`](Non-planar%20model) | An example waypoint file (`bracket.txt`) as exported by the STTO solver and used as input to the Grasshopper script: per-layer polylines of `x, y, thickness` triples that define the curved-layer toolpath. |
| [`Printheads`](Printheads) | CAD models (SolidWorks `.SLDPRT`) of the robot flange and the interchangeable printhead offset connectors (0°, 45°, 90°) used to evaluate different printhead orientations, plus the extruder holder. |
| [`Contour Comparer`](Contour%20Comparer) | `Contour_comparer_v2.py`, the shape-deviation validation script: it extracts part contours from flatbed scans via Otsu thresholding, aligns them to the reference model with ICP, and reports directed Hausdorff distance and shape-match metrics. |
| [`samples`](samples), [`docs`](docs), [`build`](build), [`tests`](tests), [`lib`](lib) | Retained from the upstream Robots plugin: general Grasshopper/Dynamo/Unity/WPF samples, documentation, build scripts, and unit tests unrelated to this thesis's experimental setup. |

## Grasshopper pipeline workflow

The end-to-end sequence for running a print job through this framework is as follows:

1. **Build the printhead** in Grasshopper using the CAD models under [`Printheads`](Printheads), assigning the correct offset connector (0°, 45°, or 90°) as the robot's tool.
2. **Define the print area** by TCP-probing the robot: jog the physical robot to the corners of the build plate and record the resulting TCP coordinates in the Grasshopper definition, so the toolpath is registered to the actual workspace rather than a nominal one.
3. **Load the model waypoint file** (a `.txt` file in the [`Non-planar model`](Non-planar%20model) format) into the Grasshopper script, which parses the per-layer `x, y, thickness` data exported by the STTO solver.
4. **Position the print** within the robot's workspace by translating and rotating the toolpath in Grasshopper until it falls inside the reachable, collision-free region defined in step 2.
5. **Simulate the program** in Grasshopper to check for collisions between the robot, the printhead, and the build plate across the full toolpath before anything is sent to physical hardware.
6. **Upload the generated robot program** to the UR5 controller (an example of this output is [`GH_program_3Dprinting.script`](Robot%20Program/GH_program_3Dprinting.script)).
7. **Start the listener script** on the laptop (`robot_communicator_v2.py`), which opens the TCP/IP proxy between the UR5 controller and the Duet board and must be running before the robot program executes.
8. **Start the robot program** on the UR5 teach pendant. The robot will connect outward to the laptop's proxy, which forwards extrusion commands to the Duet board in sync with the streamed waypoints.

## Hardcoded values — check before running on hardware

Several values in the pipeline are hardcoded in the script components rather than exposed as Grasshopper inputs. These must be checked and, where necessary, edited before any run on physical hardware:

- **TCP offset** (`set_tcp(...)` in [`Robot Program/GH_program_3Dprinting.script`](Robot%20Program/GH_program_3Dprinting.script)) and the **payload mass and center of gravity** (`set_payload(...)`) are hardcoded for the printhead configuration used at export time. A different printhead or offset connector requires these values to be updated, or the robot will track the wrong tool point.
- **Neutral/rest poses** — `rest_pose` and `levelpoint`, both defined as fixed joint-angle arrays in the same script — are used for homing and bed-leveling moves (`movej`/`movel` calls throughout the program). These are specific to the robot cell geometry at the time of recording and must be re-verified (or re-taught) if the robot base, build plate, or printhead geometry changes, to avoid a collision on the homing or leveling move.
- **`servoJ` parameters** (`global g = 300`, `global lt = 0.2`, i.e. gain and lookahead time) and the fixed timestep (`global time = 0.12`) govern TCP tracking behavior and are not passed in from Grasshopper. Changing waypoint density or travel speed without revisiting these values can push the controller outside the tracking regime the thesis validates.
- **Static network addresses** for the laptop and Duet sockets (`socket_open("172.19.126.244", 3000, ...)`, `socket_open("172.19.126.242", 23, ...)`) are hardcoded in the URScript program, and the matching `LAPTOP_IP`, `DUET_IP`, `WAYPOINT_PORT`, `DUET_PORT`, and `PROXY_PORT` values are hardcoded in `robot_communicator_v2.py`. These must match the actual IP addresses of the hardware in use (see networking note below).
- The **local file path to `print_data.json`** (`DATA_FILE` in `robot_communicator_v2.py`) is an absolute Windows path tied to the original development machine and must be updated to match the path on whichever laptop runs the listener script.

## Networking requirement

Every hardware component in the framework — the laptop running the listener/proxy script, the UR5 CB3 controller, and the Duet 3 MB6HC board — must be assigned a static IP address on the shared network. The UR5 controller and `robot_communicator_v2.py` connect to each other and to the Duet board using hardcoded IP addresses and ports (see above); if any device is issued a different address by DHCP between sessions, the socket connections in both the URScript program and the listener script will fail to establish.

## Thesis context

The toolpath streaming and validation pipeline in this repository was used to evaluate five STTO test geometries (Arc, L-shape, T-shape, Lug, Bracket) across three printhead configurations (A, B, C), and to derive a kinematic constraint on inter-waypoint angular displacement for curved-layer execution on a `servoJ`-based UR5 CB3 platform. See the thesis report for the full derivation, experimental results, and discussion of the method's transferability to Wire Arc Additive Manufacturing (WAAM).

## Requirements

- Rhino 7 or 8 (Windows or macOS) with Grasshopper, for the plugin and the `.gh` toolpath script.
- Python 3 with `socket`, `threading`, and `json` (standard library only) for `robot_communicator_v2.py`.
- Python 3 with `opencv-python`, `numpy`, `open3d`, `matplotlib`, `scipy`, `shapely`, and `Pillow` for `Contour_comparer_v2.py`.
- A UR5 CB3 controller and a Duet 3 MB6HC running RepRapFirmware, networked to the same host running the proxy script.

## Installation

1. Install the plugin in Rhino via the `_PackageManager` command, searching for `Robots`, or build it from [`src`](src) directly.
2. Restart Rhino and open Grasshopper; a `Robots` tab should appear.
3. Open `Grasshopper script/servoj_ghScript_proxy.gh` and load the UR5 robot library through the `Load robot system` component.
4. Run `Grasshopper script/robot_communicator_v2.py` on the laptop to start the TCP/IP proxy between the UR controller and the Duet board before streaming a job.

## License

Distributed under the MIT license, inherited from the upstream [visose/Robots](https://github.com/visose/Robots) project. See [`LICENSE`](LICENSE) and [`NOTICE`](NOTICE).
