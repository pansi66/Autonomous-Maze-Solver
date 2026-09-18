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
    V2.3
    Autonomous frontier exploration with BFS navigation.

    Strategy:
    1. Build a persistent map from confirmed movement and sensors.
    2. Explore locally when an unknown/unvisited edge exists.
    3. When local exploration is exhausted, use BFS through confirmed
       open edges to reach another unexplored frontier.
    4. Learn permanently from collisions.
    """

    # =========================================================
    # INITIALIZATION
    # =========================================================
    if "x" not in memory:
        memory["x"] = 0
        memory["y"] = 0
        memory["heading"] = "N"

        memory["visited"] = {(0, 0)}
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

        # Collision
        if sensors.get("accel_fwd") == -2.0:

            edge = (current, heading)

            memory["collisions"].add(edge)

            # Wall at current cell
            memory["walls"][current][heading] = True

            # Wall at opposite side of neighbor
            dx, dy = delta[heading]

            other = (
                x + dx,
                y + dy
            )

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

                new = (
                    x + dx,
                    y + dy
                )

                # Confirm open edge
                memory["walls"][old][heading] = False

                ensure_cell(new)

                memory["walls"][new][opposite[heading]] = False

                # Update position
                memory["x"] = new[0]
                memory["y"] = new[1]

                current = new

                memory["visited"].add(new)

    # =========================================================
    # PROCESS PREVIOUS TURN
    # =========================================================
    if last == "turn_right":
        heading = right_of[heading]

    elif last == "turn_left":
        heading = left_of[heading]

    memory["heading"] = heading

    # =========================================================
    # PENDING ACTION
    # =========================================================
    if memory["pending"]:

        action = memory["pending"].pop(0)

        memory["last_action"] = action

        return action

    # =========================================================
    # REFRESH
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
    # SENSOR WALL INFORMATION
    # =========================================================
    if sensors.get("dist_front", 0) == 0:
        memory["walls"][current][front] = True

    if sensors.get("dist_left", 0) == 0:
        memory["walls"][current][left] = True

    if sensors.get("dist_right", 0) == 0:
        memory["walls"][current][right] = True

    # =========================================================
    # HELPER:
    # IS THIS EDGE SAFE?
    # =========================================================
    def edge_allowed(pos, direction):

        if memory["walls"][pos][direction] is True:
            return False

        if (pos, direction) in memory["collisions"]:
            return False

        return True

    # =========================================================
    # HELPER:
    # BFS TO FRONTIER
    # =========================================================
    def find_frontier_path():

        from collections import deque

        queue = deque([current])

        came_from = {
            current: None
        }

        came_direction = {}

        target = None

        while queue:

            pos = queue.popleft()

            # A frontier is a visited cell with an unknown edge.
            if pos != current:

                cell = memory["walls"][pos]

                unknown_exists = False

                for d in directions:

                    if cell[d] is None:
                        unknown_exists = True
                        break

                if unknown_exists:

                    target = pos
                    break

            # Expand only through CONFIRMED open edges.
            cell = memory["walls"][pos]

            for direction in directions:

                if cell[direction] is not False:
                    continue

                dx, dy = delta[direction]

                nxt = (
                    pos[0] + dx,
                    pos[1] + dy
                )

                if nxt in came_from:
                    continue

                came_from[nxt] = pos
                came_direction[nxt] = direction

                queue.append(nxt)

        if target is None:
            return None

        # Reconstruct path.
        path = []

        node = target

        while node != current:

            path.append(
                came_direction[node]
            )

            node = came_from[node]

        path.reverse()

        return path

    # =========================================================
    # LOCAL EXPLORATION
    # =========================================================
    preferred = [
        right,
        front,
        left,
        back,
    ]

    # ---------------------------------------------------------
    # FIRST: UNVISITED SAFE CELL
    # ---------------------------------------------------------
    selected = None

    for direction in preferred:

        if not edge_allowed(
            current,
            direction
        ):
            continue

        dx, dy = delta[direction]

        nxt = (
            x + dx,
            y + dy
        )

        if nxt not in memory["visited"]:

            selected = (
                direction,
                nxt
            )

            break

    # ---------------------------------------------------------
    # SECOND: UNKNOWN EDGE
    # ---------------------------------------------------------
    if selected is None:

        for direction in preferred:

            if not edge_allowed(
                current,
                direction
            ):
                continue

            if memory["walls"][current][direction] is None:

                dx, dy = delta[direction]

                nxt = (
                    x + dx,
                    y + dy
                )

                selected = (
                    direction,
                    nxt
                )

                break

    # =========================================================
    # GLOBAL BFS
    # =========================================================
    if selected is None:

        path = find_frontier_path()

        if path:

            direction = path[0]

            dx, dy = delta[direction]

            nxt = (
                x + dx,
                y + dy
            )

            selected = (
                direction,
                nxt
            )

    # =========================================================
    # FALLBACK:
    # ANY SAFE KNOWN OPEN EDGE
    # =========================================================
    if selected is None:

        for direction in preferred:

            if memory["walls"][current][direction] is False:

                if (current, direction) in memory["collisions"]:
                    continue

                dx, dy = delta[direction]

                nxt = (
                    x + dx,
                    y + dy
                )

                selected = (
                    direction,
                    nxt
                )

                break

    # =========================================================
    # NOTHING FOUND
    # =========================================================
    if selected is None:

        # Special start handling.
        if current == (0, 0):

            memory["pending"] = [
                "turn_right",
                "forward",
            ]

            action = memory["pending"].pop(0)

            memory["last_action"] = action

            return action

        memory["last_action"] = "wait"

        return "wait"

    # =========================================================
    # FACE TARGET
    # =========================================================
    target_direction = selected[0]

    # ---------------------------------------------------------
    # FORWARD
    # ---------------------------------------------------------
    if target_direction == heading:

        action = "forward"

    # ---------------------------------------------------------
    # RIGHT
    # ---------------------------------------------------------
    elif target_direction == right_of[heading]:

        memory["pending"] = [
            "forward"
        ]

        action = "turn_right"

    # ---------------------------------------------------------
    # LEFT
    # ---------------------------------------------------------
    elif target_direction == left_of[heading]:

        memory["pending"] = [
            "forward"
        ]

        action = "turn_left"

    # ---------------------------------------------------------
    # BACK
    # ---------------------------------------------------------
    else:

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
