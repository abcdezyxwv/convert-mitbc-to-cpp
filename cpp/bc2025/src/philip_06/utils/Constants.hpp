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

};

}  // namespace utils
}  // namespace philip_06
