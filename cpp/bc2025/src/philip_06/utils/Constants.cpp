#include "utils/Constants.hpp"
#include "utils/Settings.hpp"
#include "utils/Utils.hpp"
#include "Pathfinding.hpp"

namespace philip_06 {
namespace utils {

RobotController Constants::rc;

const Direction Constants::directions[8] = {
    Direction::all[Direction::NORTH],
    Direction::all[Direction::NORTHEAST],
    Direction::all[Direction::EAST],
    Direction::all[Direction::SOUTHEAST],
    Direction::all[Direction::SOUTH],
    Direction::all[Direction::SOUTHWEST],
    Direction::all[Direction::WEST],
    Direction::all[Direction::NORTHWEST],
};
const Direction Constants::cardinalDirections[4] = {
    Direction::all[Direction::NORTH],
    Direction::all[Direction::EAST],
    Direction::all[Direction::SOUTH],
    Direction::all[Direction::WEST],
};
const Direction Constants::ordinalDirections[4] = {
    Direction::all[Direction::NORTHEAST],
    Direction::all[Direction::SOUTHEAST],
    Direction::all[Direction::SOUTHWEST],
    Direction::all[Direction::NORTHWEST],
};

// Java leaves `rng`/`pathfind` null until setup() runs; philip_06::utils::Random
// has no default constructor, so the placeholder seed 0 stands in for null.
// setup() overwrites both before any use, matching Java's timing.
Random Constants::rng(0);
Pathfinding Constants::pathfind;
MapLocation Constants::spawn;
MapLocation Constants::destination;  // Java: = null
MapLocation Constants::closestTower;
MapLocation Constants::closestPaintTower;
MapLocation Constants::closestPaintTowerHasPaint;
MapLocation Constants::closestEnemyTower;
int Constants::noEnemyTowers = 0;
int Constants::noEnemyRobots = 0;
int Constants::noAlliedRobots = 0;
int Constants::turnsAlive = 0;

void Constants::setup(RobotController rc) {
    Constants::rc = rc;
    Constants::rng = Random(rc.getID());
    Constants::spawn = rc.getLocation();
    Constants::pathfind = Pathfinding();
}

void Constants::update(RobotController rc) {
    turnsAlive++;
    noEnemyTowers = 0;
    noEnemyRobots = 0;
    noAlliedRobots = 0;
    destination = MapLocation::NONE;
    vector<MapLocation> fakeRuins = rc.senseNearbyRuins(-1);
    for (const MapLocation& loc : fakeRuins) {
        // RobotInfo has no NONE sentinel in api.hpp; a default RobotInfo's
        // location is MapLocation::NONE, used here as the null proxy.
        if (rc.senseRobotAtLocation(loc).getLocation().isNull() &&
            (destination.isNull() || rc.getLocation().distanceSquaredTo(loc) <
                                         rc.getLocation().distanceSquaredTo(destination)))
            destination = loc;
    }
    if (!closestTower.isNull() && rc.canSenseLocation(closestTower) &&
        rc.senseRobotAtLocation(closestTower).getLocation().isNull())
        closestTower = MapLocation::NONE;
    if (!closestPaintTower.isNull() && rc.canSenseLocation(closestPaintTower) &&
        rc.senseRobotAtLocation(closestPaintTower).getLocation().isNull())
        closestPaintTower = MapLocation::NONE;
    if (!closestPaintTowerHasPaint.isNull() && rc.canSenseLocation(closestPaintTowerHasPaint) &&
        (rc.senseRobotAtLocation(closestPaintTowerHasPaint).getLocation().isNull() ||
         rc.senseRobotAtLocation(closestPaintTowerHasPaint).getPaintAmount() <=
             Settings::minTowerPaintToTransfer * 2))
        closestPaintTowerHasPaint = MapLocation::NONE;
    closestEnemyTower = MapLocation::NONE;
    vector<RobotInfo> robots = rc.senseNearbyRobots(-1);
    for (const RobotInfo& robot : robots) {
        if (robot.getTeam() == rc.getTeam()) {
            if (isRobotType(robot.getType())) {
                noAlliedRobots++;
                rc.setIndicatorDot(robot.getLocation(), 0, 255, 0);
            }
            if (isTowerType(robot.getType()) &&
                (closestTower.isNull() ||
                 Utils::distance(rc.getLocation(), robot.getLocation()) <
                     Utils::distance(rc.getLocation(), closestTower)))
                closestTower = robot.getLocation();
            if (isTowerType(robot.getType()) && paintPerTurn(rc.getType()) > 0 &&
                (closestPaintTower.isNull() ||
                 Utils::distance(rc.getLocation(), robot.getLocation()) <
                     Utils::distance(rc.getLocation(), closestPaintTower)) &&
                robot.getTeam() == rc.getTeam())
                closestPaintTower = robot.getLocation();
            if ((isTowerType(robot.getType()) &&
                 robot.getPaintAmount() > Settings::minTowerPaintToTransfer * 2) &&
                (closestPaintTowerHasPaint.isNull() ||
                 Utils::distance(rc.getLocation(), robot.getLocation()) <
                     Utils::distance(rc.getLocation(), closestPaintTowerHasPaint)))
                closestPaintTowerHasPaint = robot.getLocation();
        } else {
            if (isRobotType(robot.getType())) {
                noEnemyRobots++;
            } else if (isTowerType(robot.getType())) {
                noEnemyTowers++;
                if (closestEnemyTower.isNull() ||
                    Utils::distance(rc.getLocation(), robot.getLocation()) <
                        Utils::distance(rc.getLocation(), closestEnemyTower))
                    closestEnemyTower = robot.getLocation();
            }
        }
    }
}

}  // namespace utils
}  // namespace philip_06
