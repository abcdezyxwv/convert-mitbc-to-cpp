#pragma once
#include "api.hpp"

namespace philip_06 {
namespace SoldierState {

struct Attack {
    static const Direction directions[8];

    static MapLocation target;
    static MapLocation next;
    static bool found;

    static MapLocation rotational(RobotController rc, MapLocation curr) {
        return MapLocation(rc.getMapWidth() - curr.x - 1, rc.getMapHeight() - curr.y - 1);
    }
    static MapLocation vertical(RobotController rc, MapLocation curr) {
        return MapLocation(rc.getMapWidth() - curr.x - 1, curr.y);
    }
    static MapLocation horizontal(RobotController rc, MapLocation curr) {
        return MapLocation(curr.x, rc.getMapHeight() - curr.y - 1);
    }
    static bool onMap(RobotController rc, MapLocation curr) {
        return curr.x >= 0 && curr.x < rc.getMapWidth() && curr.y >= 0 && curr.y < rc.getMapHeight();
    }

    static void run(RobotController rc);
};

}  // namespace SoldierState
}  // namespace philip_06
