#pragma once
#include "api.hpp"
#include <unordered_set>

namespace philip_06 {

struct Soldier {
    static bool builder;
    static int turnsAlive;
    static MapLocation spawn;
    static std::unordered_set<MapLocation> paintTowers;
    static vector<MapLocation> ruins;
    static bool messenger;
    static MapLocation messageLoc;
    static int priority, roundNum;
    static int message;
    static int moneyLastTurn;
    static bool defaultFill;
    static MapLocation attack;

    static bool onMap(RobotController rc, MapLocation curr) {
        return curr.x >= 0 && curr.x < rc.getMapWidth() && curr.y >= 0 &&
               curr.y < rc.getMapHeight();
    }
    static int scale(int value, int originalMin, int originalMax, int targetMin,
                     int targetMax) {
        return (int)std::lround(targetMin + (double)(value - originalMin) *
                                                (targetMax - targetMin) /
                                                (originalMax - originalMin));
    }
    // api.hpp's UnitType is a plain enum class and does not carry the Java
    // UnitType instance fields; these mirror battlecode.common.UnitType's
    // per-type constants that this class reads.
    static constexpr int paintCapacityOf(UnitType t) {
        switch (t) {
            case UnitType::SOLDIER: return 200;
            case UnitType::SPLASHER: return 300;
            case UnitType::MOPPER: return 100;
            default: return 1000;
        }
    }
    static constexpr int paintPerTurnOf(UnitType t) {
        switch (t) {
            case UnitType::LEVEL_ONE_PAINT_TOWER: return 5;
            case UnitType::LEVEL_TWO_PAINT_TOWER: return 10;
            case UnitType::LEVEL_THREE_PAINT_TOWER: return 15;
            default: return 0;
        }
    }
    static constexpr int attackStrengthOf(UnitType t) {
        switch (t) {
            case UnitType::SOLDIER: return 50;
            case UnitType::SPLASHER: return -1;
            case UnitType::MOPPER: return -1;
            case UnitType::LEVEL_ONE_DEFENSE_TOWER: return 40;
            case UnitType::LEVEL_TWO_DEFENSE_TOWER: return 50;
            case UnitType::LEVEL_THREE_DEFENSE_TOWER: return 60;
            default: return 20;
        }
    }
    static constexpr int aoeAttackStrengthOf(UnitType t) {
        switch (t) {
            case UnitType::SOLDIER: return -1;
            case UnitType::SPLASHER: return 100;
            case UnitType::MOPPER: return -1;
            case UnitType::LEVEL_ONE_DEFENSE_TOWER: return 20;
            case UnitType::LEVEL_TWO_DEFENSE_TOWER: return 25;
            case UnitType::LEVEL_THREE_DEFENSE_TOWER: return 30;
            default: return 10;
        }
    }

    // api.hpp's RobotController has no canSenseRobotAtLocation(MapLocation);
    // declared here (engine-provided, definition-less like the rest of the shim)
    // so the Java call is preserved verbatim.
    static bool canSenseRobotAtLocation(RobotController rc, MapLocation loc);

    static void retreat(RobotController rc);
    static void stealPaint(RobotController rc);   // package-private in Java
    static void donatePaint(RobotController rc);  // package-private in Java
    static void run(RobotController rc);
};

}  // namespace philip_06
