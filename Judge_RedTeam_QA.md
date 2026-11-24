# HELIOS-R3: NASA Judge Red-Team Q&A Preparation Brief

1. **Q: How do you prevent vacuum cold-welding or dust jamming on the thermal control shutter?**
   **A:** HELIOS-R3 has zero high-temperature rotary bearings. Power regulation uses a single cylindrical molybdenum sleeve translated vertically along linear flexures on the **300 K cold side** (`24%` open at `1,660 K` to `86%` open at `1,250 K`), leaving `+10.5%` stroke reserve (`95%` max) for 10-year aging.

2. **Q: Sintered lunar regolith is a thermal insulator ($k \approx 0.15\text{ W/m}\cdot\text{K}$). How do you extract heat fast enough?**
   **A:** Embedding **32 radial SiC fins** and **3 concentric rings** limits conductive path length to `7.53 cm`, reducing characteristic thermal diffusion time from `3,130 hr` (8 fins) to **`38.2 hr`** (verified against `1,660 K` thermal stress with `FoS = 2.42x`).

3. **Q: What happens if a micrometeoroid punctures one of your four radiator wings?**
   **A:** Each wing uses Variable-Conductance Heat Pipes (VCHPs) with non-condensable gas reservoirs that passively isolate a punctured header. The remaining three wings (`48.88 m²`) reject the full `20.17 kW_th` load by rising from `300 K` to **`319.7 K` ($46.6^\circ\text{C}$)**, maintaining `100%` (`10.0 kWe`) electrical output.

4. **Q: How does HELIOS-R3 maintain `10.0 kWe` across a 10-year design life as TPV cells and mirrors degrade?**
   **A:** Across `5,000` Monte Carlo trials modeling TPV radiation aging (`0.35%/yr`), mirror dust degradation (`0.40%/yr`), and berm conductivity scatter, the cold-side sleeve opens slightly further (`89.1%` median at Year 10) to hold **`10.0 kWe` median End-of-Life output** (`100.0%` probability $\ge 9.8\text{ kWe}$).
