# Java -> C++ conventions

Every port in this repo follows the same rules so the C++ reads line-for-line
against the Java original.

## Naming / structure

- Java `public class Foo` -> `struct Foo` (or `class`) with `static` members in
  `Foo.hpp`, definitions in `Foo.cpp`.
- Java `package foo.bar` -> C++ namespace `foo::bar` (bc2025/bc2026 keep the
  `Roles`/`Utils` sub-namespaces).
- `Foo.staticField` / `Foo.staticMethod()` -> `Foo::field` / `Foo::method()`.
- `import battlecode.common.*` -> `#include "api.hpp"`.

## Types

- `MapLocation`, `MapInfo`, `RobotInfo`, `FlagInfo`, `Message` -> value structs
  with the same field/getter names.
- `null` for MapLocation/RobotInfo/etc. -> a `NONE`/`isNull()` sentinel member
  on the value type (`loc != null` -> `!loc.isNull()` / `loc == MapLocation::NONE`),
  so member access syntax `loc.x` is preserved.
- Java arrays (`MapInfo[]`, `RobotInfo[]`, `Direction[]`) -> `std::vector<T>`;
  `.length` -> `.size()`; `arr[i]` unchanged.
- `HashSet<T>` -> `std::unordered_set<T>` (hash specialisations live in
  `api.hpp`); `HashMap` -> `std::unordered_map`.
- `String` -> `std::string`; `String.valueOf(x)` -> `std::to_string(x)`;
  `System.out.println(x)` -> `std::cout << x << '\n'`.
- `java.util.Random` -> the small xorshift `Random` in `api.hpp`
  (`nextInt(bound)`), seeded identically - faster than `std::mt19937`.

## Engine API

- `RobotController` is a class with declarations only; `rc` is passed/kept by
  value so `rc.method()` call sites are untouched.
- `GameActionException` -> a `std::exception` subclass; `throws` clauses are
  dropped, `catch (GameActionException e)` -> `catch (const GameActionException& e)`.
- `Clock.yield()` -> `Clock::yield()` (no-op declaration).
- `Direction`/`UnitType`/`Team`/`TrapType`/... -> `enum class` accessed as
  `Direction::NORTH`; `Direction` additionally keeps `.dx`/`.dy` fields and
  `opposite()/rotateLeft()/rotateRight()/ordinal()` methods.
- `switch` on enums is kept; `case UnitType.BABY_RAT:` ->
  `case UnitType::BABY_RAT:`.

## Class hierarchy & files

- `class X extends Globals` -> `struct X : Globals` — this keeps unqualified
  references to `Globals` static members (`rc`, `rng`, ...) compiling.
- One Java file `dir/Foo.java` -> `src/<bot>/dir/Foo.hpp` + `Foo.cpp` (same
  relative subdirectories). Always `#pragma once` and `#include "api.hpp"`;
  cross-file includes are relative to `src/<bot>/`, e.g.
  `#include "Utils/Globals.hpp"`.
- All Java class members (public AND private) go in the `.hpp` as
  `static` members; implementations go in `.cpp`.
- `x.equals(y)` on enums/MapLocation/String -> `x == y`.
- `String.format(...)` -> `snprintf` or `std::to_string` concatenation.
- `StringBuilder` -> `std::string` with `+=` (or `+=` + `std::to_string`).
- Ternary/loops/if stay identical; `instanceof` -> a helper or type tag.
- `System.arraycopy` -> `std::memcpy`; `Arrays.fill` -> `std::fill_n`;
  `Arrays.sort` -> `std::sort`; `ArrayList` -> `std::vector`.
- `Direction.DIRECTION_ORDER` (bc2026) -> `Direction::DIRECTION_ORDER[i]`.
- `Clock.yield()` -> `Clock::yield()`.
- `int` -> `int`, `long` -> `int64_t`/`long long`, `boolean` -> `bool`,
  `double` -> `double`, `short` -> `int16_t`.
- Static-init-order trap: Java lazily initialises class statics on first use.
  For a static field initialised from `rng` or `rc`, make it lazily assigned
  on first use (e.g. sentinel + check) to match Java timing.

## Performance rules (bytecode <-> speed)

- Prefer `constexpr`/`inline` and plain arrays over containers where the Java
  used arrays; keep every int-packing/bit-trick intact.
- Range-for over sensed arrays uses `const T&` (no copies).
- No heap allocation where the Java had none; `std::vector` only where Java
  already allocated an array.
