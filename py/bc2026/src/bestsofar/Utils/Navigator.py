# Port of bestsofar/Utils/Navigator.java. See py/CONVENTIONS.md.
from api import *
from Utils.BellmanFordNavigator import BellmanFordNavigator
from Utils.BellmanFordNavigatorCat import BellmanFordNavigatorCat
from Utils.BugNavigator import BugNavigator
from Utils.Globals import Globals
# Java uses bestsofar.Utils.Vision fully-qualified without an import;
# Python still needs the name bound.
from Utils.Vision import Vision


class Navigator(Globals):
    currentTarget = None

    minDistanceToTarget = 0
    closestPositionToTarget = None
    roundsSinceMovingCloserToTarget = 0

    @staticmethod
    def moveTo(target, canTurn):
        myLocation = Globals.rc.getLocation()
        Globals.rc.setIndicatorLine(Globals.rc.getLocation(), target, 255, 0, 0)

        if myLocation == target:
            return

        if Navigator.currentTarget is None or Navigator.currentTarget.distanceSquaredTo(target) > 2:
            Navigator.reset()
            Navigator.closestPositionToTarget = Globals.rc.getLocation()
            Navigator.minDistanceToTarget = Globals.rc.getLocation().distanceSquaredTo(target)
        elif target != Navigator.currentTarget:
            curDist = Globals.rc.getLocation().distanceSquaredTo(target)
            closestDist = Navigator.closestPositionToTarget.distanceSquaredTo(target)
            if curDist < closestDist:
                Navigator.minDistanceToTarget = curDist
                Navigator.closestPositionToTarget = Globals.rc.getLocation()
                # roundsSinceMovingCloserToTarget = 0;
            else:
                Navigator.minDistanceToTarget = closestDist

        Navigator.currentTarget = target

        # /*
        # MapLocation nextLocation = myLocation.add(myLocation.directionTo(target));
        # if (rc.canSenseLocation(nextLocation) && rc.senseMapInfo(nextLocation).isDam()) {
        #     return;
        # }
        # */
        if not Globals.cantMove and Globals.rc.isActionReady():
            distanceToTarget = myLocation.distanceSquaredTo(target)
            if distanceToTarget < Navigator.minDistanceToTarget:
                Navigator.minDistanceToTarget = distanceToTarget
                Navigator.closestPositionToTarget = myLocation
                Navigator.roundsSinceMovingCloserToTarget = 0
            else:
                Navigator.roundsSinceMovingCloserToTarget += 1

        if Navigator.roundsSinceMovingCloserToTarget < 3 and len(Globals.enemyRobots) == 0 and Globals.closestEnemy is None and len(Globals.newestSqueaks) == 0 and Globals.rc.getCarrying() is None:
            if not Globals.rc.isMovementReady() or Globals.cantMove:
                return
            Globals.rc.setIndicatorString("bellman")
            # Java dead branch kept: closestEnemy is always null here.
            if Globals.closestEnemy is not None:
                Globals.rc.setIndicatorString(str(Globals.closestEnemy))
            bellmanFordDirection = BellmanFordNavigatorCat.getBestDirection(target) if Globals.catLoc is not None else BellmanFordNavigator.getBestDirection(target)
            if bellmanFordDirection is not None:
                bellmanFordLocation = Globals.rc.adjacentLocation(bellmanFordDirection)
                if Globals.rc.canRemoveDirt(bellmanFordLocation):
                    Globals.rc.removeDirt(bellmanFordLocation)
                    Vision.digDirt(bellmanFordLocation)
                if Globals.rc.canMove(bellmanFordDirection):
                    if canTurn and Globals.rc.canTurn():
                        Vision.turn(bellmanFordDirection)
                    if Globals.rc.canMove(bellmanFordDirection):
                        Globals.rc.move(bellmanFordDirection)

                # Logger.log("bf " + bellmanFordDirection);
                return
            else:
                # Logger.log("bf null");
                pass
        else:
            # Logger.log("bf n/a");
            pass

        BugNavigator.moveTo(target, canTurn)

    @staticmethod
    def reset():
        Navigator.currentTarget = None

        Navigator.roundsSinceMovingCloserToTarget = 0

        BugNavigator.reset()
