#pragma once
#include "api.hpp"
#include "Utils/FastSet.hpp"
#include "Utils/Globals.hpp"

namespace Utils {

struct BugNavigator : Globals {
private:
    static MapLocation currentTarget;
    static int minDistanceToTarget;
    static MapLocation closestPositionToTarget;
    static bool obstacleOnRight;
    static MapLocation currentObstacle;
    static FastSet visitedStates;

    static void setInitialDirection();
    static void followWall(bool canRotate, bool canTurn);
    static char16_t getState(MapLocation target);  // Java: private static char
    static bool canMoveWithDig(Direction direction);
    static void moveWithDig(Direction direction, bool canTurn);

public:
    static void moveTo(MapLocation target, bool canTurn);
    static void reset();
    static int distance1d(MapLocation a, MapLocation b);
};

}  // namespace Utils
