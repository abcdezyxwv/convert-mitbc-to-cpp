# Java → Python port conventions

Same contract as the C++ ports (see `cpp/CONVENTIONS.md`): preserve the Java
logic line-for-line; optimise only where it can never hurt speed/bytecode.
Python has real `null` (`None`), real exceptions and a GC, so the port is much
closer to the Java text than the C++ one.

## Layout

```
py/bcYYYY/api.py                    # battlecode.common shim for that year
py/bcYYYY/src/<bot>/<Pkg>/<Cls>.py  # one .py per .java, same relative path
```

Run/check with `python3 -m py_compile` (root `make py` does all of them).
Imports are always `from api import *` plus module-form imports of other bot
files: `import <Mod>` / `from <Pkg> import <Mod>`, referenced as
`<Mod>.<Cls>.member` (e.g. `from roles import Mopper` then
`Mopper.Mopper.moveTowards`). `from <Pkg>.<Mod> import <Cls>` is used only for
leaf modules that can never be part of an import cycle (Java resolves class
references lazily; Python class-form imports crash on cycles). Java
`package x.y;` becomes a directory; no `__init__.py` needed (namespace
packages) — `sys.path` is assumed to contain `py/bcYYYY` and `py/bcYYYY/src`.

## Type mapping

| Java | Python |
|---|---|
| `int/long/double` | `int`/`float` |
| `boolean` | `bool` (`True`/`False`) |
| `null` | `None` (test with `is None` / `is not None`) |
| `T[]` / `ArrayList` | `list` |
| `HashSet` / `HashMap` | `set` / `dict` |
| `StringBuilder` | `list` + `''.join`, or `+=` on `str` |
| `java.util.Random` | `api.Random` (xorshift, same class) |
| `public class X` (all-static bot class) | `class X:` with `@staticmethod`s and class-level fields |
| `class X extends Globals` | `class X(Globals)` — inherited class attrs are read *and* written through `Globals.` / the defining class name, **never** via `X.attr =` on the subclass, which would shadow it |
| `x.equals(y)` | `x == y` (`MapLocation`/`MapInfo`/etc. implement `__eq__`/`__hash__`) |
| Java `==` on `MapLocation`/objects | `is` — preserves Java reference semantics (e.g. `rc.getLocation() == attempt` stays always-`False`) |
| Java `==` on enums | `==` (enum members are singletons) |
| `instanceof` | `isinstance` |
| `switch` | `if`/`elif` chain or `match` |
| `throw new X()` | `raise X()`; `throws GameActionException` is dropped |
| `try/catch` | `try/except` |
| `Math.abs/min/max/sqrt` | `abs/min/max/math.sqrt` |
| `.length` (array) | `len(...)`; `.size()` → `len(...)`; `.get(i)` → `[i]`; `.add(x)` → `.append(x)`; `.isEmpty()` → `not x` |
| `x.getLast()` / `removeLast()` | `x[-1]` / `x.pop()` |
| `String.valueOf` / `Integer.parseInt` | `str` / `int` |
| `Clock.yield()` | `Clock.doYield()` (`yield` is a Python keyword) |
| `continue/return/break` | unchanged |
| `final` | dropped |
| `for (int i=a; i<b; i++)` | `for i in range(a, b)`; non-constant step → `while` |
| `for (T x : xs)` | `for x in xs` |

## Integer division and `%` — the one trap

Java `/` and `%` on ints **truncate toward zero**; Python `//`/`%` floor.
For operands that are provably non-negative, `//`/`%` are fine. Otherwise use
`int(a / b)` (trunc) and `a - int(a / b) * b` (C-style remainder) so the Java
behaviour is preserved. Never silently use `//` when the operand can be
negative.

Java integer overflow wraps to 32 bits; in the rare spot a Java `int` is meant
to wrap (hash packing, `nextInt` internals) mask with `& 0xFFFFFFFF` then
`if v >= 2**31: v -= 2**32` — or better, keep the value unbounded where the
logic never depended on wraparound.

## Performance rules (same spirit as the C++ port)

- `rc.*` calls cost "bytecode" in the engine — the multiset of `rc.*` calls
  must never grow. Hoisting an identical repeated call into a local is
  allowed only when the Java already computed it at least once on every path.
- No per-turn allocation the Java didn't have (Python allocates fast but it's
  still work). Keep list-comprehension/loop structure parallel to the Java.
- Keep every bit-packing trick, table, and magic constant verbatim.
- Comments from the Java are carried over; `// Java:` comments mark places
  where the translation had to make a choice (sentinels, deleted no-ops).

## Verification contract

`rc.*` call multisets per file must match the Java original (differences must
each be a documented safe hoist). `py_compile` must pass for every file.
