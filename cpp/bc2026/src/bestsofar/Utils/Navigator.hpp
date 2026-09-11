#pragma once
#include "api.hpp"
#include "Utils/Globals.hpp"

namespace Utils {

struct Navigator : Globals {
private:
    static MapLocation currentTarget;
    static int minDistanceToTarget;
    static MapLocation closestPositionToTarget;
    static int roundsSinceMovingCloserToTarget;

public:
    static void moveTo(MapLocation target, bool canTurn);
    static void reset();
};

}  // namespace Utils
