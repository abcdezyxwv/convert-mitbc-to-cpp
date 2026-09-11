#pragma once
#include "api.hpp"
#include "Utils/Globals.hpp"

struct Baby : Utils::Globals {
    static MapLocation spawn;

    static bool isNewKing;
    static bool explorer;

    static int roundsBeingHeld;

    static void evadeCats();
    static void unevadeCats();
    static void burnCooldown();
    static void run();
};
