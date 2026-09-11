#pragma once
#include "api.hpp"
#include "Utils/Globals.hpp"

namespace Utils {

struct CatsAreWalls : Globals {
    static void pretend(MapLocation loc, Direction dir);
    static void unpretend(MapLocation loc, Direction dir);
};

}  // namespace Utils
