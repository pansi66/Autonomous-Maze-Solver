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
    V2.1
    Persistent map + bidirectional wall memory +
    collision learning + exploration/backtracking.
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

            # Remember this exact failed edge
            edge = (current, heading)
            memory["collisions"].add(edge)

            # Mark wall on current side
            memory["walls"][current][heading] = True

            # Mark opposite side on neighboring cell
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

                # Record successful edge
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
    # PROCESS TURN
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
    # BUILD CANDIDATES
    # =========================================================
    candidates = []

    # Right → Front → Left → Back
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

        # Previously collided with this edge
        if (current, direction) in memory["collisions"]:
            continue

        dx, dy = delta[direction]

        nxt = (x + dx, y + dy)

        candidates.append((direction, nxt))

    # =========================================================
    # PRIORITY 1: UNVISITED
    # =========================================================
    selected = None

    for direction, nxt in candidates:

        if nxt not in memory["visited"]:
            selected = (direction, nxt)
            break

    # =========================================================
    # PRIORITY 2: UNKNOWN
    # =========================================================
    if selected is None:

        for direction, nxt in candidates:

            if memory["walls"][current][direction] is None:
                selected = (direction, nxt)
                break

    # =========================================================
    # PRIORITY 3: BACKTRACK
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

        selected = (back_direction, parent)

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

        memory["last_action"] = "wait"

        return "wait"

    # =========================================================
    # TURN TOWARD TARGET
    # =========================================================
    target_direction = selected[0]

    if target_direction == heading:

        action = "forward"

    elif target_direction == right_of[heading]:

        memory["pending"] = ["forward"]

        action = "turn_right"

    elif target_direction == left_of[heading]:

        memory["pending"] = ["forward"]

        action = "turn_left"

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
