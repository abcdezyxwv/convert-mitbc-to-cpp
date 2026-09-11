#pragma once
#include "api.hpp"
#include "Utils/Globals.hpp"

// api.hpp's UnitType is a plain `enum class` without the Java per-type fields,
// so the Java expression `someType.visionConeRadiusSquared` has no C++ member to
// bind to. Declared here (engine-provided, like the rest of api.hpp) so the call
// sites read the same. Same for RobotInfo.carryingRobot / getCarryingRobot(),
// which api.hpp's RobotInfo is missing. NOTE: both belong in api.hpp - see notes.
int visionConeRadiusSquared(UnitType t);
RobotInfo getCarryingRobot(const RobotInfo& r);

namespace Utils {

struct Attack : Globals {
    // Java `null` for a RobotInfo -> default-constructed RobotInfo (null location).
    static bool isNullRobot(const RobotInfo& r) { return r.location.isNull(); }
    // Java `null` for a Direction -> sentinel with an out-of-range ordinal.
    static constexpr Direction DIR_NULL{(Direction::E)9, 0, 0};
    // Java ArrayList<Direction>.contains(dir)
    static bool containsDir(const vector<Direction>& arr, Direction dir);

    static int holdingRounds;
    static const int cheeseToUse[];  // Java: public static final int[] (104 entries)

    static vector<Direction> getSafeDirections();
    static bool canUseTrap();

    static RobotInfo enemy;   // Java null -> needs a NONE-style sentinel on RobotInfo
    static int unknown;

    static vector<MapLocation> blindSpot(RobotInfo bad);

    static RobotInfo lastKnown;
    static int lastRound;

    static bool onevone();
    static vector<Direction> getInvisDirections();
    static bool trapType(UnitType type);
    static bool trapKing();
    static bool trapBaby();
    static bool trapCat();
    static bool canPickUp(MapLocation pos, RobotInfo enemy);
    static Direction bestThrowingDirection();
    static Direction newBestThrowingDirection(RobotInfo enemy);
    static int damageToCheese(int dam);
    static void catMicro();
    static bool scratch();
    static int steps(MapLocation start, MapLocation end);
    static void trapMicro();
    static bool retreat();
    static bool holdLine();
    static bool moveIn();
    static bool attack();
    static int throwDamage(MapLocation pos, Direction dir, RobotInfo enemy);
    static void gunner();
    static int indexOf(const vector<Direction>& arr, Direction dir);
    static bool willGetKidnapped(MapLocation loc, Direction dir, int ignoreID);
    static bool attackType(UnitType type);
    static bool attackKing();
    static bool attackBaby();
    static bool attackCat();
};

}  // namespace Utils
