#pragma once
#include "api.hpp"
#include "Utils/FastSet.hpp"
#include "Utils/Globals.hpp"

namespace Roles {

struct Miner : Utils::Globals {
    static const Direction mineDirections[9];  // CENTER, NORTH..NORTHWEST

    static Utils::FastSet mineBlacklist;

    static MapLocation mine;
    static MapLocation cheese;
    static bool returningToKing;
    static MapLocation newKing;

    static MapLocation needNewKing();
    static bool amOccupyingMine(MapLocation loc);
    static bool mineIsOccupied(MapLocation loc);
    static bool findMine();
    static bool findCheese();
    static bool checkMineVacancy();
    static void returnToKing(bool urgent);
    static bool shouldBeMiner();

    static int knownSym;

    static void run();
};

}  // namespace Roles
