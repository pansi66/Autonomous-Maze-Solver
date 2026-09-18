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
    V1.2
    Position + heading + visited cells + parent tracking.
    Correctly handles 90-degree and 180-degree turns.
    """

    # =========================================================
    # INITIALIZE MEMORY
    # =========================================================

    if "x" not in memory:
        memory["x"] = 0
        memory["y"] = 0
        memory["heading"] = 0       # 0=N, 1=E, 2=S, 3=W

        memory["last_action"] = None

        memory["visited"] = {(0, 0)}
        memory["parent"] = {}

        # Actions that must happen before making a new decision.
        memory["pending"] = []

    x = memory["x"]
    y = memory["y"]
    heading = memory["heading"]

    last_action = memory["last_action"]

    # =========================================================
    # 1. UPDATE OUR BELIEVED POSITION / HEADING
    #    USING THE RESULT OF THE PREVIOUS ACTION
    # =========================================================

    if last_action == "turn_right":

        # The simulator reports +1.0 for right turns.
        if sensors["accel_lat"] > 0:
            heading = (heading + 1) % 4

    elif last_action == "turn_left":

        if sensors["accel_lat"] < 0:
            heading = (heading - 1) % 4

    elif last_action == "forward":

        # Wheels around +120 mean successful movement.
        # Allow encoder jitter of about +/-5.
        moved = (
            sensors["rpm_left"] > 100
            and sensors["rpm_right"] > 100
            and sensors["accel_fwd"] > -1.5
        )

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
    # 2. FINISH ANY PREVIOUS TURN SEQUENCE
    # =========================================================

    if memory["pending"]:

        action = memory["pending"].pop(0)

        memory["last_action"] = action

        return action

    # =========================================================
    # 3. SENSOR READINGS
    # =========================================================

    front_open = sensors["dist_front"] > 0
    right_open = sensors["dist_right"] > 0
    left_open = sensors["dist_left"] > 0

    # =========================================================
    # 4. HELPER: GET CELL IN A DIRECTION
    # =========================================================

    def cell_in_direction(direction):

        if direction == 0:
            return (x, y - 1)

        if direction == 1:
            return (x + 1, y)

        if direction == 2:
            return (x, y + 1)

        return (x - 1, y)

    # =========================================================
    # 5. BUILD AVAILABLE DIRECTIONS
    # =========================================================

    options = []

    # Right
    if right_open:
        direction = (heading + 1) % 4
        options.append(
            ("right", direction, cell_in_direction(direction))
        )

    # Front
    if front_open:
        direction = heading
        options.append(
            ("front", direction, cell_in_direction(direction))
        )

    # Left
    if left_open:
        direction = (heading - 1) % 4
        options.append(
            ("left", direction, cell_in_direction(direction))
        )

    # =========================================================
    # 6. PREFER UNVISITED CELLS
    #
    #    Right -> Front -> Left
    # =========================================================

    for name, direction, next_cell in options:

        if next_cell not in memory["visited"]:

            # Remember how we reached the new cell.
            if next_cell not in memory["parent"]:
                memory["parent"][next_cell] = current

            # -------------------------------------------------
            # Already facing the desired direction
            # -------------------------------------------------

            if direction == heading:

                memory["last_action"] = "forward"

                return "forward"

            # -------------------------------------------------
            # Turn right
            # -------------------------------------------------

            elif direction == (heading + 1) % 4:

                # Turn, then force forward.
                memory["pending"] = ["forward"]

                memory["last_action"] = "turn_right"

                return "turn_right"

            # -------------------------------------------------
            # Turn left
            # -------------------------------------------------

            elif direction == (heading - 1) % 4:

                memory["pending"] = ["forward"]

                memory["last_action"] = "turn_left"

                return "turn_left"

            # -------------------------------------------------
            # U-turn
            # -------------------------------------------------

            else:

                # Two 90-degree right turns.
                memory["pending"] = [
                    "turn_right",
                    "forward"
                ]

                memory["last_action"] = "turn_right"

                return "turn_right"

    # =========================================================
    # 7. NOTHING NEW NEARBY
    #
    #    BACKTRACK TO PARENT
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

        # -----------------------------------------------------
        # Parent is straight ahead
        # -----------------------------------------------------

        if target_direction == heading:

            if front_open:

                memory["last_action"] = "forward"

                return "forward"

        # -----------------------------------------------------
        # Parent is right
        # -----------------------------------------------------

        elif target_direction == (heading + 1) % 4:

            memory["pending"] = ["forward"]

            memory["last_action"] = "turn_right"

            return "turn_right"

        # -----------------------------------------------------
        # Parent is left
        # -----------------------------------------------------

        elif target_direction == (heading - 1) % 4:

            memory["pending"] = ["forward"]

            memory["last_action"] = "turn_left"

            return "turn_left"

        # -----------------------------------------------------
        # Parent is behind
        # -----------------------------------------------------

        else:

            memory["pending"] = [
                "turn_right",
                "forward"
            ]

            memory["last_action"] = "turn_right"

            return "turn_right"

    # =========================================================
    # 8. SAFETY FALLBACK
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
