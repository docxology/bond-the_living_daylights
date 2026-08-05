# References

<div id="refs"></div>

Citations appear inline as pandoc-citeproc keys (`[@key]`); the machine-readable
records are in [`references.bib`](references.bib). The full list, grouped by
what it backs in the code:

## External ballistics and sniper doctrine

1. McCoy, R. L. (1999). *Modern Exterior Ballistics: The Launch and Flight
   Dynamics of Symmetric Projectiles*. Atglen, PA: Schiffer Publishing.
   `[@mccoy1999]` — the point-mass quadratic-drag treatment and ballistic
   coefficient used by `ballistics.py`.
2. U.S. Department of the Army (1994). *FM 23-10: Sniper Training*.
   Washington, DC: Headquarters, Department of the Army. `[@fm2310sniper]` —
   mil-dot ranging and field-firing procedure behind `optics.py`.

## Countersniper detection and localization

3. Duckworth, G. L., Gilbert, D. C., & Barger, J. E. (1996). Acoustic
   counter-sniper system. *Proc. SPIE 2938: Command, Control, Communications,
   and Intelligence Systems for Law Enforcement*, 262–275.
   doi:10.1117/12.266747. `[@duckworth1996counter]`
4. Lédeczi, Á., Nádas, A., Völgyesi, P., Balogh, G., Kusy, B., Sallai, J., Pap,
   G., Dóra, S., Molnár, K., Maróti, M., & Simon, G. (2005). Countersniper
   system for urban warfare. *ACM Transactions on Sensor Networks*, 1(2),
   153–177. doi:10.1145/1105688.1105689. `[@ledeczi2005countersniper]` — both
   back the crossed-bearing localization in `countersniper.py`.
5. Van Trees, H. L. (1968). *Detection, Estimation, and Modulation Theory,
   Part I*. New York: John Wiley & Sons. `[@vantrees1968]` — the
   signal-detection formulation behind `glint_detection_probability`.
6. ASTM International (2020). *ASTM G173-03(2020): Standard Tables for
   Reference Solar Spectral Irradiances*. West Conshohocken, PA.
   `[@astmg173]` — the reference solar irradiance in the glint energy budget.
7. Kinsler, L. E., Frey, A. R., Coppens, A. B., & Sanders, J. V. (2000).
   *Fundamentals of Acoustics* (4th ed.). New York: John Wiley & Sons.
   `[@kinsler2000]` — the temperature-dependent speed of sound used for
   crack-bang ranging.

## Terrain visibility and routing

8. Bresenham, J. E. (1965). Algorithm for computer control of a digital
   plotter. *IBM Systems Journal*, 4(1), 25–30. doi:10.1147/sj.41.0025.
   `[@bresenham1965]` — the integer cell walk in `visibility.line_of_sight`.
9. Fisher, P. F. (1996). Extending the applicability of viewsheds in landscape
   planning. *Photogrammetric Engineering & Remote Sensing*, 62(11),
   1297–1302. `[@fisher1996viewshed]` — viewshed methodology.
10. Dijkstra, E. W. (1959). A note on two problems in connexion with graphs.
    *Numerische Mathematik*, 1(1), 269–271. doi:10.1007/BF01386390.
    `[@dijkstra1959]` — the least-cost route planner in `terrain_ops.py`.

## This package and its suite

11. Friedman, D. A. (2026). *The Living Daylights: SNIPER'S NEST —
    Special-Agent Mission Software* (v{{VERSION}}). PROJECT BOND suite, Active
    Inference Institute. Local-only working tree. `[@friedman2026sniper]`
12. PROJECT BOND (2026). *bond-api — the frozen mission protocol contract*
    (Phase 1 reference). PROJECT BOND suite, Active Inference Institute.
    `[@bondapi2026]`
