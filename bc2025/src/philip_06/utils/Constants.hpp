#pragma once
#include "api.hpp"
#include "Pathfinding.hpp"
#include "utils/Random.hpp"

namespace philip_06 {
namespace utils {

struct Constants {
    static RobotController rc;

    static const Direction directions[8];
    static const Direction cardinalDirections[4];
    static const Direction ordinalDirections[4];

    static Random rng;              // philip_06::utils::Random (custom class)
    static Pathfinding pathfind;    // philip_06::Pathfinding (by value)
    static MapLocation spawn;
    static MapLocation destination;
    static MapLocation closestTower;
    static MapLocation closestPaintTower;
    static MapLocation closestPaintTowerHasPaint;
    static MapLocation closestEnemyTower;
    static int noEnemyTowers;
    static int noEnemyRobots;
    static int noAlliedRobots;
    static int turnsAlive;

    static void setup(RobotController rc);
    static void update(RobotController rc);

    // api.hpp models UnitType as a plain `enum class`, so the engine's
    // per-type data fields (`UnitType.paintPerTurn`, `UnitType.paintCapacity`,
    // ...) that the Java bot reads as `rc.getType().paintPerTurn` do not
    // exist. These two lookups reproduce the engine's tables exactly
    // (battlecode.common.UnitType) and are kept as members of Constants so
    // they cannot collide with helpers added by other translation units.
    // Java `x.getType().paintPerTurn` -> `Constants::paintPerTurn(x.getType())`.
    static int paintPerTurn(UnitType t) {
        switch (t) {
            case UnitType::LEVEL_ONE_PAINT_TOWER: return 5;
            case UnitType::LEVEL_TWO_PAINT_TOWER: return 10;
            case UnitType::LEVEL_THREE_PAINT_TOWER: return 15;
            default: return 0;
        }
    }
    static int paintCapacity(UnitType t) {
        switch (t) {
            case UnitType::SOLDIER: return 200;
            case UnitType::SPLASHER: return 300;
            case UnitType::MOPPER: return 100;
            default: return 1000;  // every tower level has capacity 1000
        }
    }
};

}  // namespace utils
}  // namespace philip_06
