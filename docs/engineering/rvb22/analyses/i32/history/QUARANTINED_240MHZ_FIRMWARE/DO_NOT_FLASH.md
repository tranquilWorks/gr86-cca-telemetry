# Historical 240 MHz build — not a release image

These bytes are preserved only as prior evidence. The recorded compile used CPUFreq=240, but the I25 release thermal profile requires 160 MHz. Matching source hashes alone did not establish build-profile compatibility. Rebuild with the repaired runner/build.sh, keep the new compiler record, and pass target binary release checks. No flashing is authorized by this recovery.

The historical ELF is stored losslessly as `cca_telemetry.ino.elf.gz` to remain within the authenticated publication connector's 16 MiB request ceiling. This transport compression does not make the quarantined 240 MHz image releasable.
