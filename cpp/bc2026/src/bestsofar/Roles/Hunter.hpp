#pragma once
#include "api.hpp"
#include "Utils/Globals.hpp"

namespace Roles {

// Cat attacking micro
struct Hunter : Utils::Globals {
    static MapLocation cat;
    static Direction catDir;  // Java init: Direction.CENTER
    static int unknownRounds;

    static void run();
};

}  // namespace Roles
