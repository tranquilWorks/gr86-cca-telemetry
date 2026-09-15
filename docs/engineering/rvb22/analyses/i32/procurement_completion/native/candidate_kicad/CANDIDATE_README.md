# GR86 CCA Rev B — I32 procurement redline

This is the native design for the frozen I32 procurement substitution set. The controlling handoff and pre-redline source remain preserved in git. Current verification, sourcing, package evidence and release bindings are under `../../analyses/i32/procurement_redline/`.

The source contains 177 fitted placements: 175 factory placements plus F101 and U401 local/manual installation. C203, R301 and R306 remain DNP. The 3.3 V feedback divider is 11.8 kΩ / 5.05 kΩ (PTFR0603B11K8N9 / PLT1206Z5051LBTS). R156 uses 1206 lands, R160 uses 0805 lands, and L121 uses the BPCI00121280 manufacturer land pattern.

U101 is LTC4367HMS8#PBF. The owner accepts removal of the #W controlled-manufacturing ordering option; electrical equivalence does not confer equivalent pedigree.

Project-specific footprints are in `libraries/RevB.pretty`. New STEP bodies prefixed `ENVELOPE_I32_PROCUREMENT_` are dimensionally bounded generic maximum-body envelopes, not manufacturer CAD. Standard KiCad models require KICAD6/7/9_3DMODEL_DIR to point to an installed KiCad 3D library. No physical assembly, thermal, vehicle or hardware validation is claimed by these files.
