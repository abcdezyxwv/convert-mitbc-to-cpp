#pragma once
#include "api.hpp"
#include "Utils/Globals.hpp"

namespace Roles {

struct Multiking : Utils::Globals {
    static MapLocation newKingPos;
    static int roundsCircled;

    static bool isMultiking();

    static MapLocation targetPos;

    static void moveTo();
    static void run();
};

}  // namespace Roles
