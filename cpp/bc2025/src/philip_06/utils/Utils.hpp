#pragma once
#include "api.hpp"

namespace philip_06 {
namespace utils {

struct Utils {
    static int distance(MapLocation a, MapLocation b) {
        return std::max(std::abs(a.x - b.x), std::abs(a.y - b.y));
    }
    static MapLocation closest(MapLocation loc, const vector<MapLocation>& locs);
    static MapInfo closestInfo(MapLocation loc, const vector<MapInfo>& locs);
    static double threatLevel(MapLocation loc, RobotController rc);
    static bool spawn(RobotController rc, UnitType type);
    static bool getColour(MapLocation loc) {
        if (loc.y % 3 != 2)
            return (loc.x + loc.y) % 2 == 0;
        if (std::abs(loc.x - loc.y) % 4 == 0)
            return false;
        return (loc.x + loc.y) % 2 == 0;
        // center is loc.y%3==2 && abs(loc.x-loc.y)%4==0
    }
    static PaintType getPaint(MapLocation loc) {
        if (getColour(loc))
            return PaintType::ALLY_SECONDARY;
        return PaintType::ALLY_PRIMARY;
    }
    static void checkResources(RobotController rc);
    static void attackTowers(RobotController rc);
    static RobotInfo closestEnemyTower(RobotController rc);
    static void shuffleArray(vector<int>& array);
    static MapLocation closestRuin(RobotController rc);
};

}  // namespace utils
}  // namespace philip_06
