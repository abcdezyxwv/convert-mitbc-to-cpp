#pragma once
#include "api.hpp"
#include "Utils/Globals.hpp"

namespace Roles {

struct AntiCat : Utils::Globals {
    static int lastTime;
    static int inARow;

    static void suicide();
    static bool run(MapLocation catLoc);
};

}  // namespace Roles
