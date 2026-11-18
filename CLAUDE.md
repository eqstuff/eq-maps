# Working on eq-maps

Generates interactive guides for multi-level EverQuest zones from Brewall's map files. Read `README.md`, then `docs/DESIGN.md`; `docs/LESSONS.md` lists the traps.

* Build: `MAP_DIR=<maps dir> ./build.sh <zone>` (needs numpy, scipy, scikit-image, networkx). Output goes to `site/<zone>/`; commit it.
* All zone-specific knowledge belongs in `tools/zones/<zone>.py`. Don't hard-code floor heights or names in the generic tools.
* Run scripts with `python3 -I` and give the map directory as an argument; never run them from inside the data directory.
* After changing `model.py` or `route.py`, rebuild Arx Mentis and compare `routes.json` with the committed one; unexpected differences mean a regression. Differences caused by an intended change should be explained in the commit message.
* The compass/`/loc` orientation (MAP_FORMAT.md) is derived, not verified in the game client. Don't claim otherwise in page text.
* The front end is generated inside `build_guide.py` (CSS/JS strings, a Python f-string: braces in JS must go through the `JS` placeholder replacement, not the f-string).
* Locations are shown with `way()` (click-to-copy `/way Y, X, Z`), never bare `/loc` numbers; keep it that way so players are nudged to use waypoints.
