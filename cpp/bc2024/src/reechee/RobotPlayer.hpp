#pragma once
#include "../../api.hpp"

struct RobotPlayer {
    // SHARED ARRAY INFO
    // 0 - 2: Information about team flags - contains x, y, number of booms placed

    // Settings
    static int numDefence;
    static int flagMove1;
    static int flagMove2;
    static TrapType defensiveTrapType;

    // Game variables
    static int roundNum;
    static int id;

    // Code variables
    static Random rng;
    static int teamFlagInfo;
    static MapLocation teamFlagLocation;
    static int role;  // 0: Defender, 1: Attacker
    static MapLocation flagTargetLocation;
    static Direction oscillationDirections[8];
    static int currentOscillationDirection;

    static void run(RobotController rc);
    static void getGlobalUpgrades(RobotController& rc);
    static void spawnBot(RobotController& rc);
    static void xDefense(RobotController& rc);
    static void placeTrapsNearFlag(RobotController& rc);
    static void healNearby(RobotController& rc);
    static void attackNearby(RobotController& rc);
};
