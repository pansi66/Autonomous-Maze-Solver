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
    V1.1:
    Position + heading + visited cells + parent/backtracking.

    Important improvement:
    A turn is followed by a forward movement instead of allowing
    the robot to immediately choose another turn.
    """

    # =========================================================
    # INITIAL MEMORY
    # =========================================================

    if "x" not in memory:
        memory["x"] = 0
        memory["y"] = 0

        # 0 = North
        # 1 = East
        # 2 = South
        # 3 = West
        memory["heading"] = 0

        memory["last_action"] = None

        memory["visited"] = {(0, 0)}

        # child -> parent
        memory["parent"] = {}

        # Direction we are currently trying to enter.
        memory["target_direction"] = None

        # After turning, force a forward movement.
        memory["must_forward"] = False

    x = memory["x"]
    y = memory["y"]
    heading = memory["heading"]
    last_action = memory["last_action"]

    # =========================================================
    # 1. WORK OUT WHAT THE PREVIOUS ACTION DID
    # =========================================================

    if last_action == "turn_left":
        heading = (heading - 1) % 4

    elif last_action == "turn_right":
        heading = (heading + 1) % 4

    elif last_action == "forward":

        # Forward succeeds when both wheels are moving.
        moved = (
            sensors["rpm_left"] > 100
            and sensors["rpm_right"] > 100
        )

        # On the noisy maze, allow the ±5 encoder jitter.
        if moved:
            if heading == 0:
                y -= 1
            elif heading == 1:
                x += 1
            elif heading == 2:
                y += 1
            else:
                x -= 1

    memory["x"] = x
    memory["y"] = y
    memory["heading"] = heading

    current = (x, y)

    memory["visited"].add(current)

    # =========================================================
    # 2. IF WE JUST TURNED, MOVE FORWARD NOW
    # =========================================================

    if memory["must_forward"]:

        memory["must_forward"] = False
        memory["target_direction"] = None

        if sensors["dist_front"] > 0:
            memory["last_action"] = "forward"
            return "forward"

        # Something unexpected happened.
        # Fall through and re-evaluate.

    # =========================================================
    # 3. SENSOR READINGS
    # =========================================================

    front_open = sensors["dist_front"] > 0
    right_open = sensors["dist_right"] > 0
    left_open = sensors["dist_left"] > 0

    # =========================================================
    # 4. FIND NEIGHBOURING CELLS
    # =========================================================

    def next_cell(direction):
        if direction == 0:
            return (x, y - 1)
        elif direction == 1:
            return (x + 1, y)
        elif direction == 2:
            return (x, y + 1)
        else:
            return (x - 1, y)

    options = []

    # Right
    if right_open:
        direction = (heading + 1) % 4
        options.append(
            ("right", direction, next_cell(direction))
        )

    # Front
    if front_open:
        direction = heading
        options.append(
            ("front", direction, next_cell(direction))
        )

    # Left
    if left_open:
        direction = (heading - 1) % 4
        options.append(
            ("left", direction, next_cell(direction))
        )

    # =========================================================
    # 5. PREFER AN UNVISITED CELL
    # =========================================================

    for name, direction, cell in options:

        if cell not in memory["visited"]:

            # First time entering this cell.
            if cell not in memory["parent"]:
                memory["parent"][cell] = current

            # Already facing that direction.
            if direction == heading:
                memory["last_action"] = "forward"
                return "forward"

            # Need to turn right.
            if direction == (heading + 1) % 4:

                memory["must_forward"] = True
                memory["target_direction"] = direction
                memory["last_action"] = "turn_right"

                return "turn_right"

            # Need to turn left.
            if direction == (heading - 1) % 4:

                memory["must_forward"] = True
                memory["target_direction"] = direction
                memory["last_action"] = "turn_left"

                return "turn_left"

    # =========================================================
    # 6. NO UNVISITED CELL
    #
    #    Backtrack toward our parent.
    # =========================================================

    parent = memory["parent"].get(current)

    if parent is not None:

        px, py = parent

        dx = px - x
        dy = py - y

        if dx == 0 and dy == -1:
            target_direction = 0

        elif dx == 1 and dy == 0:
            target_direction = 1

        elif dx == 0 and dy == 1:
            target_direction = 2

        elif dx == -1 and dy == 0:
            target_direction = 3

        else:
            target_direction = heading

        # Already facing parent.
        if target_direction == heading:

            if front_open:
                memory["last_action"] = "forward"
                return "forward"

        # Parent is right.
        if target_direction == (heading + 1) % 4:

            memory["must_forward"] = True
            memory["target_direction"] = target_direction
            memory["last_action"] = "turn_right"

            return "turn_right"

        # Parent is left.
        if target_direction == (heading - 1) % 4:

            memory["must_forward"] = True
            memory["target_direction"] = target_direction
            memory["last_action"] = "turn_left"

            return "turn_left"

        # Parent is behind.
        #
        # Two right turns are needed.
        memory["must_forward"] = True
        memory["target_direction"] = target_direction
        memory["last_action"] = "turn_right"

        return "turn_right"

    # =========================================================
    # 7. SAFETY FALLBACK
    # =========================================================

    memory["last_action"] = "wait"
    return "wait"


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
