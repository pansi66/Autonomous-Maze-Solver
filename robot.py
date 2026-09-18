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
    V2.0
    - Tracks position and heading
    - Builds a persistent local map
    - Remembers walls
    - Learns from collisions
    - Explores unvisited cells
    - Backtracks when necessary
    """

    # ---------------------------------------------------------
    # INITIALISE MEMORY
    # ---------------------------------------------------------
    if "x" not in memory:
        memory["x"] = 0
        memory["y"] = 0
        memory["heading"] = "N"

        memory["visited"] = {(0, 0)}
        memory["parent"] = {}

        # walls[(x, y)] = {"N": None, "E": None, "S": None, "W": None}
        memory["walls"] = {}

        memory["last_action"] = None
        memory["pending"] = []

    x = memory["x"]
    y = memory["y"]
    heading = memory["heading"]

    current = (x, y)

    # ---------------------------------------------------------
    # HELPERS
    # ---------------------------------------------------------
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

    # ---------------------------------------------------------
    # CREATE MAP ENTRY
    # ---------------------------------------------------------
    if current not in memory["walls"]:
        memory["walls"][current] = {
            "N": None,
            "E": None,
            "S": None,
            "W": None,
        }

    # ---------------------------------------------------------
    # PROCESS RESULT OF PREVIOUS ACTION
    # ---------------------------------------------------------
    last = memory.get("last_action")

    if last == "forward":

        # Collision = definite wall
        if sensors.get("accel_fwd") == -2.0:
            memory["walls"][current][heading] = True

            # Also remember wall from the other side
            dx, dy = delta[heading]
            other = (x + dx, y + dy)

            if other not in memory["walls"]:
                memory["walls"][other] = {
                    "N": None,
                    "E": None,
                    "S": None,
                    "W": None,
                }

            memory["walls"][other][opposite[heading]] = True

        else:
            # Check whether forward actually moved.
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

                memory["x"] = new[0]
                memory["y"] = new[1]

                memory["visited"].add(new)

                if new not in memory["parent"]:
                    memory["parent"][new] = old

                current = new

                if current not in memory["walls"]:
                    memory["walls"][current] = {
                        "N": None,
                        "E": None,
                        "S": None,
                        "W": None,
                    }

    # ---------------------------------------------------------
    # PROCESS TURN
    # ---------------------------------------------------------
    if last == "turn_right":
        heading = right_of[heading]

    elif last == "turn_left":
        heading = left_of[heading]

    memory["heading"] = heading

    # ---------------------------------------------------------
    # IF A PREVIOUSLY PLANNED ACTION EXISTS
    # ---------------------------------------------------------
    if memory["pending"]:
        action = memory["pending"].pop(0)
        memory["last_action"] = action
        return action

    # ---------------------------------------------------------
    # CURRENT CELL AFTER MOVEMENT / TURN
    # ---------------------------------------------------------
    x = memory["x"]
    y = memory["y"]
    heading = memory["heading"]
    current = (x, y)

    if current not in memory["walls"]:
        memory["walls"][current] = {
            "N": None,
            "E": None,
            "S": None,
            "W": None,
        }

    # ---------------------------------------------------------
    # CONVERT SENSOR DIRECTIONS
    # ---------------------------------------------------------
    front = heading
    left = left_of[heading]
    right = right_of[heading]

    # Sensor observations.
    #
    # 0 means definitely blocked.
    # >0 means potentially open.
    #
    # We only permanently trust a collision as a wall because
    # the contract allows noisy distance readings.

    if sensors.get("dist_front", 0) == 0:
        memory["walls"][current][front] = True

    if sensors.get("dist_left", 0) == 0:
        memory["walls"][current][left] = True

    if sensors.get("dist_right", 0) == 0:
        memory["walls"][current][right] = True

    # ---------------------------------------------------------
    # INITIAL START DEAD-END / U-TURN
    # ---------------------------------------------------------
    if current == (0, 0):

        known = memory["walls"][current]

        if (
            known[front] is True
            and known[left] is True
            and known[right] is True
            and known[opposite[heading]] is None
        ):
            memory["pending"] = [
                "turn_right",
                "forward",
            ]

            action = memory["pending"].pop(0)
            memory["last_action"] = action
            return action

    # ---------------------------------------------------------
    # BUILD AVAILABLE DIRECTIONS
    # ---------------------------------------------------------
    options = []

    # Prefer right, then front, then left, then backward.
    preferred = [
        right,
        front,
        left,
        opposite[heading],
    ]

    for direction in preferred:

        # Known wall → don't use it.
        if memory["walls"][current][direction] is True:
            continue

        dx, dy = delta[direction]
        nxt = (x + dx, y + dy)

        options.append((direction, nxt))

    # ---------------------------------------------------------
    # FIRST PRIORITY: UNVISITED CELL
    # ---------------------------------------------------------
    selected = None

    for direction, nxt in options:
        if nxt not in memory["visited"]:
            selected = (direction, nxt)
            break

    # ---------------------------------------------------------
    # SECOND PRIORITY: ANY UNKNOWN PATH
    # ---------------------------------------------------------
    if selected is None:
        for direction, nxt in options:
            if memory["walls"][current][direction] is None:
                selected = (direction, nxt)
                break

    # ---------------------------------------------------------
    # THIRD PRIORITY: BACKTRACK
    # ---------------------------------------------------------
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

    # ---------------------------------------------------------
    # NO KNOWN MOVE
    # ---------------------------------------------------------
    if selected is None:

        # At the starting point, force exploration backward
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

    # ---------------------------------------------------------
    # DETERMINE HOW TO TURN TOWARD TARGET
    # ---------------------------------------------------------
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
        # 180-degree turn
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
