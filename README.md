# convert-mitbc-to-cpp

C++ and Python ports of the team's Battlecode bots. Game logic is preserved
exactly; only mechanical Java translation plus small speed/bytecode-neutral
optimisations were applied.

## Layout

- `cpp/bc2024/` - Yorkshire-Hippos, final bot `reechee` (Battlecode 2024)
- `cpp/bc2025/` - ilnz-bc2025, final bot `philip_06` (Battlecode 2025)
- `cpp/bc2026/` - Parmesan-bc2026, final bot `bestsofar` (Battlecode 2026)
- `py/bc2024|bc2025|bc2026/` - the same three bots ported to Python
- `cpp/generators/`, `py/generators/` - the Parmesan pathfinding/table
  generators, rewritten to emit C++ / Python instead of Java
  (generated output lives in `cpp/bc2026/generated/` for C++ and in
  `py/bc2026/src/bestsofar/Utils/` for Python, matching the Java package layout)

Each year directory contains:

- `api.hpp` / `api.py` - a minimal shim of that year's `battlecode.common` API
  surface (types + the `RobotController` methods the bot calls). Engine calls
  are stubs only - there is no C++/Python engine, so the C++ is compile-checked
  (`-fsyntax-only`, not linked) and the Python is `py_compile` + import checked.
- `src/` - the ported bot, one file per Java class.
- `Makefile` (C++) - `make` syntax-checks every translation unit with `-O2`.

Run `make` at the root to check everything (C++ compiles + Python compiles).

See `cpp/CONVENTIONS.md` and `py/CONVENTIONS.md` for the Java->C++ and
Java->Python mapping rules used throughout.
