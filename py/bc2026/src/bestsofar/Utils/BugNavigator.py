# Port of bestsofar/Utils/BugNavigator.java. See py/CONVENTIONS.md.
from api import *
from Utils.FastSet import FastSet
from Utils.Globals import Globals
from Utils.Vision import Vision


class BugNavigator(Globals):
    currentTarget = None

    minDistanceToTarget = 0
    closestPositionToTarget = None

    obstacleOnRight = False
    currentObstacle = None
    visitedStates = None  # Java: private static FastSet

    @staticmethod
    def moveTo(target, canTurn):
        if BugNavigator.currentTarget is None or BugNavigator.currentTarget.distanceSquaredTo(target) > 2:
            BugNavigator.reset()
            BugNavigator.closestPositionToTarget = Globals.rc.getLocation()
            BugNavigator.minDistanceToTarget = Globals.rc.getLocation().distanceSquaredTo(target)
        elif target != BugNavigator.currentTarget:
            curDist = BugNavigator.distance1d(Globals.rc.getLocation(), target)
            closestDist = BugNavigator.distance1d(BugNavigator.closestPositionToTarget, target)
            if curDist < closestDist:
                BugNavigator.minDistanceToTarget = curDist
                BugNavigator.closestPositionToTarget = Globals.rc.getLocation()
            else:
                BugNavigator.minDistanceToTarget = closestDist

        if not Globals.rc.isMovementReady():
            return

        hasOptions = False
        # Java: for (int i = adjacentDirections.length; --i >= 0; )
        for i in range(len(Globals.adjacentDirections) - 1, -1, -1):
            if BugNavigator.canMoveWithDig(Globals.adjacentDirections[i]):
                hasOptions = True
                break

        if not hasOptions:
            return

        myLocation = Globals.rc.getLocation()

        distanceToTarget = BugNavigator.distance1d(myLocation, target)
        if distanceToTarget < BugNavigator.minDistanceToTarget:
            Globals.rc.setIndicatorString("watesiggma")
            BugNavigator.reset()
            BugNavigator.minDistanceToTarget = distanceToTarget
            BugNavigator.closestPositionToTarget = Globals.rc.getLocation()

        if BugNavigator.currentObstacle is not None and Vision.hasSeenLocation(BugNavigator.currentObstacle) and Vision.sensePassability(BugNavigator.currentObstacle):
            BugNavigator.reset()

        if not BugNavigator.visitedStates.add(BugNavigator.getState(target)):
            BugNavigator.reset()

        BugNavigator.currentTarget = target

        if BugNavigator.currentObstacle is None:
            forward = myLocation.directionTo(target)
            if BugNavigator.canMoveWithDig(forward):
                BugNavigator.moveWithDig(forward, canTurn)
                return

            BugNavigator.setInitialDirection()

        BugNavigator.followWall(True, canTurn)

    @staticmethod
    def reset():
        BugNavigator.currentTarget = None
        BugNavigator.obstacleOnRight = True
        BugNavigator.currentObstacle = None
        BugNavigator.visitedStates = FastSet()

    @staticmethod
    def setInitialDirection():
        myLocation = Globals.rc.getLocation()
        forward = myLocation.directionTo(BugNavigator.currentTarget)

        left = forward.rotateLeft()
        for i in range(7, -1, -1):  # Java: for (int i = 8; --i >= 0; )
            location = Globals.rc.adjacentLocation(left)
            if Vision.hasSeenLocation(location) and Vision.sensePassability(location):
                break

            left = left.rotateLeft()

        right = forward.rotateRight()
        for i in range(7, -1, -1):  # Java: for (int i = 8; --i >= 0; )
            location = Globals.rc.adjacentLocation(right)
            if Vision.hasSeenLocation(location) and Vision.sensePassability(location):
                break

            right = right.rotateRight()

        leftLocation = Globals.rc.adjacentLocation(left)
        rightLocation = Globals.rc.adjacentLocation(right)

        leftDistance = BugNavigator.distance1d(leftLocation, BugNavigator.currentTarget)
        rightDistance = BugNavigator.distance1d(rightLocation, BugNavigator.currentTarget)

        if leftDistance < rightDistance:
            BugNavigator.obstacleOnRight = True
        elif rightDistance < leftDistance:
            BugNavigator.obstacleOnRight = False
        else:
            BugNavigator.obstacleOnRight = myLocation.distanceSquaredTo(leftLocation) < myLocation.distanceSquaredTo(rightLocation)

        if BugNavigator.obstacleOnRight:
            BugNavigator.currentObstacle = Globals.rc.adjacentLocation(left.rotateRight())
        else:
            BugNavigator.currentObstacle = Globals.rc.adjacentLocation(right.rotateLeft())

    @staticmethod
    def followWall(canRotate, canTurn):
        direction = Globals.rc.getLocation().directionTo(BugNavigator.currentObstacle)

        for i in range(7, -1, -1):  # Java: for (int i = 8; --i >= 0; )
            direction = direction.rotateLeft() if BugNavigator.obstacleOnRight else direction.rotateRight()
            if BugNavigator.canMoveWithDig(direction):
                BugNavigator.moveWithDig(direction, canTurn)
                return

            location = Globals.rc.adjacentLocation(direction)
            if canRotate and not Globals.rc.onTheMap(location):
                BugNavigator.obstacleOnRight = not BugNavigator.obstacleOnRight
                BugNavigator.followWall(False, canTurn)
                return

            if Vision.hasSeenLocation(location) and not Vision.sensePassability(location):
                BugNavigator.currentObstacle = location

    @staticmethod
    def getState(target):
        myLocation = Globals.rc.getLocation()
        # Java: currentObstacle != null ? currentObstacle : target
        direction = myLocation.directionTo(BugNavigator.currentObstacle if BugNavigator.currentObstacle is not None else target)
        rotation = 1 if BugNavigator.obstacleOnRight else 0

        # Java: (char) cast truncates to 16 bits
        return ((((myLocation.x << 6) | myLocation.y) << 4) | (direction.ordinal() << 1) | rotation) & 0xFFFF

    @staticmethod
    def distance1d(a, b):
        return max(abs(a.x - b.x), abs(a.y - b.y))

    @staticmethod
    def canMoveWithDig(direction):
        return (Globals.rc.canMove(direction) or Globals.rc.canRemoveDirt(Globals.rc.adjacentLocation(direction))) and not Vision.isDangerous(Globals.rc.adjacentLocation(direction))

    @staticmethod
    def moveWithDig(direction, canTurn):
        DigLocation = Globals.rc.adjacentLocation(direction)
        if Globals.rc.canRemoveDirt(DigLocation):
            Globals.rc.removeDirt(DigLocation)
            Vision.digDirt(DigLocation)

        if Globals.rc.canMove(direction):
            if canTurn and Globals.rc.canTurn():
                Vision.turn(direction)
            Globals.rc.move(direction)

        # Logger.log("bug " + direction);
