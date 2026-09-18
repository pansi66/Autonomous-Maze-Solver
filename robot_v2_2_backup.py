"""
Azisly Hackathon -- Round 2 submission template.

Rename this file to your team id (e.g. team17.py) and submit it. One file, Python 3,
standard library only.

You edit ONE function: decide(). Everything below the DO NOT EDIT line handles talking
to the grader for you -- you never have to think about processes or JSON.

Read CONTRACT.md first. It is short and it is the whole ruleset.
"""

import json
import sys


def decide(sensors, memory):
    """
    V2.2
    Persistent map + collision learning + BFS frontier planning.
    """

    # =========================================================
    # INITIALIZATION
    # =========================================================
    if "x" not in memory:
        memory["x"] = 0
        memory["y"] = 0
        memory["heading"] = "N"

        memory["visited"] = {(0, 0)}
        memory["parent"] = {}

        # walls[pos][direction]
        # True  = wall
        # False = known open
        # None  = unknown
        memory["walls"] = {}

        memory["last_action"] = None
        memory["pending"] = []

        memory["collisions"] = set()

    directions = ["N", "E", "S", "W"]

    delta = {
        "N": (0, -1),
        "E": (1, 0),
        "S": (0, 1),
        "W": (-1, 0),
    }

    left_of = {
        "N": "W",
        "W": "S",
        "S": "E",
        "E": "N",
    }

    right_of = {
        "N": "E",
        "E": "S",
        "S": "W",
        "W": "N",
    }

    opposite = {
        "N": "S",
        "E": "W",
        "S": "N",
        "W": "E",
    }

    # =========================================================
    # MAP HELPER
    # =========================================================
    def ensure_cell(pos):
        if pos not in memory["walls"]:
            memory["walls"][pos] = {
                "N": None,
                "E": None,
                "S": None,
                "W": None,
            }

    # =========================================================
    # CURRENT STATE
    # =========================================================
    x = memory["x"]
    y = memory["y"]
    heading = memory["heading"]

    current = (x, y)

    ensure_cell(current)

    # =========================================================
    # PROCESS PREVIOUS ACTION
    # =========================================================
    last = memory.get("last_action")

    # ---------------------------------------------------------
    # PREVIOUS FORWARD
    # ---------------------------------------------------------
    if last == "forward":

        # DEFINITE COLLISION
        if sensors.get("accel_fwd") == -2.0:
            print(
    f"COLLISION pos={current} heading={heading} "
    f"front={sensors.get('dist_front')} "
    f"left={sensors.get('dist_left')} "
    f"right={sensors.get('dist_right')}",
    file=sys.stderr,
    flush=True
)

            edge = (current, heading)
            memory["collisions"].add(edge)

            # Current side is a wall
            memory["walls"][current][heading] = True

            # Neighbor side is also a wall
            dx, dy = delta[heading]
            other = (x + dx, y + dy)

            ensure_cell(other)

            memory["walls"][other][opposite[heading]] = True

        else:

            rpm_l = sensors.get("rpm_left", 0)
            rpm_r = sensors.get("rpm_right", 0)

            moved = (
                rpm_l > 100
                and rpm_r > 100
                and sensors.get("accel_fwd", 0) > -1.5
            )

            if moved:

                dx, dy = delta[heading]

                old = (x, y)
                new = (x + dx, y + dy)

                # Successful edge
                memory["walls"][old][heading] = False

                ensure_cell(new)

                memory["walls"][new][opposite[heading]] = False

                # Update position
                memory["x"] = new[0]
                memory["y"] = new[1]

                current = new

                memory["visited"].add(new)

                if new not in memory["parent"]:
                    memory["parent"][new] = old

    # =========================================================
    # PROCESS PREVIOUS TURN
    # =========================================================
    if last == "turn_right":
        heading = right_of[heading]

    elif last == "turn_left":
        heading = left_of[heading]

    memory["heading"] = heading

    # =========================================================
    # EXECUTE PENDING ACTION
    # =========================================================
    if memory["pending"]:

        action = memory["pending"].pop(0)

        memory["last_action"] = action

        return action

    # =========================================================
    # REFRESH STATE
    # =========================================================
    x = memory["x"]
    y = memory["y"]
    heading = memory["heading"]

    current = (x, y)

    ensure_cell(current)

    # =========================================================
    # SENSOR DIRECTIONS
    # =========================================================
    front = heading
    left = left_of[heading]
    right = right_of[heading]
    back = opposite[heading]

    # =========================================================
    # DIRECT WALL OBSERVATIONS
    # =========================================================
    if sensors.get("dist_front", 0) == 0:
        memory["walls"][current][front] = True

    if sensors.get("dist_left", 0) == 0:
        memory["walls"][current][left] = True

    if sensors.get("dist_right", 0) == 0:
        memory["walls"][current][right] = True

    # =========================================================
    # START DEAD-END U-TURN
    # =========================================================
    if current == (0, 0):

        known = memory["walls"][current]

        if (
            known[front] is True
            and known[left] is True
            and known[right] is True
            and known[back] is None
        ):

            memory["pending"] = [
                "turn_right",
                "forward",
            ]

            action = memory["pending"].pop(0)

            memory["last_action"] = action

            return action

    # =========================================================
    # BFS HELPER
    # =========================================================
    def bfs_to_frontier():

        from collections import deque

        queue = deque()
        queue.append(current)

        came_from = {
            current: None
        }

        came_direction = {}

        target = None

        while queue:

            pos = queue.popleft()

            # Do not choose the current cell itself.
            if pos != current and pos in memory["visited"]:

                cell = memory["walls"].get(pos, {})

                has_unknown = any(
                    cell.get(d) is None
                    for d in directions
                )

                if has_unknown:
                    target = pos
                    break

            cell = memory["walls"].get(pos, {})

            for direction in directions:

                # Only travel through CONFIRMED open edges.
                if cell.get(direction) is not False:
                    continue

                dx, dy = delta[direction]
                nxt = (pos[0] + dx, pos[1] + dy)

                if nxt in came_from:
                    continue

                came_from[nxt] = pos
                came_direction[nxt] = direction

                queue.append(nxt)

        # No reachable frontier
        if target is None:
            return None

        # Walk backwards from target to current.
        path = []

        node = target

        while node != current:

            direction = came_direction[node]

            path.append(direction)

            node = came_from[node]

        path.reverse()

        if not path:
            return None

        return path[0]

    # =========================================================
    # BUILD LOCAL CANDIDATES
    # =========================================================
    candidates = []

    # Exploration preference:
    # Right -> Front -> Left -> Back
    preferred = [
        right,
        front,
        left,
        back,
    ]

    for direction in preferred:

        # Known wall
        if memory["walls"][current][direction] is True:
            continue

        # Previously collided edge
        if (current, direction) in memory["collisions"]:
            continue

        dx, dy = delta[direction]
        nxt = (x + dx, y + dy)

        candidates.append((direction, nxt))

    # =========================================================
    # PRIORITY 1:
    # MOVE INTO UNVISITED CELLS
    # =========================================================
    selected = None

    for direction, nxt in candidates:

        if nxt not in memory["visited"]:
            selected = (direction, nxt)
            break

    # =========================================================
    # PRIORITY 2:
    # EXPLORE UNKNOWN EDGES
    # =========================================================
    if selected is None:

        for direction, nxt in candidates:

            if memory["walls"][current][direction] is None:
                selected = (direction, nxt)
                break

    # =========================================================
    # PRIORITY 3:
    # BFS TO NEAREST KNOWN FRONTIER
    # =========================================================
    if selected is None:

        bfs_direction = bfs_to_frontier()

        if bfs_direction is not None:

            dx, dy = delta[bfs_direction]

            nxt = (
                x + dx,
                y + dy
            )

            selected = (
                bfs_direction,
                nxt
            )

    # =========================================================
    # PRIORITY 4:
    # OLD PARENT BACKTRACK
    # =========================================================
    if selected is None and current in memory["parent"]:

        parent = memory["parent"][current]

        px, py = parent

        dx = px - x
        dy = py - y

        if dx == 1:
            back_direction = "E"

        elif dx == -1:
            back_direction = "W"

        elif dy == 1:
            back_direction = "S"

        else:
            back_direction = "N"

        selected = (
            back_direction,
            parent
        )

    # =========================================================
    # NO MOVE
    # =========================================================
    if selected is None:

        if current == (0, 0):

            memory["pending"] = [
                "turn_right",
                "forward",
            ]

            action = memory["pending"].pop(0)

            memory["last_action"] = action

            return action

        # Safety fallback
        memory["last_action"] = "wait"

        return "wait"

    # =========================================================
    # TURN TOWARD TARGET
    # =========================================================
    target_direction = selected[0]

    # Already facing target
    if target_direction == heading:

        action = "forward"

    # Target is right
    elif target_direction == right_of[heading]:

        memory["pending"] = [
            "forward"
        ]

        action = "turn_right"

    # Target is left
    elif target_direction == left_of[heading]:

        memory["pending"] = [
            "forward"
        ]

        action = "turn_left"

    # Target is behind
    else:

        # 180 degree turn
        memory["pending"] = [
            "turn_right",
            "forward",
        ]

        action = "turn_right"

    memory["last_action"] = action

    return action

# =============================================================================
# DO NOT EDIT BELOW THIS LINE
# This is the plumbing that talks to the grader. Changing it will break your
# submission and score you zero.
# =============================================================================

def _main():
    print(json.dumps({"ready": True}), flush=True)
    memory = {}
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        sensors = json.loads(line)
        action = decide(sensors, memory)
        print(json.dumps({"action": action}), flush=True)
        if sensors.get("at_goal"):
            break


if __name__ == "__main__":
    _main()
