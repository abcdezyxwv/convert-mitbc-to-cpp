#include "roles/Mopper.hpp"

#include <algorithm>
#include <iostream>

#include "Helper/Comms.hpp"
#include "RobotPlayer.hpp"
#include "SoldierState/Fill.hpp"
#include "roles/Splasher.hpp"

namespace philip_06 {
namespace roles {

const Direction Mopper::directions[8] = {
    Direction::all[Direction::NORTH],
    Direction::all[Direction::NORTHEAST],
    Direction::all[Direction::EAST],
    Direction::all[Direction::SOUTHEAST],
    Direction::all[Direction::SOUTH],
    Direction::all[Direction::SOUTHWEST],
    Direction::all[Direction::WEST],
    Direction::all[Direction::NORTHWEST],
};
// Java: static HashMap<Direction, Integer> directionsOrder = null;
// The "== null" test below becomes .empty() (it is filled with all 8 entries at once).
std::unordered_map<Direction, int> Mopper::directionsOrder;
Mopper::State Mopper::mood = Mopper::State::NICE;

void Mopper::shuffleArray(vector<MapInfo>& array) {
    int index;
    for (int i = (int)array.size() - 1; i > 0; i--) {
        index = philip_06::RobotPlayer::rng.nextInt(i + 1);
        if (index != i) {
            MapInfo temp = array[index];
            array[index] = array[i];
            array[i] = temp;
        }
    }
}

MapLocation Mopper::destination = MapLocation::NONE;
int Mopper::TurnsWasted = 0;

bool Mopper::canMoveMopper(RobotController rc, Direction dir) {
    return rc.canMove(dir) && isAlly(rc.senseMapInfo(rc.getLocation().add(dir)).getPaint()) &&
           (closestEnemyTower.isNull() ||
            closestEnemyTower.distanceSquaredTo(rc.getLocation().add(dir)) > 9 ||
            closestEnemyTower.distanceSquaredTo(rc.getLocation().add(dir)) >
                closestEnemyTower.distanceSquaredTo(rc.getLocation()));
}

void Mopper::wander(RobotController rc) {
    if (!rc.isMovementReady())
        return;
    if (destination.isNull() || rc.canSenseLocation(destination) || rc.getRoundNum() % 69 == 0 ||
        TurnsWasted >= 3) {
        destination = (rc.getID()) % 4 == 0
                          ? MapLocation(philip_06::RobotPlayer::rng.nextInt(rc.getMapWidth()),
                                        philip_06::RobotPlayer::rng.nextInt(rc.getMapHeight()))
                          : philip_06::roles::Splasher::getNextCorner(rc);
        TurnsWasted = 0;
    }
    pastLocs.clear();
    rc.setIndicatorLine(rc.getLocation(), destination, 255, 255, 0);
    Direction dir = rc.getLocation().directionTo(destination);
    if (canMoveMopper(rc, dir)) {
        rc.move(dir);
        return;
    }
    dir = dir.rotateLeft();
    if (canMoveMopper(rc, dir)) {
        rc.move(dir);
        return;
    }
    dir = dir.rotateRight();
    dir = dir.rotateRight();
    if (canMoveMopper(rc, dir)) {
        rc.move(dir);
        return;
    }
    TurnsWasted++;
    dir = dir.rotateRight();
    if (canMoveMopper(rc, dir)) {
        rc.move(dir);
        return;
    }
    dir = dir.opposite();
    if (canMoveMopper(rc, dir)) {
        rc.move(dir);
        return;
    }
    dir = dir.rotateLeft();
    if (canMoveMopper(rc, dir)) {
        rc.move(dir);
        return;
    }
    dir = dir.rotateLeft();
    dir = dir.rotateLeft();
    if (canMoveMopper(rc, dir)) {
        rc.move(dir);
        return;
    }
    dir = dir.rotateRight();
    if (canMoveMopper(rc, dir)) {
        rc.move(dir);
        return;
    }
}

MapLocation Mopper::randomDestination = MapLocation::NONE;

bool Mopper::explore(RobotController rc) {
    if (!rc.isMovementReady())
        return false;
    if (randomDestination.isNull() || randomDestination == rc.getLocation() ||
        rc.getRoundNum() % 69 == 0) {
        randomDestination = (rc.getID()) % 4 == 0
                                ? MapLocation(philip_06::RobotPlayer::rng.nextInt(rc.getMapWidth()),
                                              philip_06::RobotPlayer::rng.nextInt(rc.getMapHeight()))
                                : philip_06::roles::Splasher::getNextCorner(rc);
    }
    pastLocs.clear();
    return moveTowardsMindfully(rc, randomDestination);
}

void Mopper::resetDest(RobotController rc) {
    randomDestination = (rc.getID()) % 4 == 0
                            ? MapLocation(philip_06::RobotPlayer::rng.nextInt(rc.getMapWidth()),
                                          philip_06::RobotPlayer::rng.nextInt(rc.getMapHeight()))
                            : philip_06::roles::Splasher::getNextCorner(rc);
}

/// add tower evasion
bool Mopper::moveRight = true, Mopper::stuck = false;
vector<MapLocation> Mopper::pastLocs;

bool Mopper::noBacktrack(RobotController rc, Direction dir) {
    if (pastLocs.size() == 4) {
        for (int i = 0; i < 3; i++)
            pastLocs[i] = pastLocs[i + 1];
        pastLocs.pop_back();
    }
    for (const MapLocation& loc : pastLocs)
        if (rc.getLocation().add(dir) == loc)
            return false;
    return true;
}

bool Mopper::moveTowardsMindlessly(RobotController rc, MapLocation loc) {
    if (!rc.isMovementReady())
        return false;
    rc.setIndicatorLine(rc.getLocation(), loc, 255, 0, 255);
    Direction dir = rc.getLocation().directionTo(loc);
    if (rc.getRoundNum() % 120 == 0)
        moveRight = !moveRight;
    if (rc.canMove(dir) && isAlly(rc.senseMapInfo(rc.getLocation().add(dir)).getPaint()) && noBacktrack(rc, dir)) {
        rc.move(dir);
        pastLocs.push_back(rc.getLocation());
        stuck = false;
        return true;
    }
    if (moveRight)
        dir = dir.rotateRight();
    else
        dir = dir.rotateLeft();
    if (rc.canMove(dir) && isAlly(rc.senseMapInfo(rc.getLocation().add(dir)).getPaint()) && noBacktrack(rc, dir)) {
        rc.move(dir);
        pastLocs.push_back(rc.getLocation());
        stuck = false;
        return true;
    }
    if (moveRight)
        dir = dir.rotateLeft();
    else
        dir = dir.rotateRight();
    if (moveRight)
        dir = dir.rotateLeft();
    else
        dir = dir.rotateRight();
    if (!stuck) {
        if (rc.canMove(dir) && isAlly(rc.senseMapInfo(rc.getLocation().add(dir)).getPaint()) && noBacktrack(rc, dir)) {
            rc.move(dir);
            pastLocs.push_back(rc.getLocation());
            return true;
        }
    }
    if (moveRight)
        dir = dir.rotateRight();
    else
        dir = dir.rotateLeft();
    if (rc.canMove(dir) && !isEnemy(rc.senseMapInfo(rc.getLocation().add(dir)).getPaint()) && noBacktrack(rc, dir)) {
        rc.move(dir);
        pastLocs.push_back(rc.getLocation());
        stuck = false;
        return true;
    }
    if (moveRight)
        dir = dir.rotateRight();
    else
        dir = dir.rotateLeft();
    if (rc.canMove(dir) && !isEnemy(rc.senseMapInfo(rc.getLocation().add(dir)).getPaint()) && noBacktrack(rc, dir)) {
        rc.move(dir);
        pastLocs.push_back(rc.getLocation());
        stuck = false;
        return true;
    }
    if (moveRight)
        dir = dir.rotateLeft();
    else
        dir = dir.rotateRight();
    if (moveRight)
        dir = dir.rotateLeft();
    else
        dir = dir.rotateRight();
    if (!stuck) {
        if (rc.canMove(dir) && !isEnemy(rc.senseMapInfo(rc.getLocation().add(dir)).getPaint()) && noBacktrack(rc, dir)) {
            rc.move(dir);
            pastLocs.push_back(rc.getLocation());
            return true;
        }
    }
    if (moveRight)
        dir = dir.rotateRight();
    else
        dir = dir.rotateLeft();
    if (rc.canMove(dir) && noBacktrack(rc, dir)) {
        rc.move(dir);
        pastLocs.push_back(rc.getLocation());
        stuck = false;
        return true;
    }
    if (moveRight)
        dir = dir.rotateRight();
    else
        dir = dir.rotateLeft();
    if (rc.canMove(dir) && noBacktrack(rc, dir)) {
        rc.move(dir);
        pastLocs.push_back(rc.getLocation());
        stuck = false;
        return true;
    }
    if (moveRight)
        dir = dir.rotateLeft();
    else
        dir = dir.rotateRight();
    if (moveRight)
        dir = dir.rotateLeft();
    else
        dir = dir.rotateRight();
    if (!stuck) {
        if (rc.canMove(dir) && noBacktrack(rc, dir)) {
            rc.move(dir);
            pastLocs.push_back(rc.getLocation());
            return true;
        }
    }
    if (moveRight)
        dir = dir.rotateRight();
    else
        dir = dir.rotateLeft();
    stuck = true;
    rc.setIndicatorString("Stuck" + string(moveRight ? "Right" : "Left"));
    if (moveRight) {
        dir = dir.rotateRight();
        dir = dir.rotateRight();
        if (rc.canMove(dir) && noBacktrack(rc, dir)) {
            rc.move(dir);
            pastLocs.push_back(rc.getLocation());
            return false;
        }
        dir = dir.rotateRight();
        if (rc.canMove(dir) && noBacktrack(rc, dir)) {
            rc.move(dir);
            pastLocs.push_back(rc.getLocation());
            return false;
        }
        dir = dir.rotateRight();
        if (rc.canMove(dir) && noBacktrack(rc, dir)) {
            rc.move(dir);
            pastLocs.push_back(rc.getLocation());
            return false;
        }
        dir = dir.rotateRight();
        if (rc.canMove(dir) && noBacktrack(rc, dir)) {
            rc.move(dir);
            pastLocs.push_back(rc.getLocation());
            return false;
        }
        dir = dir.rotateRight();
        if (rc.canMove(dir) && noBacktrack(rc, dir)) {
            rc.move(dir);
            pastLocs.push_back(rc.getLocation());
            return false;
        }
        dir = dir.rotateRight();
        if (rc.canMove(dir) && noBacktrack(rc, dir)) {
            rc.move(dir);
            pastLocs.push_back(rc.getLocation());
            return false;
        }
        dir = dir.rotateRight();
        if (rc.canMove(dir)) {
            rc.move(dir);
            pastLocs.push_back(rc.getLocation());
            return false;
        }
        dir = dir.rotateRight();
        if (rc.canMove(dir)) {
            rc.move(dir);
            pastLocs.push_back(rc.getLocation());
            return false;
        }
        dir = dir.rotateRight();
        if (rc.canMove(dir)) {
            rc.move(dir);
            pastLocs.push_back(rc.getLocation());
            return false;
        }
        dir = dir.rotateRight();
        if (rc.canMove(dir)) {
            rc.move(dir);
            pastLocs.push_back(rc.getLocation());
            return false;
        }
        dir = dir.rotateRight();
        if (rc.canMove(dir)) {
            rc.move(dir);
            pastLocs.push_back(rc.getLocation());
            return false;
        }
        dir = dir.rotateRight();
        if (rc.canMove(dir)) {
            rc.move(dir);
            pastLocs.push_back(rc.getLocation());
            return false;
        }
        dir = dir.rotateRight();
        if (rc.canMove(dir)) {
            rc.move(dir);
            pastLocs.push_back(rc.getLocation());
            return false;
        }
        dir = dir.rotateRight();
        if (rc.canMove(dir)) {
            rc.move(dir);
            pastLocs.push_back(rc.getLocation());
            return false;
        }
    } else {
        dir = dir.rotateLeft();
        dir = dir.rotateLeft();
        if (rc.canMove(dir) && noBacktrack(rc, dir)) {
            rc.move(dir);
            pastLocs.push_back(rc.getLocation());
            return false;
        }
        dir = dir.rotateLeft();
        if (rc.canMove(dir) && noBacktrack(rc, dir)) {
            rc.move(dir);
            pastLocs.push_back(rc.getLocation());
            return false;
        }
        dir = dir.rotateLeft();
        if (rc.canMove(dir) && noBacktrack(rc, dir)) {
            rc.move(dir);
            pastLocs.push_back(rc.getLocation());
            return false;
        }
        dir = dir.rotateLeft();
        if (rc.canMove(dir) && noBacktrack(rc, dir)) {
            rc.move(dir);
            pastLocs.push_back(rc.getLocation());
            return false;
        }
        dir = dir.rotateLeft();
        if (rc.canMove(dir) && noBacktrack(rc, dir)) {
            rc.move(dir);
            pastLocs.push_back(rc.getLocation());
            return false;
        }
        dir = dir.rotateLeft();
        if (rc.canMove(dir) && noBacktrack(rc, dir)) {
            rc.move(dir);
            pastLocs.push_back(rc.getLocation());
            return false;
        }
        dir = dir.rotateLeft();
        if (rc.canMove(dir)) {
            rc.move(dir);
            pastLocs.push_back(rc.getLocation());
            return false;
        }
        dir = dir.rotateLeft();
        if (rc.canMove(dir)) {
            rc.move(dir);
            pastLocs.push_back(rc.getLocation());
            return false;
        }
        dir = dir.rotateLeft();
        if (rc.canMove(dir)) {
            rc.move(dir);
            pastLocs.push_back(rc.getLocation());
            return false;
        }
        dir = dir.rotateLeft();
        if (rc.canMove(dir)) {
            rc.move(dir);
            pastLocs.push_back(rc.getLocation());
            return false;
        }
        dir = dir.rotateLeft();
        if (rc.canMove(dir)) {
            rc.move(dir);
            pastLocs.push_back(rc.getLocation());
            return false;
        }
        dir = dir.rotateLeft();
        if (rc.canMove(dir)) {
            rc.move(dir);
            pastLocs.push_back(rc.getLocation());
            return false;
        }
        dir = dir.rotateLeft();
        if (rc.canMove(dir)) {
            rc.move(dir);
            pastLocs.push_back(rc.getLocation());
            return false;
        }
        dir = dir.rotateLeft();
        if (rc.canMove(dir)) {
            rc.move(dir);
            pastLocs.push_back(rc.getLocation());
            return false;
        }
    }
    return false;
}

int Mopper::lastRefresh = -1;
bool Mopper::social[8] = {};

void Mopper::refresh(RobotController rc) {
    std::cout << Clock::getBytecodeNum() << '\n';
    if (directionsOrder.empty()) {
        for (int i = 0; i < 8; i++)
            directionsOrder[directions[i]] = i;
    }
    bool hasBad[5][5] = {};
    for (int i = -2; i <= 2; i++) {
        for (int j = -2; j <= 2; j++) {
            if (i == 0 && j == 0)
                continue;
            MapLocation loc = MapLocation(rc.getLocation().x + i, rc.getLocation().y + j);
            if (rc.canSenseLocation(loc) && !rc.senseRobotAtLocation(loc).location.isNull() &&
                rc.senseRobotAtLocation(loc).getTeam() == rc.getTeam())
                hasBad[i + 2][j + 2] = true;
        }
    }
    for (const Direction& dir : directions) {
        social[directionsOrder[dir]] = false;
        int a = rc.getLocation().add(dir).x, b = rc.getLocation().add(dir).y;
        /*
        for (int dx = -1; dx <= 1; dx++) {
            for (int dy = -1; dy <= 1; dy++) {
                if (hasBad[2+rc.getLocation().x-(a+dx)][2+rc.getLocation().y-(b+dy)]){
                    social[directionsOrder.get(dir)] = true;
                }
            }
        }
        */
    }
    std::cout << Clock::getBytecodeNum() << '\n';
    lastRefresh = rc.getRoundNum();
}

// Java: `public static RobotInfo closestEnemyTower(RobotController rc)`; renamed
// because the class also has a `MapLocation closestEnemyTower` field.
RobotInfo Mopper::closestEnemyTowerInfo(RobotController rc) {
    RobotInfo ans;  // Java: null -> default RobotInfo (location.isNull())
    for (const MapLocation& loc : rc.senseNearbyRuins(-1)) {
        RobotInfo info = rc.senseRobotAtLocation(loc);
        if (info.location.isNull() || info.getTeam() == rc.getTeam()) continue;
        if (ans.location.isNull() || info.location.distanceSquaredTo(rc.getLocation()) <
                                         ans.location.distanceSquaredTo(rc.getLocation()))
            ans = info;
    }
    return ans;
}

bool Mopper::moveTowardsMindfully(RobotController rc, MapLocation loc) {
    if (!rc.isMovementReady())
        return false;
    RobotInfo tower = closestEnemyTowerInfo(rc);
    rc.setIndicatorLine(rc.getLocation(), loc, 255, 255, 255);
    Direction dir = rc.getLocation().directionTo(loc);
    if (rc.getRoundNum() % 120 == 0)
        moveRight = !moveRight;
    if (rc.canMove(dir) && isAlly(rc.senseMapInfo(rc.getLocation().add(dir)).getPaint()) && noBacktrack(rc, dir) && (tower.location.isNull() || tower.location.distanceSquaredTo(rc.getLocation().add(dir)) > 9)) {
        rc.move(dir);
        pastLocs.push_back(rc.getLocation());
        stuck = false;
        return true;
    }
    if (moveRight)
        dir = dir.rotateRight();
    else
        dir = dir.rotateLeft();
    if (rc.canMove(dir) && isAlly(rc.senseMapInfo(rc.getLocation().add(dir)).getPaint()) && noBacktrack(rc, dir) && (tower.location.isNull() || tower.location.distanceSquaredTo(rc.getLocation().add(dir)) > 9)) {
        rc.move(dir);
        pastLocs.push_back(rc.getLocation());
        stuck = false;
        return true;
    }
    if (moveRight)
        dir = dir.rotateLeft();
    else
        dir = dir.rotateRight();
    if (moveRight)
        dir = dir.rotateLeft();
    else
        dir = dir.rotateRight();
    if (!stuck) {
        if (rc.canMove(dir) && isAlly(rc.senseMapInfo(rc.getLocation().add(dir)).getPaint()) && noBacktrack(rc, dir) && (tower.location.isNull() || tower.location.distanceSquaredTo(rc.getLocation().add(dir)) > 9)) {
            rc.move(dir);
            pastLocs.push_back(rc.getLocation());
            return true;
        }
    }
    if (moveRight)
        dir = dir.rotateRight();
    else
        dir = dir.rotateLeft();
    if (rc.canMove(dir) && !isEnemy(rc.senseMapInfo(rc.getLocation().add(dir)).getPaint()) && noBacktrack(rc, dir) && (tower.location.isNull() || tower.location.distanceSquaredTo(rc.getLocation().add(dir)) > 9)) {
        rc.move(dir);
        pastLocs.push_back(rc.getLocation());
        stuck = false;
        return true;
    }
    if (moveRight)
        dir = dir.rotateRight();
    else
        dir = dir.rotateLeft();
    if (rc.canMove(dir) && !isEnemy(rc.senseMapInfo(rc.getLocation().add(dir)).getPaint()) && noBacktrack(rc, dir) && (tower.location.isNull() || tower.location.distanceSquaredTo(rc.getLocation().add(dir)) > 9)) {
        rc.move(dir);
        pastLocs.push_back(rc.getLocation());
        stuck = false;
        return true;
    }
    if (moveRight)
        dir = dir.rotateLeft();
    else
        dir = dir.rotateRight();
    if (moveRight)
        dir = dir.rotateLeft();
    else
        dir = dir.rotateRight();
    if (!stuck) {
        if (rc.canMove(dir) && !isEnemy(rc.senseMapInfo(rc.getLocation().add(dir)).getPaint()) && noBacktrack(rc, dir) && (tower.location.isNull() || tower.location.distanceSquaredTo(rc.getLocation().add(dir)) > 9)) {
            rc.move(dir);
            pastLocs.push_back(rc.getLocation());
            return true;
        }
    }
    if (moveRight)
        dir = dir.rotateRight();
    else
        dir = dir.rotateLeft();
    if (rc.canMove(dir) && noBacktrack(rc, dir) && (tower.location.isNull() || tower.location.distanceSquaredTo(rc.getLocation().add(dir)) > 9)) {
        rc.move(dir);
        pastLocs.push_back(rc.getLocation());
        stuck = false;
        return true;
    }
    if (moveRight)
        dir = dir.rotateRight();
    else
        dir = dir.rotateLeft();
    if (rc.canMove(dir) && noBacktrack(rc, dir) && (tower.location.isNull() || tower.location.distanceSquaredTo(rc.getLocation().add(dir)) > 9)) {
        rc.move(dir);
        pastLocs.push_back(rc.getLocation());
        stuck = false;
        return true;
    }
    if (moveRight)
        dir = dir.rotateLeft();
    else
        dir = dir.rotateRight();
    if (moveRight)
        dir = dir.rotateLeft();
    else
        dir = dir.rotateRight();
    if (!stuck) {
        if (rc.canMove(dir) && noBacktrack(rc, dir) && (tower.location.isNull() || tower.location.distanceSquaredTo(rc.getLocation().add(dir)) > 9)) {
            rc.move(dir);
            pastLocs.push_back(rc.getLocation());
            return true;
        }
    }
    if (moveRight)
        dir = dir.rotateRight();
    else
        dir = dir.rotateLeft();
    /// UWU
    if (rc.canMove(dir) && isAlly(rc.senseMapInfo(rc.getLocation().add(dir)).getPaint()) && noBacktrack(rc, dir)) {
        rc.move(dir);
        pastLocs.push_back(rc.getLocation());
        stuck = false;
        return true;
    }
    if (moveRight)
        dir = dir.rotateRight();
    else
        dir = dir.rotateLeft();
    if (rc.canMove(dir) && isAlly(rc.senseMapInfo(rc.getLocation().add(dir)).getPaint()) && noBacktrack(rc, dir)) {
        rc.move(dir);
        pastLocs.push_back(rc.getLocation());
        stuck = false;
        return true;
    }
    if (moveRight)
        dir = dir.rotateLeft();
    else
        dir = dir.rotateRight();
    if (moveRight)
        dir = dir.rotateLeft();
    else
        dir = dir.rotateRight();
    if (!stuck) {
        if (rc.canMove(dir) && isAlly(rc.senseMapInfo(rc.getLocation().add(dir)).getPaint()) && noBacktrack(rc, dir)) {
            rc.move(dir);
            pastLocs.push_back(rc.getLocation());
            return true;
        }
    }
    if (moveRight)
        dir = dir.rotateRight();
    else
        dir = dir.rotateLeft();
    /// UWU UWU
    if (rc.canMove(dir) && !isEnemy(rc.senseMapInfo(rc.getLocation().add(dir)).getPaint()) && noBacktrack(rc, dir)) {
        rc.move(dir);
        pastLocs.push_back(rc.getLocation());
        stuck = false;
        return true;
    }
    if (moveRight)
        dir = dir.rotateRight();
    else
        dir = dir.rotateLeft();
    if (rc.canMove(dir) && !isEnemy(rc.senseMapInfo(rc.getLocation().add(dir)).getPaint()) && noBacktrack(rc, dir)) {
        rc.move(dir);
        pastLocs.push_back(rc.getLocation());
        stuck = false;
        return true;
    }
    if (moveRight)
        dir = dir.rotateLeft();
    else
        dir = dir.rotateRight();
    if (moveRight)
        dir = dir.rotateLeft();
    else
        dir = dir.rotateRight();
    if (!stuck) {
        if (rc.canMove(dir) && !isEnemy(rc.senseMapInfo(rc.getLocation().add(dir)).getPaint()) && noBacktrack(rc, dir)) {
            rc.move(dir);
            pastLocs.push_back(rc.getLocation());
            return true;
        }
    }
    if (moveRight)
        dir = dir.rotateRight();
    else
        dir = dir.rotateLeft();
    /// UWU UWU UWU
    rc.setIndicatorDot(rc.getLocation(), 120, 120, 120);
    if (rc.canMove(dir) && isAlly(rc.senseMapInfo(rc.getLocation().add(dir)).getPaint()) && noBacktrack(rc, dir)) {
        rc.move(dir);
        pastLocs.push_back(rc.getLocation());
        stuck = false;
        return true;
    }
    if (moveRight)
        dir = dir.rotateRight();
    else
        dir = dir.rotateLeft();
    if (rc.canMove(dir) && isAlly(rc.senseMapInfo(rc.getLocation().add(dir)).getPaint()) && noBacktrack(rc, dir)) {
        rc.move(dir);
        pastLocs.push_back(rc.getLocation());
        stuck = false;
        return true;
    }
    if (moveRight)
        dir = dir.rotateLeft();
    else
        dir = dir.rotateRight();
    if (moveRight)
        dir = dir.rotateLeft();
    else
        dir = dir.rotateRight();
    if (!stuck) {
        if (rc.canMove(dir) && isAlly(rc.senseMapInfo(rc.getLocation().add(dir)).getPaint()) && noBacktrack(rc, dir)) {
            rc.move(dir);
            pastLocs.push_back(rc.getLocation());
            return true;
        }
    }
    if (moveRight)
        dir = dir.rotateRight();
    else
        dir = dir.rotateLeft();
    if (rc.canMove(dir) && !isEnemy(rc.senseMapInfo(rc.getLocation().add(dir)).getPaint()) && noBacktrack(rc, dir)) {
        rc.move(dir);
        pastLocs.push_back(rc.getLocation());
        stuck = false;
        return true;
    }
    if (moveRight)
        dir = dir.rotateRight();
    else
        dir = dir.rotateLeft();
    if (rc.canMove(dir) && !isEnemy(rc.senseMapInfo(rc.getLocation().add(dir)).getPaint()) && noBacktrack(rc, dir)) {
        rc.move(dir);
        pastLocs.push_back(rc.getLocation());
        stuck = false;
        return true;
    }
    if (moveRight)
        dir = dir.rotateLeft();
    else
        dir = dir.rotateRight();
    if (moveRight)
        dir = dir.rotateLeft();
    else
        dir = dir.rotateRight();
    if (!stuck) {
        if (rc.canMove(dir) && !isEnemy(rc.senseMapInfo(rc.getLocation().add(dir)).getPaint()) && noBacktrack(rc, dir)) {
            rc.move(dir);
            pastLocs.push_back(rc.getLocation());
            return true;
        }
    }
    if (moveRight)
        dir = dir.rotateRight();
    else
        dir = dir.rotateLeft();
    if (rc.canMove(dir) && noBacktrack(rc, dir)) {
        rc.move(dir);
        pastLocs.push_back(rc.getLocation());
        stuck = false;
        return true;
    }
    if (moveRight)
        dir = dir.rotateRight();
    else
        dir = dir.rotateLeft();
    if (rc.canMove(dir) && noBacktrack(rc, dir)) {
        rc.move(dir);
        pastLocs.push_back(rc.getLocation());
        stuck = false;
        return true;
    }
    if (moveRight)
        dir = dir.rotateLeft();
    else
        dir = dir.rotateRight();
    if (moveRight)
        dir = dir.rotateLeft();
    else
        dir = dir.rotateRight();
    if (!stuck) {
        if (rc.canMove(dir) && noBacktrack(rc, dir)) {
            rc.move(dir);
            pastLocs.push_back(rc.getLocation());
            return true;
        }
    }
    if (moveRight)
        dir = dir.rotateRight();
    else
        dir = dir.rotateLeft();
    stuck = true;
    rc.setIndicatorString("Stuck" + string(moveRight ? "Right" : "Left"));
    if (moveRight) {
        dir = dir.rotateRight();
        dir = dir.rotateRight();
        if (rc.canMove(dir) && noBacktrack(rc, dir)) {
            rc.move(dir);
            pastLocs.push_back(rc.getLocation());
            return false;
        }
        dir = dir.rotateRight();
        if (rc.canMove(dir) && noBacktrack(rc, dir)) {
            rc.move(dir);
            pastLocs.push_back(rc.getLocation());
            return false;
        }
        dir = dir.rotateRight();
        if (rc.canMove(dir) && noBacktrack(rc, dir)) {
            rc.move(dir);
            pastLocs.push_back(rc.getLocation());
            return false;
        }
        dir = dir.rotateRight();
        if (rc.canMove(dir) && noBacktrack(rc, dir)) {
            rc.move(dir);
            pastLocs.push_back(rc.getLocation());
            return false;
        }
        dir = dir.rotateRight();
        if (rc.canMove(dir) && noBacktrack(rc, dir)) {
            rc.move(dir);
            pastLocs.push_back(rc.getLocation());
            return false;
        }
        dir = dir.rotateRight();
        if (rc.canMove(dir) && noBacktrack(rc, dir)) {
            rc.move(dir);
            pastLocs.push_back(rc.getLocation());
            return false;
        }
        dir = dir.rotateRight();
        if (rc.canMove(dir)) {
            rc.move(dir);
            pastLocs.push_back(rc.getLocation());
            return false;
        }
        dir = dir.rotateRight();
        if (rc.canMove(dir)) {
            rc.move(dir);
            pastLocs.push_back(rc.getLocation());
            return false;
        }
        dir = dir.rotateRight();
        if (rc.canMove(dir)) {
            rc.move(dir);
            pastLocs.push_back(rc.getLocation());
            return false;
        }
        dir = dir.rotateRight();
        if (rc.canMove(dir)) {
            rc.move(dir);
            pastLocs.push_back(rc.getLocation());
            return false;
        }
        dir = dir.rotateRight();
        if (rc.canMove(dir)) {
            rc.move(dir);
            pastLocs.push_back(rc.getLocation());
            return false;
        }
        dir = dir.rotateRight();
        if (rc.canMove(dir)) {
            rc.move(dir);
            pastLocs.push_back(rc.getLocation());
            return false;
        }
        dir = dir.rotateRight();
        if (rc.canMove(dir)) {
            rc.move(dir);
            pastLocs.push_back(rc.getLocation());
            return false;
        }
        dir = dir.rotateRight();
        if (rc.canMove(dir)) {
            rc.move(dir);
            pastLocs.push_back(rc.getLocation());
            return false;
        }
    } else {
        dir = dir.rotateLeft();
        dir = dir.rotateLeft();
        if (rc.canMove(dir) && noBacktrack(rc, dir)) {
            rc.move(dir);
            pastLocs.push_back(rc.getLocation());
            return false;
        }
        dir = dir.rotateLeft();
        if (rc.canMove(dir) && noBacktrack(rc, dir)) {
            rc.move(dir);
            pastLocs.push_back(rc.getLocation());
            return false;
        }
        dir = dir.rotateLeft();
        if (rc.canMove(dir) && noBacktrack(rc, dir)) {
            rc.move(dir);
            pastLocs.push_back(rc.getLocation());
            return false;
        }
        dir = dir.rotateLeft();
        if (rc.canMove(dir) && noBacktrack(rc, dir)) {
            rc.move(dir);
            pastLocs.push_back(rc.getLocation());
            return false;
        }
        dir = dir.rotateLeft();
        if (rc.canMove(dir) && noBacktrack(rc, dir)) {
            rc.move(dir);
            pastLocs.push_back(rc.getLocation());
            return false;
        }
        dir = dir.rotateLeft();
        if (rc.canMove(dir) && noBacktrack(rc, dir)) {
            rc.move(dir);
            pastLocs.push_back(rc.getLocation());
            return false;
        }
        dir = dir.rotateLeft();
        if (rc.canMove(dir)) {
            rc.move(dir);
            pastLocs.push_back(rc.getLocation());
            return false;
        }
        dir = dir.rotateLeft();
        if (rc.canMove(dir)) {
            rc.move(dir);
            pastLocs.push_back(rc.getLocation());
            return false;
        }
        dir = dir.rotateLeft();
        if (rc.canMove(dir)) {
            rc.move(dir);
            pastLocs.push_back(rc.getLocation());
            return false;
        }
        dir = dir.rotateLeft();
        if (rc.canMove(dir)) {
            rc.move(dir);
            pastLocs.push_back(rc.getLocation());
            return false;
        }
        dir = dir.rotateLeft();
        if (rc.canMove(dir)) {
            rc.move(dir);
            pastLocs.push_back(rc.getLocation());
            return false;
        }
        dir = dir.rotateLeft();
        if (rc.canMove(dir)) {
            rc.move(dir);
            pastLocs.push_back(rc.getLocation());
            return false;
        }
        dir = dir.rotateLeft();
        if (rc.canMove(dir)) {
            rc.move(dir);
            pastLocs.push_back(rc.getLocation());
            return false;
        }
        dir = dir.rotateLeft();
        if (rc.canMove(dir)) {
            rc.move(dir);
            pastLocs.push_back(rc.getLocation());
            return false;
        }
    }
    return false;
}

// unfinished stuff very important trust
MapLocation Mopper::enemyCell = MapLocation::NONE, Mopper::allyCell = MapLocation::NONE;

void Mopper::findEnemyCell(RobotController rc) {
    vector<MapInfo> nearby = rc.senseNearbyMapInfos();
    MapInfo closest;
    bool closestNull = true;  // Java: MapInfo closest = null
    for (const MapInfo& mi : nearby) {
        if (!isEnemy(mi.getPaint()))
            continue;
        if (closestNull || rc.getLocation().distanceSquaredTo(mi.getMapLocation()) <
                               rc.getLocation().distanceSquaredTo(closest.getMapLocation())) {
            closest = mi;
            closestNull = false;
        }
    }
    if (!closestNull)
        enemyCell = closest.getMapLocation();
    else enemyCell = MapLocation::NONE;
}

void Mopper::findAnyAllyCell(RobotController rc) {
    vector<MapInfo> nearby = rc.senseNearbyMapInfos();
    MapInfo closest;
    bool closestNull = true;  // Java: MapInfo closest = null
    for (const MapInfo& mi : nearby) {
        if (!isAlly(mi.getPaint()))
            continue;
        if (closestNull || rc.getLocation().distanceSquaredTo(mi.getMapLocation()) <
                               rc.getLocation().distanceSquaredTo(closest.getMapLocation())) {
            closest = mi;
            closestNull = false;
        }
    }
    if (!closestNull)
        allyCell = closest.getMapLocation();
}

void Mopper::findAllyCell(RobotController rc) {
    vector<MapInfo> nearby = rc.senseNearbyMapInfos();
    MapInfo furthest;
    bool furthestNull = true;  // Java: MapInfo furthest = null
    for (const MapInfo& mi : nearby) {
        if (!isAlly(mi.getPaint()) || !mi.isPassable())
            continue;
        if (furthestNull || rc.getLocation().distanceSquaredTo(mi.getMapLocation()) >
                                rc.getLocation().distanceSquaredTo(furthest.getMapLocation())) {
            furthest = mi;
            furthestNull = false;
        }
    }
    if (!furthestNull)
        allyCell = furthest.getMapLocation();
}

bool Mopper::cleanUpSomePaint(RobotController rc, MapLocation loc) {
    if ((!loc.isNull() && !rc.canAttack(loc)) || !rc.isActionReady())
        return false;
    vector<MapInfo> nearby = rc.senseNearbyMapInfos();
    MapInfo closest;
    bool closestNull = true;  // Java: MapInfo closest = null
    for (const MapInfo& mi : nearby) {
        if (!isEnemy(mi.getPaint()) || !rc.canSenseRobotAtLocation(mi.getMapLocation()) ||
            rc.senseRobotAtLocation(mi.getMapLocation()).location.isNull() ||
            rc.senseRobotAtLocation(mi.getMapLocation()).getTeam() == rc.getTeam())
            continue;
        if (!closestNull) {
            if (rc.getLocation().distanceSquaredTo(mi.getMapLocation()) <
                rc.getLocation().distanceSquaredTo(closest.getMapLocation())) {
                closest = mi;
            }
        } else {
            closest = mi;
            closestNull = false;
        }
    }
    if (!closestNull && rc.canAttack(closest.getMapLocation()))
        rc.attack(closest.getMapLocation());
    else if (!loc.isNull())
        rc.attack(loc);
    enemyCell = MapLocation::NONE;
    return true;
}

bool Mopper::paintEnemyCell(RobotController rc) {
    if (enemyCell.isNull() || !rc.isActionReady())
        return false;
    if (cleanUpSomePaint(rc, enemyCell)) {
        enemyCell = MapLocation::NONE;
        return true;
    }
    bool successful = moveTowardsMindfully(rc, enemyCell);
    if (!successful)
        return false;
    if (cleanUpSomePaint(rc, enemyCell)) {
        enemyCell = MapLocation::NONE;
        return true;
    }
    return false;
}

void Mopper::donatePaint(RobotController rc) {
    if (rc.getPaint() <= 60)
        return;
    vector<RobotInfo> nearby = rc.senseNearbyRobots(8, rc.getTeam());
    RobotInfo lowest;
    bool lowestNull = true;  // Java: RobotInfo lowest = null
    for (const RobotInfo& ri : nearby) {
        if (ri.type != UnitType::MOPPER && ri.type != UnitType::SPLASHER &&
            ri.type != UnitType::SOLDIER)
            continue;
        if (lowestNull || ri.getPaintAmount() < lowest.getPaintAmount()) {
            lowest = ri;
            lowestNull = false;
        }
    }
    if (lowestNull)
        return;
    if (lowest.type == UnitType::SPLASHER && lowest.getPaintAmount() >= 240)
        return;
    if (lowest.type == UnitType::MOPPER && lowest.getPaintAmount() >= 45)
        return;
    if (lowest.type == UnitType::SOLDIER && lowest.getPaintAmount() >= 120)
        return;
    int amt;
    if (lowest.type == UnitType::SPLASHER)
        amt = std::min(300 - lowest.getPaintAmount(), rc.getPaint() - 40);
    else if (lowest.type == UnitType::MOPPER)
        amt = std::min(100 - lowest.getPaintAmount(), rc.getPaint() - 50);
    else
        amt = std::min(200 - lowest.getPaintAmount(), rc.getPaint() - 50);
    if (!rc.canTransferPaint(lowest.getLocation(), amt))
        moveTowardsMindfully(rc, lowest.getLocation());
    if (rc.canTransferPaint(lowest.getLocation(), amt))
        rc.transferPaint(lowest.getLocation(), amt);
}

void Mopper::stealPaint(RobotController rc) {
    if (rc.getPaint() >= 90 || !rc.isActionReady())
        return;
    for (const RobotInfo& ri : rc.senseNearbyRobots(2, rc.getTeam())) {
        if (ri.type != UnitType::MOPPER && ri.type != UnitType::SPLASHER &&
            ri.type != UnitType::SOLDIER) {
            if (ri.getPaintAmount() > 10) {
                int amt = std::min(ri.getPaintAmount(), 100 - rc.getPaint());
                if (rc.canTransferPaint(ri.getLocation(), -amt)) {
                    rc.transferPaint(ri.getLocation(), -amt);
                    return;
                }
                bool ret = moveTowardsMindfully(rc, ri.getLocation());
                if (!ret)
                    return;
                if (rc.canTransferPaint(ri.getLocation(), -amt)) {
                    rc.transferPaint(ri.getLocation(), -amt);
                    return;
                }
            }
            return;
        }
    }
}

void Mopper::move(RobotController rc) {
    if (!rc.isMovementReady())
        return;
    if (isEnemy(rc.senseMapInfo(rc.getLocation()).getPaint())) {
        findAnyAllyCell(rc);
        if (allyCell.isNull()) {
            for (const Direction& dir : directions) {
                if (!isEnemy(rc.senseMapInfo(rc.getLocation().add(dir)).getPaint())) {
                    if (rc.canMove(dir)) {
                        rc.move(dir);
                        return;
                    }
                }
            }
            explore(rc);
        } else {
            moveTowardsMindfully(rc, allyCell);
            // Java compared MapLocation *references* with `==` here (identity, not
            // equals), which is never true for distinct objects -> kept as a
            // never-taken branch to preserve behaviour exactly.
            if (/* rc.getLocation() == allyCell */ false)
                allyCell = MapLocation::NONE;
        }
    } else if (isAlly(rc.senseMapInfo(rc.getLocation()).getPaint())) {
        if (enemyCell.isNull())
            wander(rc);
        else {
            if (rc.getLocation().distanceSquaredTo(enemyCell) <= 2 ||
                rc.getActionCooldownTurns() > 2)
                return;
            moveTowardsMindfully(rc, enemyCell);
        }
    } else {
        if (enemyCell.isNull() || rc.getActionCooldownTurns() > 2) {
            findAnyAllyCell(rc);
            if (allyCell.isNull()) {
                explore(rc);
            } else {
                moveTowardsMindfully(rc, allyCell);
                if (/* rc.getLocation() == allyCell */ false)
                    allyCell = MapLocation::NONE;
            }
        } else {
            if (rc.getLocation().distanceSquaredTo(enemyCell) <= 2) {
                if (!isAlly(rc.senseMapInfo(rc.getLocation()).getPaint())) {
                    findAnyAllyCell(rc);
                    if (allyCell.isNull()) {
                        for (const Direction& dir : directions) {
                            if (!isEnemy(rc.senseMapInfo(rc.getLocation().add(dir)).getPaint())) {
                                if (rc.canMove(dir)) {
                                    rc.move(dir);
                                    return;
                                }
                            }
                        }
                        explore(rc);
                    } else {
                        moveTowardsMindfully(rc, allyCell);
                        if (/* rc.getLocation() == allyCell */ false)
                            allyCell = MapLocation::NONE;
                    }
                }
                return;
            }
            moveTowardsMindfully(rc, enemyCell);
        }
    }
}

MapLocation Mopper::orderedTo = MapLocation::NONE;

void Mopper::followOrders(RobotController rc) {
    if (orderedTo.isNull())
        return;
    // System.out.println("Im a good bunny "+Clock.getBytecodeNum());
    rc.setIndicatorString("Folliwng orders to " + orderedTo.toString());
    rc.setIndicatorLine(rc.getLocation(), orderedTo, 69, 69, 255);
    if (rc.canSenseLocation(orderedTo) && !isEnemy(rc.senseMapInfo(orderedTo).getPaint())) {
        orderedTo = MapLocation::NONE;
        return;
    }
    if (!rc.canSenseLocation(orderedTo)) {
        cleanUpSomePaint(rc, MapLocation::NONE);
        moveTowardsMindfully(rc, orderedTo);
        cleanUpSomePaint(rc, MapLocation::NONE);
    } else {
        if (rc.canAttack(orderedTo)) {
            rc.attack(orderedTo);
            orderedTo = MapLocation::NONE;
            return;
        }
        moveTowardsMindfully(rc, orderedTo);
        if (rc.canAttack(orderedTo)) {
            rc.attack(orderedTo);
            orderedTo = MapLocation::NONE;
        }
    }
}

void Mopper::doStuff(RobotController rc) {
    philip_06::Helper::Comms::getMsg(rc);
    followOrders(rc);
    donatePaint(rc);
    findEnemyCell(rc);
    if (!enemyCell.isNull())
        paintEnemyCell(rc);
    move(rc);
    stealPaint(rc);
}

MapLocation Mopper::victim = MapLocation::NONE;

void Mopper::findClosestVictim(RobotController rc) {
    MapLocation closest = MapLocation::NONE;
    for (const RobotInfo& ri : rc.senseNearbyRobots(-1, opponent(rc.getTeam()))) {
        if (closest.isNull() || rc.getLocation().distanceSquaredTo(ri.getLocation()) <=
                                    rc.getLocation().distanceSquaredTo(closest))
            closest = ri.getLocation();
    }
    if (!closest.isNull())
        victim = closest;
}

bool Mopper::attackVictim(RobotController rc) {
    if (!rc.isActionReady())
        return false;
    if (victim.isNull() || rc.getLocation().distanceSquaredTo(victim) > 8)
        return false;
    if (rc.canAttack(victim)) {
        rc.attack(victim);
        return true;
    }
    bool successful = moveTowardsMindfully(rc, victim);
    if (!successful)
        return false;
    if (rc.canAttack(victim)) {
        rc.attack(victim);
        return true;
    }
    return false;
}

void Mopper::beBully(RobotController rc) {
    findClosestVictim(rc);
    bool isBully = attackVictim(rc);
    if (!isBully)
        doStuff(rc);
    else
        moveTowardsMindfully(rc, victim);
}

/// TODO: add feature where if cant move anywhere in a certain amount of time, then we explore for a
/// certain number of turns
int Mopper::paint(MapInfo loc) {
    PaintType curr = loc.getPaint();
    if (curr == PaintType::ALLY_PRIMARY || curr == PaintType::ALLY_SECONDARY || loc.isWall())
        return 1;
    if (curr == PaintType::EMPTY) return 0;
    else return -1;
}

MapLocation Mopper::closestEnemyTower;

void Mopper::run(RobotController rc) {
    RobotInfo tower = closestEnemyTowerInfo(rc);
    closestEnemyTower = tower.location.isNull() ? MapLocation::NONE : tower.location;
    switch (mood) {
        case State::NICE: doStuff(rc); break;
        case State::BULLY: beBully(rc); break;
        default: doStuff(rc); break;
    }
}

}  // namespace roles
}  // namespace philip_06
