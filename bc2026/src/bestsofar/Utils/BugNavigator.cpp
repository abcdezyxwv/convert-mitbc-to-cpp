#include "Utils/BugNavigator.hpp"

#include <algorithm>
#include <cstdlib>

#include "Utils/FastSet.hpp"
#include "Utils/Globals.hpp"
#include "Utils/Vision.hpp"

namespace Utils {

MapLocation BugNavigator::currentTarget = MapLocation::NONE;
int BugNavigator::minDistanceToTarget = 0;
MapLocation BugNavigator::closestPositionToTarget = MapLocation::NONE;
bool BugNavigator::obstacleOnRight = false;
MapLocation BugNavigator::currentObstacle = MapLocation::NONE;
FastSet BugNavigator::visitedStates;

void BugNavigator::moveTo(MapLocation target, bool canTurn) {
    if (currentTarget.isNull() || currentTarget.distanceSquaredTo(target) > 2) {
        reset();
        closestPositionToTarget = rc.getLocation();
        minDistanceToTarget = rc.getLocation().distanceSquaredTo(target);
    } else if (!(target == currentTarget)) {
        int curDist = distance1d(rc.getLocation(), target);
        int closestDist = distance1d(closestPositionToTarget, target);
        if (curDist < closestDist) {
            minDistanceToTarget = curDist;
            closestPositionToTarget = rc.getLocation();
        } else
            minDistanceToTarget = closestDist;
    }

    if (!rc.isMovementReady()) return;

    bool hasOptions = false;
    for (int i = (int)adjacentDirections.size(); --i >= 0;) {
        if (canMoveWithDig(adjacentDirections[i])) {
            hasOptions = true;
            break;
        }
    }

    if (!hasOptions) {
        return;
    }

    MapLocation myLocation = rc.getLocation();

    int distanceToTarget = distance1d(myLocation, target);
    if (distanceToTarget < minDistanceToTarget) {
        rc.setIndicatorString("watesiggma");
        reset();
        minDistanceToTarget = distanceToTarget;
        closestPositionToTarget = rc.getLocation();
    }

    if (!currentObstacle.isNull() && Vision::hasSeenLocation(currentObstacle) &&
        Vision::sensePassability(currentObstacle)) {
        reset();
    }

    if (!visitedStates.add(getState(target))) {
        reset();
    }

    currentTarget = target;

    if (currentObstacle.isNull()) {
        Direction forward = myLocation.directionTo(target);
        if (canMoveWithDig(forward)) {
            moveWithDig(forward, canTurn);
            return;
        }

        setInitialDirection();
    }

    followWall(true, canTurn);
}

void BugNavigator::reset() {
    currentTarget = MapLocation::NONE;
    obstacleOnRight = true;
    currentObstacle = MapLocation::NONE;
    visitedStates = FastSet();
}

void BugNavigator::setInitialDirection() {
    MapLocation myLocation = rc.getLocation();
    Direction forward = myLocation.directionTo(currentTarget);

    Direction left = forward.rotateLeft();
    for (int i = 8; --i >= 0;) {
        MapLocation location = rc.adjacentLocation(left);
        if (Vision::hasSeenLocation(location) && Vision::sensePassability(location)) {
            break;
        }

        left = left.rotateLeft();
    }

    Direction right = forward.rotateRight();
    for (int i = 8; --i >= 0;) {
        MapLocation location = rc.adjacentLocation(right);
        if (Vision::hasSeenLocation(location) && Vision::sensePassability(location)) {
            break;
        }

        right = right.rotateRight();
    }

    MapLocation leftLocation = rc.adjacentLocation(left);
    MapLocation rightLocation = rc.adjacentLocation(right);

    int leftDistance = distance1d(leftLocation, currentTarget);
    int rightDistance = distance1d(rightLocation, currentTarget);

    if (leftDistance < rightDistance) {
        obstacleOnRight = true;
    } else if (rightDistance < leftDistance) {
        obstacleOnRight = false;
    } else {
        obstacleOnRight =
            myLocation.distanceSquaredTo(leftLocation) < myLocation.distanceSquaredTo(rightLocation);
    }

    if (obstacleOnRight) {
        currentObstacle = rc.adjacentLocation(left.rotateRight());
    } else {
        currentObstacle = rc.adjacentLocation(right.rotateLeft());
    }
}

void BugNavigator::followWall(bool canRotate, bool canTurn) {
    Direction direction = rc.getLocation().directionTo(currentObstacle);

    for (int i = 8; --i >= 0;) {
        direction = obstacleOnRight ? direction.rotateLeft() : direction.rotateRight();
        if (canMoveWithDig(direction)) {
            moveWithDig(direction, canTurn);
            return;
        }

        MapLocation location = rc.adjacentLocation(direction);
        if (canRotate && !rc.onTheMap(location)) {
            obstacleOnRight = !obstacleOnRight;
            followWall(false, canTurn);
            return;
        }

        if (Vision::hasSeenLocation(location) && !Vision::sensePassability(location)) {
            currentObstacle = location;
        }
    }
}

char16_t BugNavigator::getState(MapLocation target) {
    MapLocation myLocation = rc.getLocation();
    Direction direction = myLocation.directionTo(!currentObstacle.isNull() ? currentObstacle : target);
    int rotation = obstacleOnRight ? 1 : 0;

    return (char16_t)((((myLocation.x << 6) | myLocation.y) << 4) | (direction.ordinal() << 1) |
                      rotation);
}

int BugNavigator::distance1d(MapLocation a, MapLocation b) {
    return std::max(std::abs(a.x - b.x), std::abs(a.y - b.y));
}

bool BugNavigator::canMoveWithDig(Direction direction) {
    return (rc.canMove(direction) || rc.canRemoveDirt(rc.adjacentLocation(direction))) &&
           !Vision::isDangerous(rc.adjacentLocation(direction));
}

void BugNavigator::moveWithDig(Direction direction, bool canTurn) {
    MapLocation DigLocation = rc.adjacentLocation(direction);
    if (rc.canRemoveDirt(DigLocation)) {
        rc.removeDirt(DigLocation);
        Vision::digDirt(DigLocation);
    }

    if (rc.canMove(direction)) {
        if (canTurn && rc.canTurn()) {
            Vision::turn(direction);
        }
        rc.move(direction);
    }

    // Logger.log("bug " + direction);
}

}  // namespace Utils
