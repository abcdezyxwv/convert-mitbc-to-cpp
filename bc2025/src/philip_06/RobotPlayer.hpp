#pragma once
#include "api.hpp"

namespace philip_06 {

struct RobotPlayer {
    static Random rng;  // java.util.Random -> api.hpp ::Random (Java: = null)
    static bool rush;
    static bool fill;
    static bool retreat;
    static bool build;
    static bool built;
    static int aliveTurns;
    static int lastSeenEnemy;
    static MapLocation lastEnemyTower;

    static void run(RobotController rc);
};

}  // namespace philip_06
