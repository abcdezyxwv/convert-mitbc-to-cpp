#pragma once
#include "api.hpp"

namespace philip_06 {
namespace Helper {

struct Pathfind {
    static MapLocation dest;
    static Direction exploreDirection;

    static void setDest(RobotController rc, MapLocation loc);
    static void makeMove(RobotController rc);
    static void explore(RobotController rc);
};

}  // namespace Helper
}  // namespace philip_06
