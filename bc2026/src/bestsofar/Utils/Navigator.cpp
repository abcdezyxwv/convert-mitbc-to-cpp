#include "Utils/Navigator.hpp"

#include "Utils/BellmanFordNavigator.hpp"
#include "Utils/BellmanFordNavigatorCat.hpp"
#include "Utils/BugNavigator.hpp"
#include "Utils/Globals.hpp"
#include "Utils/Vision.hpp"

namespace Utils {

MapLocation Navigator::currentTarget = MapLocation::NONE;
int Navigator::minDistanceToTarget = 0;
MapLocation Navigator::closestPositionToTarget = MapLocation::NONE;
int Navigator::roundsSinceMovingCloserToTarget = 0;

void Navigator::moveTo(MapLocation target, bool canTurn) {
    MapLocation myLocation = rc.getLocation();
    rc.setIndicatorLine(rc.getLocation(), target, 255, 0, 0);

    if (myLocation == target) {
        return;
    }

    if (currentTarget.isNull() || currentTarget.distanceSquaredTo(target) > 2) {
        reset();
        closestPositionToTarget = rc.getLocation();
        minDistanceToTarget = rc.getLocation().distanceSquaredTo(target);
    } else if (!(target == currentTarget)) {
        int curDist = rc.getLocation().distanceSquaredTo(target);
        int closestDist = closestPositionToTarget.distanceSquaredTo(target);
        if (curDist < closestDist) {
            minDistanceToTarget = curDist;
            closestPositionToTarget = rc.getLocation();
            // roundsSinceMovingCloserToTarget = 0;
        } else
            minDistanceToTarget = closestDist;
    }

    currentTarget = target;

    /*
    MapLocation nextLocation = myLocation.add(myLocation.directionTo(target));
    if (rc.canSenseLocation(nextLocation) && rc.senseMapInfo(nextLocation).isDam()) {
        return;
    }
    */
    if (!cantMove && rc.isActionReady()) {
        int distanceToTarget = myLocation.distanceSquaredTo(target);
        if (distanceToTarget < minDistanceToTarget) {
            minDistanceToTarget = distanceToTarget;
            closestPositionToTarget = myLocation;
            roundsSinceMovingCloserToTarget = 0;
        } else {
            roundsSinceMovingCloserToTarget++;
        }
    }

    if (roundsSinceMovingCloserToTarget < 3 && enemyRobots.size() == 0 &&
        closestEnemy.location.isNull() && newestSqueaks.size() == 0 &&
        rc.getCarrying().location.isNull()) {
        if (!rc.isMovementReady() || cantMove) return;
        rc.setIndicatorString("bellman");
        // dead branch in the Java too (closestEnemy is null here); api.hpp's
        // RobotInfo has no toString(), so its location's is used.
        if (!closestEnemy.location.isNull()) rc.setIndicatorString(closestEnemy.location.toString());
        Direction bellmanFordDirection = !catLoc.isNull()
                                             ? BellmanFordNavigatorCat::getBestDirection(target)
                                             : BellmanFordNavigator::getBestDirection(target);
        if (bellmanFordDirection != Direction::all[Direction::CENTER]) {
            MapLocation bellmanFordLocation = rc.adjacentLocation(bellmanFordDirection);
            if (rc.canRemoveDirt(bellmanFordLocation)) {
                rc.removeDirt(bellmanFordLocation);
                Vision::digDirt(bellmanFordLocation);
            }
            if (rc.canMove(bellmanFordDirection)) {
                if (canTurn && rc.canTurn()) {
                    Vision::turn(bellmanFordDirection);
                }
                if (rc.canMove(bellmanFordDirection)) {
                    rc.move(bellmanFordDirection);
                }
            }

            // Logger.log("bf " + bellmanFordDirection);
            return;
        } else {
            // Logger.log("bf null");
        }
    } else {
        // Logger.log("bf n/a");
    }

    BugNavigator::moveTo(target, canTurn);
}

void Navigator::reset() {
    currentTarget = MapLocation::NONE;

    roundsSinceMovingCloserToTarget = 0;

    BugNavigator::reset();
}

}  // namespace Utils
