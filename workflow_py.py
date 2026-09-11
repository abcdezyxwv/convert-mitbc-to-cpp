import asyncio
import json

CONVENTIONS = "/home/ubuntu/repos/convert-to-cpp/py/CONVENTIONS.md"
OUT = "/home/ubuntu/repos/convert-to-cpp/py"

COMMON = f"""You are porting Battlecode bot Java source files to Python, one .py file per .java file.

Read /home/ubuntu/repos/convert-to-cpp/py/CONVENTIONS.md first — it is the contract. Also read the matching api.py shim for the year and the already-ported reference bot (/home/ubuntu/repos/convert-to-cpp/py/bc2024/src/reechee/) to see the expected style and fidelity level.

Rules:
- The port must be line-for-line faithful: same control flow, same call order, same constants. `rc.*` calls must match the Java exactly (same multiset per file) except documented safe hoists of an identical repeated call.
- `null` -> `None`; `.equals()` -> `==`; Java `==` on objects (reference identity) -> `is`. NEVER turn a Java `==` on two MapLocation/RobotInfo into `==` — that changes semantics.
- Java `x.y` where y is a public field -> `x.y` (the api classes expose both fields and getY() accessors; match whichever the Java used - prefer the same form as the Java: `.team` field reads stay field reads).
- All-static Java classes -> `class X:` with @staticmethods and class attributes; inside methods write `X.field` for reads AND writes of X's own fields.
- Class `X extends Globals` -> `class X(Globals)`; an assignment to an inherited static MUST be qualified with the defining class (`Globals.foo = ...`), never `X.foo = ...` (that would shadow).
- `Clock.yield()` -> `Clock.doYield()`. `System.out.println(x)` -> `print(x)`. `e.printStackTrace()` -> `traceback.print_exc()`.
- Java int division `/` truncates toward zero: use `//` only when operands are provably non-negative, else `int(a / b)`. Same for `%` on negatives.
- Imports: `from api import *` always; Java `import bestsofar.Utils.Globals;` -> `from Utils.Globals import Globals`; `import bestsofar.Utils.*;` -> one `from Utils.X import X` per class actually used; `import static Foo.bar` -> `from Foo import bar`. Module paths mirror the Java package (Utils/Globals.py for package bestsofar.Utils class Globals).
- Do NOT create __init__.py, do NOT create files other than the listed .py outputs, do NOT touch any file outside your assigned outputs, do NOT run git commands.
- Every output must pass `python3 -m py_compile`. Verify imports resolve names that actually exist (check the api.py + referenced class files' declared members).
- `java.util.Random` -> `Random` from api. `Integer.bitCount` -> `bin(x).count('1')`. `Math.min/max/abs/signum` -> min/max/abs/signum.
- Keep the Java comments; mark translation choices with `# Java:` comments only where the Java did something non-obvious (always-false `==`, dead code, etc.).

When done, report files (list of .py paths written) and notes (anything that needed a judgment call)."""


def task(files, year, bot, srcroot):
    lines = []
    for f in files:
        out = f"{OUT}/{year}/src/{bot}/{f[:-5]}.py"
        lines.append(f"  {srcroot}/{f}  ->  {out}")
    return "\n".join(lines)


def prompt(files, year, bot, srcroot):
    return COMMON + f"""

Your files (java -> py):
{task(files, year, bot, srcroot)}

The C++ port of the same bot exists under /home/ubuntu/repos/convert-to-cpp/cpp/{year}/src/{bot}/ - consult it when a Java construct needs a design decision, but port FROM THE JAVA, matching its exact call sequence."""


SCHEMA = {
    "type": "object",
    "properties": {
        "files": {"type": "array", "items": {"type": "string"}},
        "notes": {"type": "string"},
    },
    "required": ["files", "notes"],
}

J25 = "/home/ubuntu/repos/ilnz-bc2025-converted/src/philip_06"
J26 = "/home/ubuntu/repos/Parmesan-bc2026/src/bestsofar"

BATCHES = [
    # (files, year, bot, srcroot, label)
    (["RobotPlayer.java", "utils/Actions.java", "utils/Constants.java",
      "utils/Random.java", "utils/Settings.java", "utils/Utils.java",
      "Helper/Comms.java", "Helper/Communication.java", "Helper/Pathfind.java"],
     "bc2025", "philip_06", J25, "b25-core"),
    (["Soldier.java", "SoldierState/Attack.java", "SoldierState/Build.java",
      "SoldierState/Fill.java", "SoldierState/Messenger.java",
      "SoldierState/Retreat.java"],
     "bc2025", "philip_06", J25, "b25-soldier"),
    (["roles/Mopper.java"], "bc2025", "philip_06", J25, "b25-mopper"),
    (["roles/Splasher.java", "roles/Tower.java", "Pathfinding.java"],
     "bc2025", "philip_06", J25, "b25-rest"),
    (["Utils/Attack.java"], "bc2026", "bestsofar", J26, "b26-attack"),
    (["Utils/Globals.java", "Utils/Comms.java"], "bc2026", "bestsofar", J26, "b26-globals"),
    (["Utils/BugNavigator.java", "Utils/CatsAreWalls.java", "Utils/FastSet.java",
      "Utils/Movement.java", "Utils/Navigator.java", "Utils/Symmetry.java",
      "Utils/Vision.java"], "bc2026", "bestsofar", J26, "b26-nav"),
    (["Roles/AntiCat.java", "Roles/Hunter.java", "Roles/Miner.java",
      "Roles/Multiking.java", "Roles/Rush.java", "Baby.java", "RobotPlayer.java"],
     "bc2026", "bestsofar", J26, "b26-roles"),
    (["King.java", "Utils/AdditionalClasses/Threat.java",
      "Utils/AdditionalClasses/Thrown.java"], "bc2026", "bestsofar", J26, "b26-king"),
]

GEN_PROMPT = COMMON + """

Special task: convert the three C++-emitting generators in
/home/ubuntu/repos/convert-to-cpp/cpp/generators/ into Python-emitting
generators saved at /home/ubuntu/repos/convert-to-cpp/py/generators/
(same filenames). Each generator must emit a Python .py file (into
/home/ubuntu/repos/convert-to-cpp/py/bc2026/generated/) that is the
line-for-line Python port of the Java file the ORIGINAL generator emitted
(it still lives at {J26}/Utils/<Name>.java - compare against it).

The generated class is a static class like the Java (`class X:` +
`@staticmethod`), module lives at py/bc2026/generated/<Name>.py, importing
`from api import *` and `from Utils.Globals import Globals`, `from Utils.Vision import Vision` etc. as the Java did. Inside generated methods, `rc.` refers to `Globals.rc` (as the Java static field) - check how the generated Java accesses rc and mirror it.

Run each generator (`python3 py/generators/<name>.py`) and verify the output
compiles with py_compile and that the `rc.*` call multiset matches the
original generated Java file (script it: grep -oE 'rc\\.[a-zA-Z_]+' both, sort, uniq -c, diff). Report files + notes."""


async def main():
    await register_workflow({
        "name": "java-to-py-port",
        "description": "Port philip_06 + bestsofar Java bots to Python + generators",
        "phases": [
            {"title": "port-bc2025", "detail": "philip_06 -> py", "count": 4},
            {"title": "port-bc2026", "detail": "bestsofar -> py", "count": 5},
            {"title": "generators", "detail": "generators emit python", "count": 1},
        ],
        "soft_time_limit_minutes": 30,
    })
    thunks = []
    for files, year, bot, srcroot, label in BATCHES:
        phase = "port-" + year
        thunks.append((lambda f=files, y=year, b=bot, s=srcroot, p=phase, l=label:
                       agent(prompt(f, y, b, s), phase=p, schema=SCHEMA, label=l,
                             vm_mode="shared"))())  # shared: outputs land directly in this working tree
    thunks.append(agent(GEN_PROMPT, phase="generators", schema=SCHEMA,
                        label="generators", vm_mode="shared"))
    results = await parallel(thunks)
    for (files, year, bot, _s, label), res in zip(BATCHES, results):
        log(f"{label}: {res['files']} notes={res['notes'][:200]}")
    log(f"generators: {results[-1]['files']}")


asyncio.run(main())
