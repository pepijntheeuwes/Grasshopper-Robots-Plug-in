; ==========================================
; Duet 3 MB 6HC - Config
; Extruder + Nozzle heater + Bed heater
; ==========================================

; --- Network ---
if {network.interfaces[0].type = "ethernet"}
    M552 P0.0.0.0 S1
else
    M552 S1
M586 P0 S1                                             ; Enable HTTP
M586 P2 S1                                             ; Enable Telnet (TCP)
M586 P1 S0                                             ; Explicitly DISABLE FTP
M575 P1 S0                                             ; Disable PanelDue

; --- Heater Configuration ---
M308 S0 P"temp0" Y"thermistor" A"Nozzle" T100000 B4388  ; Nozzle thermistor (temp0)
M950 H0 C"out1" T0                                     ; Nozzle heater on out1
M307 H0 R3.475 C90.8:84.3 D3.5 S1.00 V19.9             ; Nozzle heater tuning
M143 H0 S300                                           ; Nozzle max temp

M308 S1 P"temp1" Y"thermistor" A"Bed" T100000 B3950    ; Bed thermistor (temp1)
M950 H1 C"out0" T1                                     ; Bed heater on out0
M307 H1 R0.327 K0.524:0.000 D4.57 E1.35 S1.00 B0       ; Bed heater tuning (run M303 H1 S60)
M143 H1 S120                                           ; Bed max temp
M140 H1                                                ; Map bed to heater #1

; --- Fan Configuration ---
M950 F0 C"out7"                                        ; Part cooling fan (out7)
M106 P0 S0 L0 X1 B0.1 C"Part cooling"                  ; Part cooling - controlled via slicer

M950 F1 C"out8"                                        ; Heatsink fan (out8)
M106 P1 S1 L0 X1 B0.1 H0 T50 C"Heatsink"              ; Heatsink fan - auto on at 50°C

; --- Extruder & Motor Configuration ---
M569 P0.0 S1                                           ; Extruder driver direction
M584 E0.0                                              ; Assign extruder to driver 0
M350 E16 I1                                            ; 16x microstepping
M92 E690                                               ; Steps per mm
M203 E7200                                             ; Max speed (mm/min)
M566 E1000                                             ; Jerk (mm/min)
M201 E3000                                             ; Acceleration (mm/s²)
M906 E1200 I10                                         ; Motor current 1.2A, idle 10%
M572 D0 S0.02                                          ; Pressure advance
M207 F7200 S1.5 Z0.2                                   ; Firmware retraction
M302 P1                                                ; Allow cold extrusion
M83                                                    ; Relative extrusion mode

; --- Tool Definition ---
M563 P0 D0 H0 F0 S"Extruder"                           ; Tool 0: extruder, nozzle heater, part cooling fan
G10 P0 S0 R0                                           ; Tool 0 temps to 0
T0                                                     ; Auto-select tool 0 on startup

; --- FIX: Disable motor idle timeout ---
; Prevents the Duet from going idle during extrusion-only moves
; (no XYZ motion means the idle timer can fire mid-print)
M18 S0                                                 ; Never time out / disable stepper idle timeout

; --- FIX: Increase GCode input buffer depth ---
; Raises the number of queued GCode commands to reduce starvation risk
; during high-frequency TCP streaming from the UR5
M595 P3 S16                                            ; Set GCode channel 3 (Telnet/TCP) queue depth to 16

; --- Load Saved Parameters ---
M501
