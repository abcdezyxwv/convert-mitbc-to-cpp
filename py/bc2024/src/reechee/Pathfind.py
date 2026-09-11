# Port of reechee/Pathfind.java. See py/CONVENTIONS.md.
from api import *
import RobotPlayer


class Pathfind:
    # Lazily initialised from RobotPlayer.rng on first use (Java field
    # initializer runs at class load, after RobotPlayer.run has set rng).
    turnDir = -1

    exploreDirection = Direction.NORTH

    directions = [
        Direction.NORTH,
        Direction.NORTHEAST,
        Direction.EAST,
        Direction.SOUTHEAST,
        Direction.SOUTH,
        Direction.SOUTHWEST,
        Direction.WEST,
        Direction.NORTHWEST,
    ]

    # Variables for path find v2
    bugState = 0
    closestObstacle = None
    closestObstacleDist = 99999
    pathDir = None

    # Variables for path find v3
    prevDest = None
    destLine = None
    obstacleStartDist = 0

    @staticmethod
    def resetVar():
        Pathfind.bugState = 0
        Pathfind.closestObstacle = None
        Pathfind.closestObstacleDist = 99999
        Pathfind.pathDir = None

    @staticmethod
    def _createLine(a, b):
        locs = set()
        x = a.x
        y = a.y
        dx = b.x - a.x
        dy = b.y - a.y
        sx = signum(dx)
        sy = signum(dy)
        dx = abs(dx)
        dy = abs(dy)
        d = max(dx, dy)
        r = d // 2  # d >= 0: Java int division
        if dx > dy:
            for i in range(d):
                locs.add(MapLocation(x, y))
                x += sx
                r += dy
                if r >= dx:
                    locs.add(MapLocation(x, y))
                    y += sy
                    r -= dx
        else:
            for i in range(d):
                locs.add(MapLocation(x, y))
                y += sy
                r += dx
                if r >= dy:
                    locs.add(MapLocation(x, y))
                    x += sx
                    r -= dy
        locs.add(MapLocation(x, y))
        return locs

    @staticmethod
    def moveTowardsV1(rc, loc):
        if Pathfind.turnDir < 0:
            Pathfind.turnDir = RobotPlayer.RobotPlayer.rng.nextInt(2)

        # Find the best direction to go to target
        dir = rc.getLocation().directionTo(loc)

        # Keep trying to move towards the target unless not possible
        # In that case turn 45 degrees in a random direction
        # To avoid left -> right -> left etc cycles, make it turn 1 direction the entire time
        if Pathfind.turnDir == 1:
            # Turn Left
            attempts = 0
            while attempts < 8:
                attempts += 1
                # If there is water in the way, fill it
                ahead = rc.getLocation().add(dir)
                if rc.canFill(ahead):
                    rc.fill(ahead)

                # Try move in that direction
                if rc.canMove(dir):
                    rc.move(dir)
                    break

                # Rotate 45 degrees left and try again
                dir = dir.rotateLeft()
        else:
            # Turn Right
            attempts = 0
            while attempts < 8:
                attempts += 1
                # If there is water in the way, fill it
                ahead = rc.getLocation().add(dir)
                if rc.canFill(ahead):
                    rc.fill(ahead)

                # Try move in that direction
                if rc.canMove(dir):
                    rc.move(dir)
                    break

                # Rotate 45 degrees right and try again
                dir = dir.rotateRight()

    @staticmethod
    def moveTowardsV2(rc, loc):
        # bugState: 0 for head towards obstacle, 1 for circle obstacle
        if Pathfind.bugState == 0:
            # If you can move, move. Otherwise, entire obstacle circle mode
            Pathfind.pathDir = rc.getLocation().directionTo(loc)
            ahead = rc.getLocation().add(Pathfind.pathDir)
            if rc.canFill(ahead):
                rc.fill(ahead)
            if rc.canMove(Pathfind.pathDir):
                rc.move(Pathfind.pathDir)
            else:
                Pathfind.bugState = 1
                Pathfind.closestObstacle = None
                Pathfind.closestObstacleDist = 99999
        else:
            if rc.getLocation() == Pathfind.closestObstacle:
                Pathfind.bugState = 0
            if rc.getLocation().distanceSquaredTo(loc) < Pathfind.closestObstacleDist:
                Pathfind.closestObstacleDist = rc.getLocation().distanceSquaredTo(loc)
                Pathfind.closestObstacle = rc.getLocation()
            for i in range(8):
                ahead = rc.getLocation().add(Pathfind.pathDir)
                if rc.canFill(ahead):
                    rc.fill(ahead)
                if rc.canMove(Pathfind.pathDir):
                    rc.move(Pathfind.pathDir)
                    Pathfind.pathDir = Pathfind.pathDir.rotateLeft()
                    Pathfind.pathDir = Pathfind.pathDir.rotateLeft()
                    break
                else:
                    Pathfind.pathDir = Pathfind.pathDir.rotateRight()

    @staticmethod
    def moveTowards(rc, loc):
        # If needs a new destination
        if loc != Pathfind.prevDest:
            Pathfind.prevDest = loc
            Pathfind.destLine = Pathfind._createLine(rc.getLocation(), loc)

        for point in Pathfind.destLine:
            rc.setIndicatorDot(point, 255, 0, 0)

        # bugState: 0 for head towards obstacle, 1 for circle obstacle
        if Pathfind.bugState == 0:
            # If you can move, move. Otherwise, entire obstacle circle mode
            Pathfind.pathDir = rc.getLocation().directionTo(loc)
            ahead = rc.getLocation().add(Pathfind.pathDir)
            toMove = rc.senseMapInfo(ahead)
            if rc.canFill(ahead):
                rc.fill(ahead)
            if rc.canMove(Pathfind.pathDir):
                rc.move(Pathfind.pathDir)
            elif not toMove.isWater():
                Pathfind.bugState = 1
                Pathfind.obstacleStartDist = rc.getLocation().distanceSquaredTo(loc)
        else:
            # Checks if it sees the line again
            if rc.getLocation() in Pathfind.destLine and \
                    rc.getLocation().distanceSquaredTo(loc) < Pathfind.obstacleStartDist:
                Pathfind.bugState = 0
                return

            # Follows around the obstacle
            for i in range(8):
                ahead = rc.getLocation().add(Pathfind.pathDir)
                if rc.canFill(ahead):
                    rc.fill(ahead)
                if rc.canMove(Pathfind.pathDir):
                    rc.move(Pathfind.pathDir)
                    Pathfind.pathDir = Pathfind.pathDir.rotateLeft()
                    break
                else:
                    Pathfind.pathDir = Pathfind.pathDir.rotateRight()

    @staticmethod
    def explore(rc):
        # (commented-out water-fill block removed in the Java too)
        crumbs = rc.senseNearbyCrumbs(-1)
        target = None
        bestDist = 99999

        # Iterate through the crumbs and choose the first one to get
        for crumb in crumbs:
            if rc.getLocation().distanceSquaredTo(crumb) < bestDist:
                target = crumb
                bestDist = rc.getLocation().distanceSquaredTo(crumb)

        if target is not None:
            # If there are crumbs to get, get them
            Pathfind.moveTowards(rc, target)
        else:
            # Do the normal exploration
            if rc.isMovementReady():
                # If you can keep moving in that direction, do it unless there is
                # a random change of direction
                ahead = rc.getLocation().add(Pathfind.exploreDirection)
                if rc.canFill(ahead):
                    rc.fill(ahead)
                if rc.canMove(Pathfind.exploreDirection) and \
                        RobotPlayer.RobotPlayer.rng.nextInt(50) != 0:
                    rc.move(Pathfind.exploreDirection)
                # If it has reached the end, pick a random number of turns in a random direction
                else:
                    # Random number of turns that are needed to do
                    # Guarantees that it doesn't to an 180 degree turn
                    Pathfind.exploreDirection = Direction.allDirections()[
                        RobotPlayer.RobotPlayer.rng.nextInt(8)]
