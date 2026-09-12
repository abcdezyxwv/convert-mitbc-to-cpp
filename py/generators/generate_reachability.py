"""Python version of Parmesan-bc2026/scripts/generate_reachability.py
(via cpp/generators/generate_reachability.py).

Emits bc2026/src/bestsofar/Utils/Reachability.py instead of Reachability.java.
Translation rules per py/CONVENTIONS.md:

  Direction.NORTH                        -> Direction.NORTH (api singletons)
  Vision.isPassableWithDig(loc) /
    bestsofar.Utils.Vision.xxx           -> Vision.xxx
  rc.xxx (inherited Globals.rc static)   -> Globals.rc.xxx
  Vision.isReachable[x] |= 1L<<y         -> Vision.isReachable[x] |= 1 << y
  boolean canVisitN; (uninitialised)     -> canVisitN = False
  switch (direction) / case Direction.NORTH:
                                         -> if/elif chain on direction ==
  new IllegalArgumentException           -> ValueError

The dispatch parameter is `Direction` (as in the checked-in
src/bestsofar/Utils/Reachability.java and the ported C++), not the `String`
used by the older Java generator - see the port notes.
"""

from pathlib import Path
from queue import Queue

checkRadius = 20

# quarter name -> Direction enumerator used by the dispatch
QUARTER_DIRECTION = {
    "N": "NORTH",
    "E": "EAST",
    "S": "SOUTH",
    "W": "WEST",
    "NE": "NORTHEAST",
    "SE": "SOUTHEAST",
    "NW": "NORTHWEST",
    "SW": "SOUTHWEST",
}

def distance(dx: int, dy: int) -> int:
    return dx ** 2 + dy ** 2

def direction(dx: int, dy: int) -> str:
    horizontal = {
        -1: "WEST",
        0: "",
        1: "EAST"
    }[dx]

    vertical = {
        -1: "SOUTH",
        0: "",
        1: "NORTH"
    }[dy]

    return f"Direction.{vertical}{horizontal}"

def is_in_quarter(dx: int, dy: int, quarter: str) -> bool:
    """Check if (dx, dy) is in the specified quarter-circle."""
    if quarter == "N":
        # Bounded by y = x and y = -x, y >= 0
        return dy >= 0 and abs(dx) <= dy
    elif quarter == "S":
        # Bounded by y = x and y = -x, y <= 0
        return dy <= 0 and abs(dx) <= -dy
    elif quarter == "E":
        # Bounded by y = x and y = -x, x >= 0
        return dx >= 0 and abs(dy) <= dx
    elif quarter == "W":
        # Bounded by y = x and y = -x, x <= 0
        return dx <= 0 and abs(dy) <= -dx
    elif quarter == "NE":
        # Bounded by x = 0 and y = 0, dx >= 0, dy >= 0
        return dx >= 0 and dy >= 0
    elif quarter == "SE":
        # Bounded by x = 0 and y = 0, dx >= 0, dy <= 0
        return dx >= 0 and dy <= 0
    elif quarter == "NW":
        # Bounded by x = 0 and y = 0, dx <= 0, dy >= 0
        return dx <= 0 and dy >= 0
    elif quarter == "SW":
        # Bounded by x = 0 and y = 0, dx <= 0, dy <= 0
        return dx <= 0 and dy <= 0
    else:
        raise ValueError(f"Invalid quarter: {quarter}")

def generate_quarter_reachability(quarter: str) -> str:
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
    offsets = {}

    # Start with points within radius 2 that are in the quarter
    queue = Queue()
    for dx, dy in directions:
        if is_in_quarter(dx, dy, quarter):
            queue.put((dx, dy, 0, direction(dx, dy)))

    # BFS to explore points in the quarter-circle
    while not queue.empty():
        (dx, dy, previous_id, direction_from_previous) = queue.get()

        if (dx, dy) in offsets:
            continue

        # Skip if not in quarter-circle
        if not is_in_quarter(dx, dy, quarter):
            continue

        id = len(offsets) + 1
        neighbors_before = []
        outer_ring = False

        for direction_dx, direction_dy in directions:
            new_dx, new_dy = dx + direction_dx, dy + direction_dy

            # Skip if new point is not in the quarter-circle
            if not is_in_quarter(new_dx, new_dy, quarter):
                continue

            new_distance = distance(new_dx, new_dy)

            if new_distance < distance(dx, dy):
                if new_dx != 0 or new_dy != 0:
                    neighbors_before.append(offsets[(new_dx, new_dy)]["id"])
            elif new_distance <= checkRadius:
                queue.put((new_dx, new_dy, id, direction(direction_dx, direction_dy)))
            else:
                outer_ring = True

        offsets[(dx, dy)] = {
            "id": id,
            "previous_id": previous_id,
            "direction_from_previous": direction_from_previous,
            "outer_ring": outer_ring,
            "neighbors_before": neighbors_before,
            "neighbors_after": [],
        }

    # Generate neighbors_after
    for dx, dy in offsets:
        neighbors_after = offsets[(dx, dy)]["neighbors_after"]

        for direction_dx, direction_dy in directions:
            new_dx, new_dy = dx + direction_dx, dy + direction_dy

            # Skip if new point is not in the quarter-circle
            if not is_in_quarter(new_dx, new_dy, quarter):
                continue

            new_distance = distance(new_dx, new_dy)

            if new_distance >= distance(dx, dy) and new_distance <= checkRadius:
                neighbors_after.append(offsets[(new_dx, new_dy)]["id"])

    # Sort by distance
    offsets_by_distance = list(sorted(
        offsets.keys(),
        key=lambda item: distance(item[0], item[1])
    ))

    # Generate Python code for this quarter
    content = ""

    # Initialize points within radius 2
    for dx, dy in offsets_by_distance:
        data = offsets[(dx, dy)]
        id = data["id"]

        if distance(dx, dy) > 2:
            continue

        content += f"""
        location{id} = Globals.rc.adjacentLocation({data['direction_from_previous']})
        canVisit{id} = (Vision.hasSeenLocation(location{id}) and Vision.isPassableWithDig(location{id})) or Globals.rc.canMove({direction(dx, dy)})
        steppable{id} = (Vision.hasSeenLocation(location{id}) and Vision.isPassableWithDig(location{id}))
        """.rstrip() + "\n"

    # Initialize points beyond radius 2
    for dx, dy in offsets_by_distance:
        data = offsets[(dx, dy)]
        id = data["id"]

        if distance(dx, dy) <= 2:
            continue

        content += f"""
        location{id} = location{data['previous_id']}.add({data['direction_from_previous']})
        canVisit{id} = False
        steppable{id} = (Vision.hasSeenLocation(location{id}) and Vision.isPassableWithDig(location{id}))
        """.rstrip() + "\n"

    # Bellman-Ford updates
    hasDone = [False]*30

    for i, (side, ordered_offsets) in enumerate([
        ("before", offsets_by_distance),
        ("after", reversed(offsets_by_distance)),
        ("before", offsets_by_distance)
    ]):
        for dx, dy in ordered_offsets:
            data = offsets[(dx, dy)]
            id = data["id"]
            neighbors = data[f"neighbors_{side}"]

            if distance(dx, dy) <= 2:
                continue

            if len(neighbors) == 0:
                continue
            if hasDone[id]:

                content += f"        canVisit{id} = canVisit{id} or (steppable{id} and ("
                content += " or ".join([f"canVisit{neighbor}" for neighbor in neighbors])
                content += "))\n"

            else:

                hasDone[id] = True
                content += f"        canVisit{id} = (steppable{id} and ("
                content += " or ".join([f"canVisit{neighbor}" for neighbor in neighbors])
                content += "))\n"


    # Update reachability for all points
    all_ids = [data["id"] for data in offsets.values()]

    for id in all_ids:
        content += f"""
        if steppable{id}:
            if canVisit{id}:
                Vision.isReachable[location{id}.x] |= 1 << location{id}.y
            else:
                Vision.isReachable[location{id}.x] &= ~(1 << location{id}.y)

"""

    return content

def main() -> None:
    quarters = ["N", "E", "S", "W", "NE", "SE", "NW", "SW"]

    # Generate if/elif chain for each quarter (Java: switch on Direction)
    dispatch_cases = ""
    for i, quarter in enumerate(quarters):
        keyword = "if" if i == 0 else "elif"
        dispatch_cases += f"""
        {keyword} direction == Direction.{QUARTER_DIRECTION[quarter]}:
            Reachability.checkReachability{quarter.upper()}()
"""

    # Generate individual methods for each quarter
    quarter_methods = ""
    for quarter in quarters:
        quarter_code = generate_quarter_reachability(quarter)
        quarter_methods += f"""
    @staticmethod
    def checkReachability{quarter.upper()}():
{quarter_code.rstrip()}
"""

    # Combine everything into the final Python module
    content = f"""
# Generated by generators/generate_reachability.py
from api import *
from Utils.Globals import Globals
from Utils.Vision import Vision


class Reachability(Globals):
    # Individual quarter-circle reachability methods
{quarter_methods.rstrip()}

    # Main method that dispatches to the appropriate quarter-circle method
    @staticmethod
    def checkReachability(direction):
{dispatch_cases.rstrip()}
        else:
            raise ValueError("Invalid direction: " + str(direction))
    """.strip()

    output_dir = Path(__file__).resolve().parent.parent / "bc2026" / "src" / "bestsofar" / "Utils"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "Reachability.py"
    with output_file.open("w+", encoding="utf-8") as file:
        file.write(content.strip() + "\n")

if __name__ == "__main__":
    main()
