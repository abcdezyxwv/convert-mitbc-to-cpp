#pragma once
#include "../../api.hpp"

struct Pathfind {
    static int turnDir;  // lazily initialised from RobotPlayer::rng on first use
    static Direction exploreDirection;
    static const Direction directions[8];

    // bug-nav state
    static int bugState;
    static MapLocation closestObstacle;
    static int closestObstacleDist;
    static Direction pathDir;

    static MapLocation prevDest;
    static std::unordered_set<MapLocation> destLine;
    static int obstacleStartDist;

    static void resetVar();
    static std::unordered_set<MapLocation> createLine(MapLocation a, MapLocation b);
    static void moveTowardsV1(RobotController& rc, MapLocation loc);
    static void moveTowardsV2(RobotController& rc, MapLocation loc);
    static void moveTowards(RobotController& rc, MapLocation loc);
    static void explore(RobotController& rc);
};
