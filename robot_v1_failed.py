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
    V1:
    - Track position
    - Track heading
    - Remember visited cells
    - Remember parent cells
    - Explore unvisited cells
    - Backtrack when necessary
    """

    # ---------------------------------------------------------
    # INITIALIZE MEMORY
    # ---------------------------------------------------------

    if "x" not in memory:
        memory["x"] = 0
        memory["y"] = 0

        # 0 = North
        # 1 = East
        # 2 = South
        # 3 = West
        memory["heading"] = 0

        memory["last_action"] = None

        # Cells that we have already visited
        memory["visited"] = {(0, 0)}

        # Parent relationship:
        # child cell -> cell from which we reached it
        memory["parent"] = {}

    x = memory["x"]
    y = memory["y"]
    heading = memory["heading"]
    last_action = memory["last_action"]

    # ---------------------------------------------------------
    # 1. PROCESS THE PREVIOUS ACTION
    # ---------------------------------------------------------

    if last_action == "turn_left":
        heading = (heading - 1) % 4

    elif last_action == "turn_right":
        heading = (heading + 1) % 4

    elif last_action == "forward":

        # -2.0 means collision.
        collision = sensors["accel_fwd"] < -1.5

        if not collision:

            if heading == 0:
                y -= 1

            elif heading == 1:
                x += 1

            elif heading == 2:
                y += 1

            elif heading == 3:
                x -= 1

    # Save updated state
    memory["x"] = x
    memory["y"] = y
    memory["heading"] = heading

    current = (x, y)

    # Remember current cell
    memory["visited"].add(current)

    # ---------------------------------------------------------
    # 2. READ THE THREE DIRECTIONS
    # ---------------------------------------------------------

    front_open = sensors["dist_front"] > 0
    left_open = sensors["dist_left"] > 0
    right_open = sensors["dist_right"] > 0

    # ---------------------------------------------------------
    # 3. CALCULATE WHERE EACH OPENING LEADS
    # ---------------------------------------------------------

    # Direction numbers:
    #
    # 0 = North
    # 1 = East
    # 2 = South
    # 3 = West

    possible = []

    # Front
    if front_open:

        if heading == 0:
            next_cell = (x, y - 1)

        elif heading == 1:
            next_cell = (x + 1, y)

        elif heading == 2:
            next_cell = (x, y + 1)

        else:
            next_cell = (x - 1, y)

        possible.append(("front", heading, next_cell))

    # Right
    if right_open:

        direction = (heading + 1) % 4

        if direction == 0:
            next_cell = (x, y - 1)

        elif direction == 1:
            next_cell = (x + 1, y)

        elif direction == 2:
            next_cell = (x, y + 1)

        else:
            next_cell = (x - 1, y)

        possible.append(("right", direction, next_cell))

    # Left
    if left_open:

        direction = (heading - 1) % 4

        if direction == 0:
            next_cell = (x, y - 1)

        elif direction == 1:
            next_cell = (x + 1, y)

        elif direction == 2:
            next_cell = (x, y + 1)

        else:
            next_cell = (x - 1, y)

        possible.append(("left", direction, next_cell))

    # ---------------------------------------------------------
    # 4. FIRST PRIORITY:
    #    GO TO AN UNVISITED OPEN CELL
    #
    #    Preference:
    #    right -> front -> left
    # ---------------------------------------------------------

    for preferred in ("right", "front", "left"):

        for name, direction, next_cell in possible:

            if name == preferred and next_cell not in memory["visited"]:

                # Remember how we reached this new cell.
                if next_cell not in memory["parent"]:
                    memory["parent"][next_cell] = current

                if name == "front":
                    action = "forward"

                elif name == "right":
                    action = "turn_right"

                else:
                    action = "turn_left"

                memory["last_action"] = action
                return action

    # ---------------------------------------------------------
    # 5. NO UNVISITED NEIGHBOUR
    #
    #    We have probably reached a dead end or finished
    #    exploring this part of the maze.
    #
    #    Go back toward our parent.
    # ---------------------------------------------------------

    target = memory["parent"].get(current)

    if target is not None:

        target_x, target_y = target

        dx = target_x - x
        dy = target_y - y

        # Find direction toward parent
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

        # Parent is directly ahead
        if target_direction == heading:
            action = "forward"

        # Parent is on the right
        elif target_direction == (heading + 1) % 4:
            action = "turn_right"

        # Parent is on the left
        elif target_direction == (heading - 1) % 4:
            action = "turn_left"

        # Parent is behind us
        else:
            # A U-turn requires two turns.
            action = "turn_right"

        memory["last_action"] = action
        return action

    # ---------------------------------------------------------
    # 6. SAFETY FALLBACK
    # ---------------------------------------------------------

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
