#pragma once
#include "api.hpp"
#include <deque>
#include <utility>

// --- MISSING FROM api.hpp (declarations only; see notes) -------------------
// battlecode.common.UnitType carries stat fields that the C++ shim's
// `enum class UnitType` cannot hold, so `rc.getType().attackStrength` etc.
// become free lookup functions over UnitType.
int attackStrength(UnitType t);
int aoeAttackStrength(UnitType t);
// --------------------------------------------------------------------------

namespace philip_06 {
namespace roles {

struct Tower {
    // Java: static class SpawnRateChange
    struct SpawnRateChange {
        int soldierPrty, splasherPrty, mopperPrty;
        // Java declares `SpawnRateChange s;` and assigns it in every branch;
        // C++ needs a default ctor for that to compile.
        SpawnRateChange() : soldierPrty(0), splasherPrty(0), mopperPrty(0) {}
        SpawnRateChange(int sol, int spl, int mop)
            : soldierPrty(sol), splasherPrty(spl), mopperPrty(mop) {}
    };

    // Queue<Map.Entry<UnitType, MapLocation>> -> deque<pair<...>>
    // peek()->front(), remove()->pop_front(), add()->push_back(), isEmpty()->empty()
    static std::deque<std::pair<UnitType, MapLocation>> toSpawn;
    static MapLocation target;
    static int targetRound;

    static void run(RobotController rc);
};

}  // namespace roles
}  // namespace philip_06
