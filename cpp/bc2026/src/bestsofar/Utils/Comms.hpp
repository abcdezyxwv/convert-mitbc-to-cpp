#pragma once
#include "api.hpp"
#include "Utils/Globals.hpp"

namespace Utils {

// api.hpp's RobotInfo has no `getCarryingRobot()` (only RobotController's own
// `getCarrying()`), so squeakEnemies()'s `enemy.getCarryingRobot()` is routed
// through this engine-facing declaration (definition-less, like the rest of the
// shim). Ideally api.hpp gains `RobotInfo RobotInfo::getCarryingRobot() const`.
RobotInfo getCarryingRobot(const RobotInfo& robot);

struct Comms : Globals {
    static void init();
    static void startTurn();
    static int getNumKings();
    static int getSymmetry();
    static void updateSymmetry(int x);
    static int encodeDir(Direction dir);
    static Direction decodeDir(int dir);
    static void squeakEnemies();
    static vector<AdditionalClasses::Threat> readThreats();
    static void alertHunters(RobotInfo cat);
    static void updatePreyLoc(MapLocation loc);
    static MapLocation getPreyLoc();
    static void squeakEnemyKing(MapLocation loc);
    static MapLocation getEnemyKing();
    static void squeakNewKing(MapLocation mine);
    static MapLocation checkForNewKings();
    static void encodeNewKingPos(MapLocation mine);
    static void clearNewKing();
    static int getNumberBots();
    static void incNewKingBotCount(int cur);
    static MapLocation needNewKing();
    static void beingThrown();
    static vector<AdditionalClasses::Thrown> getAlliesThrown();
    static void squeakForSacrifices(MapLocation loc);
    static void squeakForSacrificesToo(MapLocation loc);
    static MapLocation getSacrifices();
};

}  // namespace Utils
