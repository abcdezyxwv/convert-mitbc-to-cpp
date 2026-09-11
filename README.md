# convert-to-cpp

C++ ports of the team's Battlecode bots. Game logic is preserved exactly; only
mechanical Java->C++ translation plus small speed/bytecode-neutral
optimisations were applied.

## Layout

- `bc2024/` - Yorkshire-Hippos, final bot `reechee` (Battlecode 2024)
- `bc2025/` - ilnz-bc2025, final bot `philip_06` (Battlecode 2025)
- `bc2026/` - Parmesan-bc2026, final bot `bestsofar` (Battlecode 2026)
- `generators/` - the Parmesan pathfinding/table generators, rewritten to emit
  C++ instead of Java (`bc2026/generated/` holds their output)

Each year directory contains:

- `api.hpp` - a minimal C++ shim of that year's `battlecode.common` API surface
  (types + the `RobotController` methods the bot calls). Engine calls are
  declarations only - there is no C++ engine, so each translation unit is
  compile-checked, not linked.
- `src/` - the ported bot, one `.hpp`/`.cpp` pair per Java class.
- `Makefile` - `make` syntax/compiles every translation unit with `-O2`.

See `CONVENTIONS.md` for the Java->C++ mapping rules used throughout.
