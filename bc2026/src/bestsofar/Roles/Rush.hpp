#pragma once
#include "api.hpp"
#include "Utils/Globals.hpp"

namespace Roles {

struct Rush : Utils::Globals {
    static MapLocation spawnLoc;
    static MapLocation rush;
    static MapLocation approx;
    static int remainingSym;
    static int guessedSym;
    static int susFactor[5];
    static int turnsStuck;
    static int bestDist;
    static int approxRound;
    static bool kingFound;

    static MapLocation getNewRushLocation();
    static void run(MapLocation spawn);
};

}  // namespace Roles
