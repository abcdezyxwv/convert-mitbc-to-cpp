#include "Pathfinding.hpp"
#include "utils/Constants.hpp"
#include "utils/Settings.hpp"
#include "utils/Utils.hpp"
#include "roles/Mopper.hpp"
#include <algorithm>

namespace philip_06 {

MapLocation Pathfinding::dest;        // Java: = null
MapLocation Pathfinding::destination; // Java: = null
int Pathfinding::TurnsWasted = 0;

// api.hpp's UnitType is a plain enum class without fields; Java's
// UnitType.paintCapacity values (bc2025 engine, UnitType ctor arg 6):
// SOLDIER=200, SPLASHER=300, MOPPER=100, every tower=1000.
static int paintCapacityOf(UnitType t) {
    switch (t) {
        case UnitType::SOLDIER: return 200;
        case UnitType::SPLASHER: return 300;
        case UnitType::MOPPER: return 100;
        default: return 1000;
    }
}

void Pathfinding::setDest(RobotController rc, MapLocation loc) {
    if (loc.isNull()) {
        dest = MapLocation(utils::Constants::rng.nextInt() % rc.getMapWidth(),
                           utils::Constants::rng.nextInt() % rc.getMapHeight());
    } else {
        dest = loc;
    }
}

void Pathfinding::makeMove(RobotController rc) {
    if (dest.isNull()) dest = MapLocation(rc.getMapWidth() / 2, rc.getMapHeight() / 2);
    rc.setIndicatorLine(rc.getLocation(), dest, 0, 255, 255);
    roles::Mopper::moveTowardsMindlessly(rc, dest);
}

void Pathfinding::move(RobotController rc, MapLocation loc) {
    setDest(rc, loc);
    makeMove(rc);
}

void Pathfinding::explore(RobotController rc) {
    roles::Mopper::explore(rc);
}

void Pathfinding::rush(RobotController rc) {
    MapLocation target;
    double cur = -100000;
    vector<MapInfo> scan = rc.senseNearbyMapInfos();
    //System.out.println(Clock.getBytecodeNum());
    vector<int> temp(scan.size());
    for (int i = 0; i < (int)temp.size(); i++) {
        temp[i] = i;
    }
    //System.out.println(Clock.getBytecodeNum());
    utils::Utils::shuffleArray(temp);
    //System.out.println(Clock.getBytecodeNum());
    for (int i = 0; i < (int)scan.size(); i++) {
        const MapInfo& loc = scan[temp[i]];
        if (loc.isPassable()) {
            if (target.isNull() || utils::Utils::threatLevel(loc.getMapLocation(), rc) > cur) {
                target = loc.getMapLocation();
                cur = utils::Utils::threatLevel(loc.getMapLocation(), rc);
            }
        }
    }
    //System.out.println(Clock.getBytecodeNum());
    if (!target.isNull() && rc.canSenseLocation(target) &&
        isAlly(rc.senseMapInfo(target).getPaint())) {
        target = MapLocation::NONE;
    }
    if (target.isNull()) {
        explore(rc);
    } else {
        setDest(rc, target);
        makeMove(rc);
    }
}

void Pathfinding::turtle(RobotController rc) {
    MapLocation target;
    vector<MapInfo> scan = rc.senseNearbyMapInfos();
    vector<int> temp(scan.size());
    for (int i = 0; i < (int)temp.size(); i++) {
        temp[i] = i;
    }
    utils::Utils::shuffleArray(temp);
    for (int i = 0; i < (int)scan.size(); i++) {
        const MapInfo& loc = scan[temp[i]];
        if (loc.isPassable()) {
            if ((target.isNull() ||
                 loc.getMapLocation().distanceSquaredTo(rc.getLocation()) <
                     target.distanceSquaredTo(rc.getLocation())) &&
                loc.getPaint() == PaintType::EMPTY) {
                target = loc.getMapLocation();
            }
        }
    }
    if (target.isNull()) {
        explore(rc);
    } else {
        setDest(rc, target);
        makeMove(rc);
    }
}

void Pathfinding::retreat(RobotController rc) {
    rc.setIndicatorString("retreat");
    if (!utils::Constants::closestPaintTowerHasPaint.isNull())
        rc.setIndicatorLine(rc.getLocation(), utils::Constants::closestPaintTowerHasPaint, 0, 0, 255);
    if (rc.getPaint() <= utils::Settings::lowPaint &&
        !utils::Constants::closestPaintTowerHasPaint.isNull()) {
        setDest(rc, utils::Constants::closestPaintTowerHasPaint);
        rc.setIndicatorString("found paint");
    } else if (!utils::Constants::closestPaintTower.isNull()) {
        setDest(rc, utils::Constants::closestPaintTower);
        rc.setIndicatorString("found paint tower");
    } else {
        rc.setIndicatorString("explore");
        explore(rc);
        return;
    }
    if (rc.getPaint() <= utils::Settings::lowPaint) {
        if (!utils::Constants::closestTower.isNull() &&
            rc.canSenseLocation(utils::Constants::closestTower)) {
            if (rc.canTransferPaint(
                    utils::Constants::closestTower,
                    -std::min(paintCapacityOf(rc.getType()) - rc.getPaint(),
                              rc.senseRobotAtLocation(utils::Constants::closestTower).paintAmount -
                                  utils::Settings::minTowerPaintToTransfer)))
                rc.transferPaint(
                    utils::Constants::closestTower,
                    -std::min(paintCapacityOf(rc.getType()) - rc.getPaint(),
                              rc.senseRobotAtLocation(utils::Constants::closestTower).paintAmount -
                                  utils::Settings::minTowerPaintToTransfer));
        }
    }
    makeMove(rc);
}

bool Pathfinding::canMoveFriendly(RobotController rc, Direction dir) {
    return rc.canMove(dir) &&
           isAlly(rc.senseMapInfo(rc.getLocation().add(dir)).getPaint());
}

void Pathfinding::wander(RobotController rc) {
    if (destination.isNull() || destination == rc.getLocation() ||
        rc.getRoundNum() % 69 == 0 || TurnsWasted >= 3) {
        destination = MapLocation(utils::Constants::rng.nextInt() % rc.getMapWidth(),
                                  utils::Constants::rng.nextInt() % rc.getMapHeight());
        TurnsWasted = 0;
    }
    Direction dir = rc.getLocation().directionTo(destination);
    if (canMoveFriendly(rc, dir)) {
        rc.move(dir);
        return;
    }
    dir = dir.rotateLeft();
    if (canMoveFriendly(rc, dir)) {
        rc.move(dir);
        return;
    }
    dir = dir.rotateRight();
    dir = dir.rotateRight();
    if (canMoveFriendly(rc, dir)) {
        rc.move(dir);
        return;
    }
    TurnsWasted++;
    dir = dir.rotateRight();
    if (canMoveFriendly(rc, dir)) {
        rc.move(dir);
        return;
    }
    dir = dir.opposite();
    if (canMoveFriendly(rc, dir)) {
        rc.move(dir);
        return;
    }
    dir = dir.rotateLeft();
    if (canMoveFriendly(rc, dir)) {
        rc.move(dir);
        return;
    }
    dir = dir.rotateLeft();
    dir = dir.rotateLeft();
    if (canMoveFriendly(rc, dir)) {
        rc.move(dir);
        return;
    }
    dir = dir.rotateRight();
    if (canMoveFriendly(rc, dir)) {
        rc.move(dir);
        return;
    }
}

MapInfo Pathfinding::findClosestAllyCell(RobotController rc) {
    vector<MapInfo> nearby = rc.senseNearbyMapInfos();
    MapInfo closest;  // Java: null (loc == MapLocation::NONE acts as the null sentinel)
    for (const MapInfo& mi : nearby) {
        if (!isAlly(mi.getPaint()) || !mi.isPassable())
            continue;
        if (closest.getMapLocation().isNull() ||
            rc.getLocation().distanceSquaredTo(mi.getMapLocation()) <
                rc.getLocation().distanceSquaredTo(closest.getMapLocation())) {
            closest = mi;
        }
    }
    return closest;
}

MapInfo Pathfinding::findFurthestAllyCell(RobotController rc) {
    vector<MapInfo> nearby = rc.senseNearbyMapInfos();
    MapInfo furthest;
    for (const MapInfo& mi : nearby) {
        if (!isAlly(mi.getPaint()) || !mi.isPassable())
            continue;
        if (furthest.getMapLocation().isNull() ||
            rc.getLocation().distanceSquaredTo(mi.getMapLocation()) >
                rc.getLocation().distanceSquaredTo(furthest.getMapLocation())) {
            furthest = mi;
        }
    }
    return furthest;
}

MapInfo Pathfinding::findClosestEnemyCell(RobotController rc) {
    vector<MapInfo> nearby = rc.senseNearbyMapInfos();
    MapInfo closest;
    for (const MapInfo& mi : nearby) {
        if (!isEnemy(mi.getPaint()) || !mi.isPassable())
            continue;
        if (closest.getMapLocation().isNull() ||
            rc.getLocation().distanceSquaredTo(mi.getMapLocation()) <
                rc.getLocation().distanceSquaredTo(closest.getMapLocation())) {
            closest = mi;
        }
    }
    return closest;
}

MapInfo Pathfinding::findFurthestEnemyCell(RobotController rc) {
    vector<MapInfo> nearby = rc.senseNearbyMapInfos();
    MapInfo furthest;
    for (const MapInfo& mi : nearby) {
        if (!isEnemy(mi.getPaint()) || !mi.isPassable())
            continue;
        if (furthest.getMapLocation().isNull() ||
            rc.getLocation().distanceSquaredTo(mi.getMapLocation()) >
                rc.getLocation().distanceSquaredTo(furthest.getMapLocation())) {
            furthest = mi;
        }
    }
    return furthest;
}

}  // namespace philip_06
