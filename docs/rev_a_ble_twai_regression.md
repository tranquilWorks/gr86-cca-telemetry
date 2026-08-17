# Rev A BLE/TWAI regression firmware branch

This branch contains the firmware changes discovered during the first fabricated Rev A CCA bring-up.
It does **not** repair the PCB defects; the heavily bodged prototype still requires its external 3.3 V/5 V
rail injections, EN/GPIO0 programming bodges, correctly oriented PA1616D, and crossed GPS UART wires.

## Functional changes

- Advertises the explicit `CAN Telemetry` name and compact 16-bit RaceChrono service UUID `0x1FF8`.
- Disables BLE bonding/passkey pairing by default; FIL writes remain protected by the existing application token.
- Handles one actual BLE disconnect once instead of continuously restarting while no phone is connected.
- A BLE disconnect no longer invalidates CAN/GPS/oil state or forces GPS reinitialization.
- Disables forced 7.5-15 ms connection-parameter requests by default for iOS stability.
- Uses `BAUD_RATE` as the single TWAI bitrate source and compiles physical CAN writes out by default.
- Leaves TWAI in normal mode so the CCA ACKs frames on a two-node CANgaroo/CANable bench.
- Creates a non-zero FIL token on virgin NVS instead of printing `00000000` forever.
- Adds `SHOW CAN`, `SHOW GPS`, and `SHOW OIL` diagnostics.
- Removes the unused `esp_gatt_defs.h` dependency that broke the ESP32-S3 Arduino build.

## Known-good build baseline

- Board: `ESP32S3 Dev Module` (`esp32:esp32:esp32s3`)
- Arduino-ESP32 core: **3.3.6**
- Vendored NimBLE-Arduino: **2.3.6**
- Serial: 115200 8N1

Do not upgrade Arduino-ESP32 and NimBLE independently during CAN/oil regression. NimBLE 2.3.6 crashed
at BLE initialization with newer Arduino core combinations during bring-up.

## First phone test

Because iOS may retain the old bond created by the previous firmware, forget `CAN Telemetry` once in iOS
Bluetooth settings before the first test of this branch. A clean connection should not request a passkey or
require the former **Pair, then Cancel the second prompt** workaround.

## Remaining evidence-dependent work

The GR86 PID equations/IDs are deliberately unchanged here. Reconcile them against Timurr's Gen2 notes,
CANgaroo captures, and RaceChrono values only after the physical CAN regression test. Likewise, do not replace
the oil calibration defaults until FY6900 measurements establish the real ADC-side endpoints.
