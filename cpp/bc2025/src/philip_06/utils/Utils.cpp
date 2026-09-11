#include "utils/Utils.hpp"
#include "utils/Constants.hpp"

namespace philip_06 {
namespace utils {

// `import static philip_06.utils.Constants.rng;` -> Constants::rng
// (distance()/getColour()/getPaint() stay inline in Utils.hpp: they are
// one-line hot helpers called from every role each turn.)

MapLocation Utils::closest(MapLocation loc, const vector<MapLocation>& locs) {
    MapLocation closest = MapLocation::NONE;
    int minDist = 1000000;
    for (const MapLocation& l : locs) {
        int dist = distance(loc, l);
        if (dist < minDist) {
            minDist = dist;
            closest = l;
        }
    }
    return closest;
}

MapInfo Utils::closestInfo(MapLocation loc, const vector<MapInfo>& locs) {
    // MapInfo has no NONE sentinel in api.hpp; a default MapInfo's
    // getMapLocation() is MapLocation::NONE, used as the null proxy.
    MapInfo closest = MapInfo();
    int minDist = 1000000;
    for (const MapInfo& l : locs) {
        int dist = distance(loc, l.getMapLocation());
        if (dist < minDist) {
            minDist = dist;
            closest = l;
        }
    }
    return closest;
}

double Utils::threatLevel(MapLocation loc, RobotController rc) {
    MapLocation oppSpawn(rc.getMapWidth() - Constants::spawn.x,
                         rc.getMapHeight() - Constants::spawn.y);
    return -std::sqrt((double)loc.distanceSquaredTo(oppSpawn)) +
           std::sqrt((double)loc.distanceSquaredTo(Constants::spawn));
}

bool Utils::spawn(RobotController rc, UnitType type) {
    for (const Direction& dir : Constants::directions) {
        if (rc.canBuildRobot(type, rc.getLocation().add(dir))) {
            rc.buildRobot(type, rc.getLocation().add(dir));
            return true;
        }
    }
    return false;
}

void Utils::checkResources(RobotController rc) {
    for (const MapLocation& loc :
         rc.getAllLocationsWithinRadiusSquared(rc.getLocation(), -1)) {
        if (loc.y % 3 == 2 && std::abs(loc.x - loc.y) % 4 == 0 &&
            rc.canCompleteResourcePattern(loc)) {
            rc.completeResourcePattern(loc);
        }
    }
}

void Utils::attackTowers(RobotController rc) {
    if (Constants::closestEnemyTower.isNull())
        return;
    if (rc.canAttack(Constants::closestEnemyTower))
        rc.attack(Constants::closestEnemyTower, getColour(Constants::closestEnemyTower));
    if (rc.canMove(rc.getLocation().directionTo(Constants::closestEnemyTower).opposite()))
        rc.move(rc.getLocation().directionTo(Constants::closestEnemyTower).opposite());
}

RobotInfo Utils::closestEnemyTower(RobotController rc) {
    // RobotInfo has no NONE sentinel in api.hpp; a default RobotInfo's
    // location is MapLocation::NONE, used here as the null proxy.
    RobotInfo ans = RobotInfo();
    for (const MapLocation& loc : rc.senseNearbyRuins(-1)) {
        RobotInfo info = rc.senseRobotAtLocation(loc);
        if (info.getLocation().isNull() || info.getTeam() == rc.getTeam()) continue;
        if (ans.getLocation().isNull() ||
            info.location.distanceSquaredTo(rc.getLocation()) <
                ans.location.distanceSquaredTo(rc.getLocation()))
            ans = info;
    }
    return ans;
}

void Utils::shuffleArray(vector<int>& array) {
    int index;
    for (int i = (int)array.size() - 1; i > 0; i--) {
        index = Constants::rng.nextInt() % (i + 1);
        if (index != i) {
            int temp = array[index];
            array[index] = array[i];
            array[i] = temp;
        }
    }
}

MapLocation Utils::closestRuin(RobotController rc) {
    MapLocation best = MapLocation::NONE;
    for (const MapLocation& loc : rc.senseNearbyRuins(-1)) {
        if (rc.senseRobotAtLocation(loc).getLocation().isNull() &&
            (best.isNull() || best.distanceSquaredTo(rc.getLocation()) >
                                  loc.distanceSquaredTo(rc.getLocation())))
            best = loc;
    }
    return best;
}

}  // namespace utils
}  // namespace philip_06
