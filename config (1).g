; --- Network Configuration ---
if {network.interfaces[0].type = "ethernet"}
    M552 P0.0.0.0 S1
else
    M552 S1                                            ; Enable network
M586 P0 S1                                             ; Enable HTTP
M586 P1 S1                                             ; Enable FTP
M586 P2 S1                                             ; Enable Telnet (this is key for TCP)

M595 P0 R0 S20
; Enable PanelDue
M575 P1 S1 B57600

; --- Fan Configuration ---
M950 F0 C"out7"                                        ; Create fan #0
M106 P0 S0 L0 X1 B0.1 C"Part cooling"                  ; Configure fan #0
M950 F1 C"out8"                                        ; Create fan #1
M106 P1 S0 L0 X1 B0.1 H0 T50 C"Heater cooling"         ; Configure fan #1

; --- Heater Configuration ---
;M308 S0 P"temp0" Y"thermistor" A"Nozzle" T100000 B4725 C7.060000e-8 ; Define sensor #0
M308 S0 P"temp0" Y"thermistor" A"Nozzle" T100000 B4388 ; Define sensor #0

M950 H0 C"out1" T0                                     ; Create heater #0
M307 H0 R3.475 C90.8:84.3 D3.5 S1.00 V19.9             ; Heater tuning parameters
M143 H0 S300                                           ; Max temperature limit

; --- Virtual Axes Configuration (X, Y, Z) ---
M569 P0 S1                                             ; Virtual X-axis
M569 P1 S1                                             ; Virtual Y-axis
M569 P2 S1                                             ; Virtual Z-axis
M569 P3 S1                                             ; Virtual B-axis (rotation)

M584 X1 Y2 Z3 B4 E0                                    ; Map X, Y, Z, B as virtual and assign extruder to driver 0
M350 X16 Y16 Z16 B16 E16 I1                            ; Set microstepping
M92 X100 Y100 Z100 B100 E690                           ; Steps per mm (extruder value kept from original config)

; Define movement speeds for virtual axes
M203 X10000 Y10000 Z10000 B3600 E7200 I0.6             ; Max speed X-Y-Z-E (mm/min), B (rad/min), Min speed E 0.6 mm/min
M201 X500 Y500 Z500 B300 E3000                         ; Acceleration X-Y-Z-E (mm/s²), B (rad/s²)
M566 X200 Y200 Z200 B100 E300                          ; Jerk X-Y-Z-E (mm/min), B (rad/min)

; Set Axis Limits
M208 X0 Y0 Z0 B-3.14159 S1                             ; Set minimum (not needed but avoids errors)
M208 X500 Y500 Z500 B3.14159 S0                        ; Set maximum (adjust based on your working area)

; **Fix for Endstop Error** - Assign endstops to a non-existent pin
M574 X1 S1 P"nil"                                      ; Disable X endstop
M574 Y1 S1 P"nil"                                      ; Disable Y endstop
M574 Z1 S1 P"nil"                                      ; Disable Z endstop
M574 B1 S1 P"nil"                                      ; Disable B endstop

; Define the input pin (e.g., IO 1)
; Ensure the pin is not used elsewhere (like an endstop)
M574 P"nil"                 
; Define the Input Pin - check if your sensor requires a pull-up (^)
M950 J5 C"io5.in"                                      ; Create Input 5 on io5.in
; Link Input 1 to Trigger 2
M581 P5 T2 S1 R0                                       ; P5 refers to J1. T2 refers to trigger2.g. S1 = Rising Edge. R0 = Trigger any time.

; Initialize a global variable to track the current line
if !exists(global.line_count)
  global line_count = 0
else
  set global.line_count = 0                            ; Reset to 0 on every config load
  
; **Important: Allow Extrusion During X/Y Movement**
M302 P1                                                ; Allow extrusion even when below temperature (safety warning)

; --- Extruder Configuration ---
M569 P0.0 S1
M584 E0.0                                              ; Assign extruder driver
M92 E690                                               ; Steps per mm for extruder
M203 E7200                                             ; Max extruder speed (mm/min)
M566 E1000                                              ; Instantaneous speed change (jerk, mm/min)
M201 E3000                                             ; Extruder acceleration (mm/s²)
M906 E1200 I10                                         ; Motor current 1.2A, idle current 10%
M572 D0 S0.02                                          ; Pressure advance
M207 F7200 S1.5 Z0.2                                   ; Firmware retraction settings
M83                                                    ; relative extrusion mode

; --- Tool Configuration ---
M563 P0 D0 H0 F1 S"Robotic Head"                       ; Define tool 0 (extruder only)
G10 P0 S0 R0                                           ; Set tool 0 temperatures to 0

; --- Load Saved Parameters ---
M501                                                   ; Load previously stored settings