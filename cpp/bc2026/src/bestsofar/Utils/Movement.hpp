#pragma once
#include "api.hpp"
#include "Utils/Globals.hpp"

namespace Utils {

struct Movement : Globals {
    static MapLocation targetLoc;
    static MapLocation explorePoints[144];
    static int epSize;
    static int turnsStuck;
    static int bestDist;

    static void indicateAllExplorePoints();
    static void setNextExplorePoint();
    static void explore();
    static void init();
    static void exploreSafe();
    static void circle(MapLocation loc);
};

}  // namespace Utils
