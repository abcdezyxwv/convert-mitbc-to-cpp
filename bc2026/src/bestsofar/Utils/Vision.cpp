#include "Utils/Vision.hpp"

#include <cmath>

#include "Utils/AdditionalClasses/Thrown.hpp"
#include "Utils/Globals.hpp"

namespace Utils {

int64_t Vision::hasSeen[60] = {};
Vision::IsWallBits Vision::isWall;
Vision::IsDirtBits Vision::isDirt;
int64_t Vision::hasCheeseMine[60] = {};
int64_t Vision::isReachable[60] = {};
Vision::IsWallBits Vision::isDangerous;

vector<RobotInfo> Vision::enemies;
vector<MapLocation> Vision::walls;
int Vision::numWalls = 0;
vector<MapLocation> Vision::mines;
int Vision::numMines = 0;

// mirrors battlecode.common.UnitType's per-type constants
int Vision::visionConeRadiusSquared(UnitType t) {
    switch (t) {
        case UnitType::BABY_RAT: return 20;
        case UnitType::RAT_KING: return 25;
        case UnitType::CAT: return 17;
    }
    return 0;
}

int Vision::visionConeAngle(UnitType t) {
    switch (t) {
        case UnitType::BABY_RAT: return 90;
        case UnitType::RAT_KING: return 360;
        case UnitType::CAT: return 180;
    }
    return 0;
}

// mirrors MapLocation.isWithinDistanceSquared(location, distanceSquared,
// facingDir, theta) (useBottomLeft == false)
bool Vision::isWithinDistanceSquaredCone(MapLocation self, MapLocation location,
                                         int distanceSquared, Direction facingDir, double theta) {
    if (self == location) {
        return true;
    }

    double adjustment = 1e-3;

    bool isValidDistance = self.distanceSquaredTo(location) <= distanceSquared;

    double dx = location.x - self.x;
    double dy = location.y - self.y;

    bool isValidAngle;
    if (facingDir == Direction::all[Direction::CENTER]) {
        isValidAngle = true;
    } else {
        double cosSim = (facingDir.dx * dx + facingDir.dy * dy) /
                        (std::sqrt((dx * dx + dy * dy) * (double)(facingDir.dx * facingDir.dx +
                                                                  facingDir.dy * facingDir.dy)));
        double halfAngle = std::abs(std::acos(cosSim)) * 180.0 / M_PI;
        isValidAngle = halfAngle - adjustment <= theta / 2;
    }
    return isValidDistance && isValidAngle;
}

void Vision::lookAround() {
    // System.out.println(Clock.getBytecodeNum());

    for (const MapInfo& mi : rc.senseNearbyMapInfos()) {
        int x = mi.getMapLocation().x, y = mi.getMapLocation().y;

        if (((hasSeen[x] >> y) & 1) == 0 || ((isWall[x] >> y) & 1) == 0) {
            hasSeen[x] |= 1LL << y;
            if (mi.isWall()) isWall[x] |= 1LL << y;
            if (mi.hasCheeseMine()) hasCheeseMine[x] |= 1LL << y;
            if (mi.isDirt()) isDirt[x] |= 1LL << y;
            else isDirt[x] &= ~(1LL << y);
        }
    }

    // System.out.println(Clock.getBytecodeNum());
}

void Vision::turn(Direction dir) {
    if (dir == Direction::all[Direction::CENTER] || dir == rc.getDirection() || cantTurn ||
        !rc.canTurn())
        return;
    rc.turn(dir);
    lookAround();
}

bool Vision::turnLeft = false;

Direction Vision::bestTurn() {
    int sumX = rc.getLocation().x, sumY = rc.getLocation().y;
    for (int i = 0; i < (int)newestSqueaks.size(); i++) {
        sumX += newestSqueaks[i].getSource().x;
        sumY += newestSqueaks[i].getSource().y;
    }
    sumX = (sumX + ((int)newestSqueaks.size() + 1) / 2) / ((int)newestSqueaks.size() + 1);
    sumY = (sumY + ((int)newestSqueaks.size() + 1) / 2) / ((int)newestSqueaks.size() + 1);
    Direction d = rc.getLocation().directionTo(MapLocation(sumX, sumY)).opposite();
    if (d == Direction::all[Direction::CENTER]) {
        turnLeft = !turnLeft;
        if (turnLeft) return rc.getDirection().rotateLeft().rotateLeft();
        return rc.getDirection().rotateRight().rotateRight();
    }
    return d;
}

void Vision::turnJustBecause() {
    if (rc.canTurn() && enemyRobots.size() == 0 && newestSqueaks.size() == 0) turn(bestTurn());
}

void Vision::senseNearbyEnemies() {
    enemies = rc.senseNearbyRobots(visionConeRadiusSquared(rc.getType()), opponentTeam);
}

bool Vision::seenByEnemies() {
    for (const RobotInfo& ri : enemies) {
        if (isWithinDistanceSquaredCone(rc.getLocation(), ri.location,
                                        visionConeRadiusSquared(ri.getType()), ri.getDirection(),
                                        visionConeAngle(ri.getType()))) {
            return true;
        }
    }
    return false;
}

void Vision::digDirt(MapLocation loc) {
    isDirt[loc.x] &= ~(1LL << loc.y);
}

void Vision::placeDirt(MapLocation loc) {
    isDirt[loc.x] |= 1LL << loc.y;
}

bool Vision::hasSeenLocation(MapLocation loc) {
    return rc.onTheMap(loc) && ((hasSeen[loc.x] >> loc.y) & 1) > 0;
}

bool Vision::hasSeenLocationKnownToBeOnMap(MapLocation loc) {
    return ((hasSeen[loc.x] >> loc.y) & 1) > 0;
}

bool Vision::sensePassability(MapLocation loc) {
    return ((isWall[loc.x] >> loc.y) & 1) == 0 && ((isDirt[loc.x] >> loc.y) & 1) == 0;
}

// Java `isDirt(MapLocation)` -> Vision::IsDirtBits::operator() in Vision.hpp
// Java `isWall(MapLocation)` -> Vision::IsWallBits::operator() in Vision.hpp

bool Vision::canReach(MapLocation loc) {
    return ((isReachable[loc.x] >> loc.y) & 1) > 0;
}

// Java `isDangerous(MapLocation)` -> Vision::IsWallBits::operator() in Vision.hpp

bool Vision::isPassableWithDig(MapLocation loc) {
    return ((isWall[loc.x] >> loc.y) & 1) == 0;
}

bool Vision::isMine(MapLocation loc) {
    return ((hasCheeseMine[loc.x] >> loc.y) & 1) > 0;
}

void Vision::init() {
}

void Vision::startTurn() {
    if (rc.getType() == UnitType::BABY_RAT)
        lookAround();
    // TODO: optimise by detecting canDig nearby or canMove nearby
    for (const AdditionalClasses::Thrown& throwns : alliesThrown) {
        MapLocation loc = throwns.loc.add(throwns.dir);
        if (hasSeenLocation(loc)) {
            isDangerous[loc.x] |= (1LL << loc.y);
        }
        loc = loc.add(throwns.dir);
        if (hasSeenLocation(loc)) {
            isDangerous[loc.x] |= (1LL << loc.y);
        }
    }
}

void Vision::endTurn() {
    for (const AdditionalClasses::Thrown& throwns : alliesThrown) {
        MapLocation loc = throwns.loc.add(throwns.dir);
        if (hasSeenLocation(loc)) {
            isDangerous[loc.x] &= ~(1LL << loc.y);
        }
        loc = loc.add(throwns.dir);
        if (hasSeenLocation(loc)) {
            isDangerous[loc.x] &= ~(1LL << loc.y);
        }
    }
}

}  // namespace Utils
