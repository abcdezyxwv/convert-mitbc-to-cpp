#pragma once
#include "api.hpp"
#include "Utils/Globals.hpp"

struct King : Utils::Globals {
    static int lastCatTrap;  // Java init: -5
    static int lastRatTrap;  // Java init: -5

    // SPAWNING ------------------------------------------------------------ //

    static void spawn();
    static int spawnAmountThreshold();
    static int insaneSpawnAmountThreshold();
    static void spawnIf();

    // SURVIVAL ------------------------------------------------------------ //

    static Direction lastDir;  // Java null -> lastDir + lastDirNull pair
    static bool lastDirNull;   // true == Java `lastDir == null`
    static MapLocation unsafe[20];
    static int unsafeTime[20];

    static void moveSafety();

    static int catID[15];
    static int catRound[15];
    static int pointer;

    static void defendCats();
    static void tryAttack();
    static void defendRats();
    static void tryDigDirt();

    static MapLocation newKingPos;
    static int lastSeenEnemy;

    static void needNewKing();
    static void spawnNewKing();
    static void run();
};
