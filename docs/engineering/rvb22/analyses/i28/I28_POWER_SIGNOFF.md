# I28 electrical / power pre-fabrication signoff

**Disposition: PASS WITH PHYSICAL QUALIFICATION.**

U121 is changed from catalog LM5164DDAR to automotive-qualified LM5164QDDARQ1 (same DDA footprint and pin map; no routing change).

At the release 5 V burden of 2.3326875 W and an 80% efficiency floor, using a deliberately pessimistic 1.15 V D101 drop plus 0.125 ohm Q101 and 0.47 ohm R110 gives **10.688 V at U121 VIN from 12.0 V raw** and **0.273 A** input current. This remains comfortably above the LM5164-Q1 6 V minimum.

LTC4367 post-diode thresholds bound to UV trip **7.425-7.652 V**, UV re-enable **7.727-8.134 V**, and OV trip **19.700-20.300 V**. A deep 6 V crank therefore intentionally shuts the board down and it restarts after input recovery; continuous crank ride-through is not claimed.

For load dump, the protection controller and 200 V Q101 are the primary isolation mechanism. The 100 V buck rating is not used as permission to expose U121 directly to an unsuppressed raw load dump.

TI simulation packages were acquired. The LM5164-Q1 package relies on PSpice primitives unsupported by stock ngspice and the LM63615-Q1 package is Cadence-encrypted, so **no full vendor-macromodel SPICE pass is claimed**. I28 instead uses exact native connectivity plus guaranteed datasheet limits and conservative circuit bounds; physical startup/transient qualification remains mandatory.
