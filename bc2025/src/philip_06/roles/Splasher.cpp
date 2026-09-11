#include "roles/Splasher.hpp"

#include <algorithm>
#include <cmath>
#include <iostream>

#include "Helper/Comms.hpp"
#include "RobotPlayer.hpp"
#include "roles/Mopper.hpp"
#include "utils/Utils.hpp"

namespace philip_06 {
namespace roles {

using philip_06::Helper::Comms;
using philip_06::utils::Utils;

Random* Splasher::rng = nullptr;
bool Splasher::type = false;
MapLocation Splasher::destination;  // Java: null
int Splasher::opponentPaintSquares = 0;
std::unordered_set<MapLocation> Splasher::paintTowers;
int Splasher::turnsSinceLastAttack = -100;
bool Splasher::targetRuinsOnly = false;
MapLocation Splasher::oppSpawn;  // Java: null

void Splasher::retreat(RobotController rc) {
    MapLocation bestOpt;  // Java: null
    for (const MapLocation& curr : paintTowers) {
        if (bestOpt.isNull() ||
            (rc.getLocation().distanceSquaredTo(curr) < rc.getLocation().distanceSquaredTo(bestOpt) &&
             (!rc.canSenseLocation(bestOpt) || !rc.senseRobotAtLocation(bestOpt).getLocation().isNull()))) {
            bestOpt = curr;
        }
    }
    if (bestOpt.isNull()) {
        bestOpt = getNextCorner(rc);
        Mopper::moveTowardsMindfully(rc, bestOpt);
        return;
    }
    int transfer = paintCapacity(rc.getType()) - rc.getPaint();
    if (rc.canSenseLocation(bestOpt) && !rc.senseRobotAtLocation(bestOpt).getLocation().isNull()) {
        transfer = std::min(transfer, rc.senseRobotAtLocation(bestOpt).getPaintAmount());
        rc.setIndicatorString(std::to_string(transfer));
        if (rc.canTransferPaint(bestOpt, -transfer)) rc.transferPaint(bestOpt, -transfer);
    }
    Mopper::moveTowardsMindfully(rc, bestOpt);
}

void Splasher::bestRuinAttack(RobotController rc) {
    MapLocation closestRuin = Utils::closestRuin(rc);
    (void)closestRuin;  // Java: assigned but unused in this method
    bool forced = false;
    int best = -1000;
    MapLocation target;  // Java: null
    vector<MapInfo> nearby = rc.senseNearbyMapInfos(4);
    int xavg = 0, yavg = 0;

    for (const MapInfo& loc : rc.senseNearbyMapInfos(-1)) {
        if (isEnemy(loc.getPaint())) {
            opponentPaintSquares++;
            xavg += loc.getMapLocation().x;
            yavg += loc.getMapLocation().y;
        }
    }
    if (opponentPaintSquares != 0) {
        // Java Math.round(float) == floor(x + 0.5f)
        xavg = (int)std::floor((float)xavg / opponentPaintSquares + 0.5f);
        yavg = (int)std::floor((float)yavg / opponentPaintSquares + 0.5f);
        forced = rc.getLocation().isWithinDistanceSquared(MapLocation(xavg, yavg), 1);
    }
    /*
    int[] temp = new int[nearby.length];
    for(int i = 0; i<temp.length; i++){
        temp[i] = i;
    }
    Utils.shuffleArray(temp);
    */
    for (const MapInfo& loc : nearby) {
        int damage = 0;
        bool prim = false, sec = false;
        for (const MapInfo& hit : rc.senseNearbyMapInfos(loc.getMapLocation(), 4)) {
            // 1 for paint, 3 for enemy
            if (hit.isWall()) continue;
            if (isAlly(hit.getPaint())) {
                damage -= 2;
                if (hit.getPaint() == PaintType::ALLY_PRIMARY) {
                    prim = true;
                    if (sec)
                        break;
                }
                if (hit.getPaint() == PaintType::ALLY_SECONDARY) {
                    sec = true;
                    if (prim)
                        break;
                }
            }
            else if (hit.hasRuin() && (rc.senseRobotAtLocation(hit.getMapLocation()).getLocation().isNull() ||
                                       rc.senseRobotAtLocation(hit.getMapLocation()).getTeam() != rc.getTeam()))
                damage += 10000;
            else damage += 1;

        }
        if (damage >= best) {
            best = damage;
            target = loc.getMapLocation();
            if (sec)
                type = true;
            if (prim)
                type = false;
        }
    }
    if (opponentPaintSquares == 0)
        turnsSinceLastAttack = 0;
    if (best > 10000 || forced) {
        if (rc.canAttack(target)) {
            turnsSinceLastAttack = 0;
            rc.attack(target, type);
            Mopper::explore(rc);
        } else {
            turnsSinceLastAttack++;
            Mopper::explore(rc);
        }
    } else if (opponentPaintSquares != 0) {
        turnsSinceLastAttack++;
        Mopper::explore(rc);
    } else {
        turnsSinceLastAttack++;
        Mopper::explore(rc);
    }
}

void Splasher::bestAttack(RobotController rc) {
    MapLocation closestRuin = Utils::closestRuin(rc);
    bool forced = false;
    int best = -1000;
    MapLocation target;  // Java: null
    vector<MapInfo> nearby = rc.senseNearbyMapInfos(4);
    int xavg = 0, yavg = 0;

    for (const MapInfo& loc : rc.senseNearbyMapInfos(-1)) {
        if (loc.isResourcePatternCenter() && isEnemy(loc.getPaint())) {
            opponentPaintSquares += 10;
            xavg += 10 * loc.getMapLocation().x;
            yavg += 10 * loc.getMapLocation().y;
        } else if (isEnemy(loc.getPaint())) {
            opponentPaintSquares++;
            xavg += loc.getMapLocation().x;
            yavg += loc.getMapLocation().y;
        }
    }
    if (opponentPaintSquares != 0) {
        // Java Math.round(float) == floor(x + 0.5f)
        xavg = (int)std::floor((float)xavg / opponentPaintSquares + 0.5f);
        yavg = (int)std::floor((float)yavg / opponentPaintSquares + 0.5f);
        forced = rc.getLocation().isWithinDistanceSquared(MapLocation(xavg, yavg), 1);
    }
    /*
    int[] temp = new int[nearby.length];
    for(int i = 0; i<temp.length; i++){
        temp[i] = i;
    }
    Utils.shuffleArray(temp);
    */
    for (const MapInfo& loc : nearby) {
        int damage = 0;
        bool prim = false, sec = false;
        for (const MapInfo& hit : rc.senseNearbyMapInfos(loc.getMapLocation(), 4)) {
            // 1 for paint, 3 for enemy
            if (hit.isWall() || hit.hasRuin()) continue;
            if (isAlly(hit.getPaint())) {
                damage--;
                if (hit.getPaint() == PaintType::ALLY_PRIMARY) {
                    prim = true;
                    if (sec)
                        break;
                }
                if (hit.getPaint() == PaintType::ALLY_SECONDARY) {
                    sec = true;
                    if (prim)
                        break;
                }
            }
            else if (hit.getPaint() == PaintType::EMPTY) damage += 1;
            else if (hit.getMapLocation().distanceSquaredTo(loc.getMapLocation()) <= 2) {
                if (hit.isResourcePatternCenter() && isEnemy(hit.getPaint()))
                    damage += 30;
                else if (!closestRuin.isNull() && closestRuin.isWithinDistanceSquared(hit.getMapLocation(), 8))
                    damage += 5;
                else
                    damage += 3;
            }
        }
        if (damage >= best) {
            best = damage;
            target = loc.getMapLocation();
            if (sec)
                type = true;
            if (prim)
                type = false;
        }
    }
    if (opponentPaintSquares == 0)
        turnsSinceLastAttack = 0;
    if (best > 11 || forced) {
        if (rc.canAttack(target)) {
            turnsSinceLastAttack = 0;
            rc.attack(target, type);
            if (opponentPaintSquares != 0 &&
                rc.canMove(rc.getLocation().directionTo(MapLocation(xavg, yavg)).opposite()))
                rc.move(rc.getLocation().directionTo(MapLocation(xavg, yavg)).opposite());
        } else {
            turnsSinceLastAttack++;
            //Mopper.explore(rc);
        }
    } else if (opponentPaintSquares != 0) {
        turnsSinceLastAttack++;
        Mopper::moveTowardsMindfully(rc, MapLocation(xavg, yavg));
    } else {
        turnsSinceLastAttack++;
        //Mopper.explore(rc);
    }
}

Direction Splasher::shouldMove(RobotController rc, Direction dir) {
    if (!rc.canMove(dir)) return Direction::all[Direction::CENTER];  // Java: null
    vector<MapLocation> nearby = rc.senseNearbyRuins(16);
    for (const MapLocation& loc : nearby) {
        if (!canSenseRobotAtLocation(rc, loc)) continue;
        RobotInfo tower = rc.senseRobotAtLocation(loc);
        if (tower.getTeam() == rc.getTeam()) continue;
        dir = rc.getLocation().directionTo(loc).opposite();
    }
    if (rc.canSenseLocation(rc.getLocation().add(dir)) &&
        !isEnemy(rc.senseMapInfo(rc.getLocation().add(dir)).getPaint()))
        return dir;
    dir = dir.rotateRight();
    if (rc.canSenseLocation(rc.getLocation().add(dir)) &&
        !isEnemy(rc.senseMapInfo(rc.getLocation().add(dir)).getPaint()))
        return dir;
    dir = dir.rotateLeft();
    dir = dir.rotateLeft();
    if (rc.canSenseLocation(rc.getLocation().add(dir)) &&
        !isEnemy(rc.senseMapInfo(rc.getLocation().add(dir)).getPaint()))
        return dir;
    return Direction::all[Direction::CENTER];  // Java: null
}

MapLocation Splasher::getNextCorner(RobotController rc) {
    if (rng == nullptr) rng = &RobotPlayer::rng;
    int x = rng->nextInt(3) * (rc.getMapWidth() / 2), y = rng->nextInt(3) * (rc.getMapHeight() / 2);
    x = std::max(0, std::min(rc.getMapWidth() - 1, x + rng->nextInt() % 3));
    y = std::max(0, std::min(rc.getMapHeight() - 1, y + rng->nextInt() % 3));
    return MapLocation(x, y);
}

void Splasher::run(RobotController rc) {
    if (rc.getRoundNum() < 4 || rc.getID() % 20 == 0)
        targetRuinsOnly = true;
    if (targetRuinsOnly) {
        bestRuinAttack(rc);
        return;
    }
    if (rng == nullptr) rng = &RobotPlayer::rng;
    for (const MapLocation& loc : rc.senseNearbyRuins(-1)) {
        RobotInfo tower = rc.senseRobotAtLocation(loc);
        if (tower.getLocation().isNull() || tower.getTeam() == opponent(rc.getTeam())) {
            if (!tower.getLocation().isNull())
                RobotPlayer::lastEnemyTower = tower.getLocation();
            paintTowers.erase(loc);
            continue;
        }
        if (tower.getPaintAmount() >= 150 || paintPerTurn(tower.getType()) > 0)
            paintTowers.insert(loc);
        else
            paintTowers.erase(loc);
    }

    Comms::sendMsg(rc);
    Comms::getMsg(rc);
    if (rc.getPaint() < 10) {
        for (const RobotInfo& robot : rc.senseNearbyRobots(2)) {
            if (robot.getTeam() == rc.getTeam() && isRobotType(robot.getType()) &&
                robot.getType() != UnitType::MOPPER && robot.getPaintAmount() > 50) {
                std::cout << "goodbye" << '\n';
                rc.disintegrate();
            }
        }
    }
    if (rc.getPaint() < 50) {
        retreat(rc);
        rc.setIndicatorString("retreat");
        return;
    }
    opponentPaintSquares = 0;
    //if (oppSpawn == null) destination = oppSpawn = new MapLocation(rc.getMapWidth()-rc.getLocation().x,rc.getMapHeight()-rc.getLocation().y);
    /*
    int pri = -1;
    for (Message mess : rc.readMessages(-1)) {
        int[] action = Comms.decode(mess.getBytes());

        // Only care about recent messages
        if (rc.getRoundNum() - action[4] > 50) continue;

        // action[5] = 0 => attack location
        if (action[5] == 0) {
            if (action[1] > pri) {
                pri = action[1];
                destination = new MapLocation(action[2], action[3]);
            }
        }
    }*/

    if (destination.isNull() || rc.getLocation().distanceSquaredTo(destination) < 9 ||
        rc.getRoundNum() % 69 == 0)
        destination = getNextCorner(rc);
    bestAttack(rc);
    if (opponentPaintSquares == 0) {
        Mopper::moveTowardsMindfully(rc, destination);
    }
    if (rc.isMovementReady()) {
        MapLocation best;  // Java: null
        for (const MapInfo& loc : rc.senseNearbyMapInfos(-1)) {
            if (isAlly(loc.getPaint()) &&
                (best.isNull() || rc.getLocation().distanceSquaredTo(loc.getMapLocation()) <
                                      rc.getLocation().distanceSquaredTo(best))) {
                best = loc.getMapLocation();
            }
        }
        if (!best.isNull()) {
            Mopper::moveTowardsMindfully(rc, best);
        }
    }
}

}  // namespace roles
}  // namespace philip_06
