#pragma once
#include "api.hpp"
#include "Utils/Globals.hpp"

namespace Utils {

struct Vision : Globals {
    static int64_t hasSeen[60];  // Java: public static long[60]

    // The Java has BOTH a `public static long[] isWall` field AND a
    // `public static boolean isWall(MapLocation)` method (same for isDirt and
    // isDangerous). One name cannot be a field and a method in C++, so these
    // are functor objects that support BOTH `Vision::isWall[x]` (array access,
    // returns int64_t&) and `Vision::isWall(loc)` (the method's exact logic).
    // The .cpp must only define `Vision::IsWallBits Vision::isWall;` etc. -
    // there is no separate `isWall(MapLocation)` function to define.
    struct IsWallBits {
        int64_t v[60]{};
        int64_t& operator[](int i) { return v[i]; }
        int64_t operator[](int i) const { return v[i]; }
        // Java: public static boolean isWall(MapLocation loc)
        bool operator()(MapLocation loc) const {
            return ((v[loc.x] >> loc.y) & 1) > 0;
        }
    };
    struct IsDirtBits {
        int64_t v[60]{};
        int64_t& operator[](int i) { return v[i]; }
        int64_t operator[](int i) const { return v[i]; }
        // Java: public static boolean isDirt(MapLocation loc)
        bool operator()(MapLocation loc) const {
            return ((hasSeen[loc.x] >> loc.y) & 1) > 0 && ((v[loc.x] >> loc.y) & 1) > 0;
        }
    };
    static IsWallBits isWall;
    static IsDirtBits isDirt;
    static int64_t hasCheeseMine[60];
    static int64_t isReachable[60];
    static IsWallBits isDangerous;  // method form identical to isWall

    static vector<RobotInfo> enemies;
    static vector<MapLocation> walls;
    static int numWalls;
    static vector<MapLocation> mines;
    static int numMines;

    static bool turnLeft;

    // api.hpp's UnitType is a plain enum class and MapLocation only offers the
    // 2-argument isWithinDistanceSquared, so the engine's UnitType vision-cone
    // constants and the cone overload are mirrored here (values/logic copied
    // verbatim from battlecode.common.UnitType / MapLocation).
    // See notes: these belong in api.hpp.
    static int visionConeRadiusSquared(UnitType t);
    static int visionConeAngle(UnitType t);
    static bool isWithinDistanceSquaredCone(MapLocation self, MapLocation location,
                                            int distanceSquared, Direction facingDir,
                                            double theta);

    static void lookAround();
    static void turn(Direction dir);
    static Direction bestTurn();
    static void turnJustBecause();
    static void senseNearbyEnemies();
    static bool seenByEnemies();
    static void digDirt(MapLocation loc);
    static void placeDirt(MapLocation loc);
    static bool hasSeenLocation(MapLocation loc);
    static bool hasSeenLocationKnownToBeOnMap(MapLocation loc);
    static bool sensePassability(MapLocation loc);
    static bool canReach(MapLocation loc);
    static bool isPassableWithDig(MapLocation loc);
    static bool isMine(MapLocation loc);
    static void init();
    static void startTurn();
    static void endTurn();
};

}  // namespace Utils
