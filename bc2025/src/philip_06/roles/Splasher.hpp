#pragma once
#include "api.hpp"
#include <unordered_set>


namespace philip_06 {
namespace roles {

struct Splasher {
    // Java: `static Random rng = null;` - an object *reference* that is aliased
    // to RobotPlayer.rng (shared RNG stream), so it maps to a pointer, with
    // nullptr as Java's null.
    static Random* rng;

    static bool type;
    static MapLocation destination;
    static int opponentPaintSquares;
    static std::unordered_set<MapLocation> paintTowers;
    static int turnsSinceLastAttack;
    static bool targetRuinsOnly;
    static MapLocation oppSpawn;

    static void retreat(RobotController rc);
    static void bestRuinAttack(RobotController rc);
    static void bestAttack(RobotController rc);
    // Java returns Direction or null; Direction::CENTER is used as the null
    // sentinel (this method is dead code - nothing calls it).
    static Direction shouldMove(RobotController rc, Direction dir);
    static MapLocation getNextCorner(RobotController rc);
    static void run(RobotController rc);
};

}  // namespace roles
}  // namespace philip_06
