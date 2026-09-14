# I32 160 MHz firmware closure evidence

This directory preserves a genuine ESP32-S3 target compilation of the unchanged adopted firmware at `CPUFreq=160`. `RESULT.json`, the source/tool inventories, verbose compiler log, split images, 8 MiB merged image, ELF/map, and preserved 28-check release result define the evidence.

The shell allowlist blocked Arduino's package indexes, so the same official Arduino CLI 1.3.1, Arduino-ESP32 3.3.6, ESP32-S3 libraries, GCC 14.2.0_20251107, esptool 5.1.0 and NimBLE-Arduino 2.3.6 were installed directly from their official GitHub release archives and verified by published SHA-256. Arduino's small `ctags` helper was built from the exact `arduino/ctags` 5.8-arduino11 tag with a macro-name compatibility edit for current glibc; this affects prototype discovery only and is disclosed in `TOOLCHAIN_INVENTORY.json`.

The ELF and linker map are stored losslessly as gzip files because the authenticated publication connector limits request bodies to 16 MiB; `IMAGE_MANIFEST.json` records both compressed containers and the original artifact identities, and `run_release_check.py` expands the ELF only in a temporary directory. The build was not flashed or executed on target hardware. It does not close supplier, assembly, vehicle, EMC, thermal-correlation, or first-article gates.
