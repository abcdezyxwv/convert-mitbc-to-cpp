#include "SoldierState/Build.hpp"
#include "SoldierState/Attack.hpp"
#include "SoldierState/Fill.hpp"
#include "Helper/Comms.hpp"
#include "RobotPlayer.hpp"
#include "Soldier.hpp"
#include "roles/Mopper.hpp"
#include "roles/Splasher.hpp"
#include <algorithm>
#include <cmath>
#include <iostream>

namespace philip_06 {
namespace SoldierState {

using std::abs;
using std::max;

// java.util.Random.nextBoolean() has no equivalent on api.hpp's Random.
static inline bool rngNextBoolean() { return RobotPlayer::rng.nextInt(2) != 0; }

MapLocation Build::dest;         // Java: = null
MapLocation Build::destination;  // Java: = null
bool Build::found = false;
bool Build::built = false;

int Build::lastStuck = -100;
int Build::turnsWasted = 0;
int Build::moneyLastTurn = 0;
vector<MapLocation> Build::toFinish;
vector<int> Build::turnAdded;
bool Build::movingTowardsToFinish = false;
MapLocation Build::enemyPaintCell;  // Java: = null
MapLocation Build::halfBuilt;       // Java: = null
int Build::turnEnemyPaintCell = -100;
bool Build::askForMopper = false;
MapLocation Build::wontBegForMore;  // Java: = null

void Build::run(RobotController rc) {
    if (rc.getNumberTowers() == 25) {
        Attack::run(rc);
        return;
    }
    // api.hpp has no canSenseRobotAtLocation; a default RobotInfo's location is
    // MapLocation::NONE, used here as the "no robot there" proxy.
    if ((!halfBuilt.isNull() && rc.canSenseLocation(halfBuilt) &&
         !rc.senseRobotAtLocation(halfBuilt).getLocation().isNull()) ||
        (!halfBuilt.isNull() && !toFinish.empty() && halfBuilt.x == toFinish.back().x &&
         halfBuilt.y == toFinish.back().y)) {
        //std::cout << "Byebye halfbuilt" << '\n';
        halfBuilt = MapLocation::NONE;
    }
    if (askForMopper) {
        for (const RobotInfo& bot : rc.senseNearbyRobots(-1, rc.getTeam())) {
            if (bot.getType() == UnitType::MOPPER) {
                askForMopper = false;
                enemyPaintCell = MapLocation::NONE;
                break;
            }
        }
        if (!isAlly(rc.senseMapInfo(rc.getLocation()).getPaint()) && rc.canAttack(rc.getLocation()))
            rc.attack(rc.getLocation(), true);
        for (const Direction& direction : Fill::directions) {
            if (rc.onTheMap(rc.getLocation().add(direction)) &&
                !isAlly(rc.senseMapInfo(rc.getLocation().add(direction)).getPaint()) &&
                rc.canAttack(rc.getLocation().add(direction))) {
                rc.attack(rc.getLocation().add(direction), true);
            }
        }
        Helper::Comms::sendMsg(rc);
        Soldier::retreat(rc);
        rc.setIndicatorString("begging for a mopper");
        return;
    }
    if (turnsWasted == 3 && rc.getRoundNum() - lastStuck <= 6) {
        halfBuilt = MapLocation::NONE;
        roles::Mopper::explore(rc);
        if (rc.senseMapInfo(rc.getLocation()).getPaint() == PaintType::EMPTY &&
            rc.canAttack(rc.getLocation()))
            rc.attack(rc.getLocation(), rngNextBoolean());
        for (const Direction& dir : Direction::allDirections())
            if (rc.canSenseLocation(rc.getLocation().add(dir)) &&
                rc.senseMapInfo(rc.getLocation().add(dir)).getPaint() == PaintType::EMPTY &&
                rc.canAttack(rc.getLocation().add(dir)))
                rc.attack(rc.getLocation().add(dir), rngNextBoolean());
        rc.setIndicatorString("Exploring");
        moneyLastTurn = rc.getMoney();
        return;
    }
    if (!halfBuilt.isNull())
        destination = halfBuilt;
    rc.setIndicatorString("Building ahh");
    rc.setIndicatorDot(rc.getLocation(), 0, 255, 0);
    if (rc.getNumberTowers() == GameConstants::MAX_NUMBER_OF_TOWERS) return;
    for (const MapLocation& loc : rc.senseNearbyRuins(-1)) {
        if (rc.canCompleteTowerPattern(UnitType::LEVEL_ONE_PAINT_TOWER, loc)) {
            if (rc.getType() == UnitType::SOLDIER && movingTowardsToFinish &&
                toFinish.back() == loc) {
                toFinish.pop_back();
                movingTowardsToFinish = false;
            }
            rc.completeTowerPattern(UnitType::LEVEL_ONE_PAINT_TOWER, loc);
            built = true;
        }
        if (rc.canCompleteTowerPattern(UnitType::LEVEL_ONE_MONEY_TOWER, loc)) {
            if (rc.getType() == UnitType::SOLDIER && movingTowardsToFinish &&
                toFinish.back() == loc) {
                toFinish.pop_back();
                movingTowardsToFinish = false;
            }
            rc.completeTowerPattern(UnitType::LEVEL_ONE_MONEY_TOWER, loc);
            built = true;
        }
        if (rc.canCompleteTowerPattern(UnitType::LEVEL_ONE_DEFENSE_TOWER, loc)) {
            if (rc.getType() == UnitType::SOLDIER && movingTowardsToFinish &&
                toFinish.back() == loc) {
                toFinish.pop_back();
                movingTowardsToFinish = false;
            }
            rc.completeTowerPattern(UnitType::LEVEL_ONE_DEFENSE_TOWER, loc);
            built = true;
        }
    }
    // Go to centre at the start
    while (!turnAdded.empty() && rc.getRoundNum() - turnAdded.back() > 80 &&
           !movingTowardsToFinish) {
        toFinish.pop_back();
        turnAdded.pop_back();
    }
    // Check for ruins
    dest = MapLocation::NONE;
    // Drain nearby paint
    for (const MapLocation& ruin : rc.senseNearbyRuins(-1)) {
        //if (!rc.senseRobotAtLocation(ruin).getLocation().isNull() && built) rc.setIndicatorString("bruh gimme paint");
        if (rc.senseRobotAtLocation(ruin).getLocation().isNull() &&
            rc.canSenseLocation(ruin.add(Direction::all[Direction::SOUTH]))) {
            if (dest.isNull() || rc.getLocation().distanceSquaredTo(ruin) <
                                     rc.getLocation().distanceSquaredTo(dest)) {
                dest = ruin;
                found = true;
            }
        } else if (ruin.isAdjacentTo(rc.getLocation()) && built) {
            RobotInfo tower = rc.senseRobotAtLocation(ruin);
            if (tower.getTeam() == rc.getTeam()) {
                // Steal as much paint as possible
                int steal = std::min(200 - rc.getPaint(), tower.getPaintAmount());
                if (rc.canTransferPaint(ruin, -steal)) rc.transferPaint(ruin, -steal);
            }
        }
    }
    if (!dest.isNull() && rc.getRoundNum() < 500) {
        bool giveUpOnRuin = false;
        for (int dx = -2; dx <= 2; dx++) {
            for (int dy = -2; dy <= 2; dy++) {
                if (dx == 0 && dy == 0) continue;
                MapLocation ml(dest.x + dx, dest.y + dy);
                if (!rc.canSenseLocation(ml)) continue;
                if (ml.x == rc.getLocation().x && ml.y == rc.getLocation().y)
                    continue;
                RobotInfo ri = rc.senseRobotAtLocation(ml);
                if (!ri.getLocation().isNull() && ri.getTeam() == rc.getTeam()) {
                    if (ri.getPaintAmount() < rc.getPaint() ||
                        (ri.getPaintAmount() == rc.getPaint() && ri.ID < rc.getID())) {
                        giveUpOnRuin = true;
                    }
                }
            }
        }
        for (int dx = -3; dx <= 3; dx++) {
            for (int dy = -3; dy <= 3; dy++) {
                if (dx == 0 && dy == 0) continue;
                MapLocation ml(dest.x + dx, dest.y + dy);
                if (!rc.canSenseLocation(ml)) continue;
                if (ml.x == rc.getLocation().x && ml.y == rc.getLocation().y)
                    continue;
                RobotInfo ri = rc.senseRobotAtLocation(ml);
                if (!ri.getLocation().isNull() && ri.getTeam() != rc.getTeam())
                    giveUpOnRuin = false;
            }
        }
        if (giveUpOnRuin) {
            if (destination.isNull() || rc.canSenseLocation(destination) ||
                rc.getRoundNum() % 40 == 32)
                destination = (rc.getID()) % 4 == 0
                                  ? MapLocation(RobotPlayer::rng.nextInt(rc.getMapWidth()),
                                                RobotPlayer::rng.nextInt(rc.getMapHeight()))
                                  : roles::Splasher::getNextCorner(rc);
            dest = destination;
        }
    }
    if (rc.getMoney() < 400 && movingTowardsToFinish) {
        movingTowardsToFinish = false;
        if (destination.isNull() || rc.canSenseLocation(destination) ||
            rc.getRoundNum() % 40 == 32)
            destination = (rc.getID()) % 4 == 0
                              ? MapLocation(RobotPlayer::rng.nextInt(rc.getMapWidth()),
                                            RobotPlayer::rng.nextInt(rc.getMapHeight()))
                              : roles::Splasher::getNextCorner(rc);
        dest = destination;
    }
    //if (rc.getPaint() < 40 && !toFinish.empty())
    //    movingTowardsToFinish = true;
    built = false;
    if (dest.isNull() || (!toFinish.empty() && dest.x == toFinish.back().x &&
                          dest.y == toFinish.back().y && !movingTowardsToFinish)) {
        if (destination.isNull() || rc.canSenseLocation(destination) ||
            rc.getRoundNum() % 40 == 32)
            destination = (rc.getID()) % 4 == 0
                              ? MapLocation(RobotPlayer::rng.nextInt(rc.getMapWidth()),
                                            RobotPlayer::rng.nextInt(rc.getMapHeight()))
                              : roles::Splasher::getNextCorner(rc);
        dest = destination;
    }
    if (movingTowardsToFinish)
        dest = toFinish.back();
    if (movingTowardsToFinish) {
        if (rc.canSenseLocation(dest)) {
            if (!rc.senseRobotAtLocation(dest).getLocation().isNull()) {
                toFinish.pop_back();
                turnAdded.pop_back();
                movingTowardsToFinish = false;
            }
        }
    } else if (!toFinish.empty()) {
        bool keepGoing = true;
        for (int dx = -2; dx <= 2 && keepGoing; dx++) {
            for (int dy = -2; dy <= 2 && keepGoing; dy++) {
                if (dx == 0 && dy == 0)
                    continue;
                MapLocation loc(toFinish.back().x + dx, toFinish.back().y + dy);
                if (rc.canSenseLocation(loc) &&
                    rc.senseMapInfo(loc).getPaint() == PaintType::EMPTY) {
                    dest = toFinish.back();
                    toFinish.pop_back();
                    turnAdded.pop_back();
                    keepGoing = false;
                }
            }
        }
    }
    roles::Mopper::moveTowardsMindfully(rc, dest);
    rc.setIndicatorLine(rc.getLocation(), dest, 255, 0, 0);
    if (movingTowardsToFinish) {
        rc.setIndicatorLine(rc.getLocation(), dest, 120, 120, 120);
        if (rc.canSenseLocation(dest)) {
            if (!rc.senseRobotAtLocation(dest).getLocation().isNull()) {
                toFinish.pop_back();
                turnAdded.pop_back();
                movingTowardsToFinish = false;
            }
        }
    }
    // Try to paint the current location
    vector<MapInfo> marked;
    for (const MapInfo& map : rc.senseNearbyMapInfos())
        if (isAlly(map.getMark()) && isSecondary(map.getMark())) {
            if (rc.canSenseLocation(map.getMapLocation().add(Direction::all[Direction::NORTH])) &&
                !rc.senseMapInfo(map.getMapLocation().add(Direction::all[Direction::NORTH]))
                     .hasRuin()) {
                marked.push_back(map);
            }
            if (!rc.canSenseLocation(map.getMapLocation().add(Direction::all[Direction::NORTH]))) {
                // Hope and pray :skull:
                marked.push_back(map);
            }
        }
    bool col = false;
    for (const MapInfo& map : marked)
        if (rc.getLocation().isWithinDistanceSquared(map.getMapLocation(), 8)) {
            int dist = rc.getLocation().distanceSquaredTo(map.getMapLocation());
            if (dist == 0 || dist == 5 || dist == 8) col = true;
        }

    if (rc.senseMapInfo(rc.getLocation()).getPaint() == PaintType::EMPTY) {
        bool colour = col;
        if (rc.canSenseLocation(dest.add(Direction::all[Direction::SOUTH])) &&
            isAlly(rc.senseMapInfo(dest.add(Direction::all[Direction::SOUTH])).getMark())) {
            colour = true;
            bool money =
                isSecondary(rc.senseMapInfo(dest.add(Direction::all[Direction::SOUTH])).getMark());
            if (money) {
                int dist = dest.distanceSquaredTo(rc.getLocation());
                if (dist == 1 || dist == 8) colour = false;
            } else {
                colour = false;
                int dist = dest.distanceSquaredTo(rc.getLocation());
                if (dist == 2 || dist == 8) colour = true;
            }
        }
        if (rc.canAttack(rc.getLocation())) rc.attack(rc.getLocation(), colour);
    }

    // See if it needs to change direction
    /*
    if (rc.canSenseLocation(dest) && !found) {
        if ((rc.getID())%3 == 0) dest = MapLocation(RobotPlayer::rng.nextInt(rc.getMapWidth()), RobotPlayer::rng.nextInt(rc.getMapHeight()));
        else dest = Splasher::getNextCorner(rc);
    }
     */

    // Try to complete tower
    if (found && rc.canSenseLocation(dest) &&
        rc.canSenseLocation(dest.add(Direction::all[Direction::SOUTH])) &&
        rc.senseMapInfo(dest).hasRuin()) {
        if (!isAlly(rc.senseMapInfo(dest.add(Direction::all[Direction::SOUTH])).getMark())) {
            int r = RobotPlayer::rng.nextInt(2);
            if (rc.getNumberTowers() <= 4) {
                if (rc.canMark(dest.add(Direction::all[Direction::SOUTH]))) {
                    rc.mark(dest.add(Direction::all[Direction::SOUTH]), true);
                    halfBuilt = dest;
                }
            } else if (rc.getNumberTowers() <= 6) {
                if (rc.canMark(dest.add(Direction::all[Direction::SOUTH]))) {
                    rc.mark(dest.add(Direction::all[Direction::SOUTH]), false);
                    halfBuilt = dest;
                }
            } else if (r == 0 || rc.getMoney() > 5000) {
                if (rc.canMark(dest.add(Direction::all[Direction::SOUTH]))) {
                    rc.mark(dest.add(Direction::all[Direction::SOUTH]), false);
                    halfBuilt = dest;
                }
            } else {
                if (rc.canMark(dest.add(Direction::all[Direction::SOUTH]))) {
                    rc.mark(dest.add(Direction::all[Direction::SOUTH]), true);
                    halfBuilt = dest;
                }
            }
        }
        if (rc.isActionReady() &&
            isAlly(rc.senseMapInfo(dest.add(Direction::all[Direction::SOUTH])).getMark())) {
            bool money =
                isSecondary(rc.senseMapInfo(dest.add(Direction::all[Direction::SOUTH])).getMark());
            bool def = rc.getRoundNum() - RobotPlayer::lastSeenEnemy < 5 &&
                       rc.getRoundNum() > 2 * (rc.getMapWidth() + rc.getMapHeight());
            rc.setIndicatorDot(dest, 255, 0, 255);
            bool done = false;
            for (int dx = -2; !done && dx < 3; dx++) {
                for (int dy = -2; dy < 3; dy++) {
                    if (!rc.canSenseLocation(MapLocation(dest.x + dx, dest.y + dy)) ||
                        (dx == 0 && dy == 0))
                        continue;
                    MapInfo todo = rc.senseMapInfo(MapLocation(dest.x + dx, dest.y + dy));
                    if (isEnemy(todo.getPaint())) {
                        enemyPaintCell = MapLocation(dest.x + dx, dest.y + dy);
                        turnEnemyPaintCell = rc.getRoundNum();
                        continue;
                    }
                    if (!todo.hasRuin() && rc.canAttack(todo.getMapLocation()) &&
                        todo.getMapLocation().isWithinDistanceSquared(dest, 8)) {
                        if (!todo.hasRuin() && rc.canAttack(todo.getMapLocation()) &&
                            todo.getMapLocation().isWithinDistanceSquared(dest, 8)) {
                            bool colour = true;
                            if (def) {
                                colour = dest.distanceSquaredTo(todo.getMapLocation()) <= 4;
                            } else if (money) {
                                int dist = dest.distanceSquaredTo(todo.getMapLocation());
                                if (dist == 1 || dist == 8) colour = false;
                            } else {
                                colour = false;
                                int dist = dest.distanceSquaredTo(todo.getMapLocation());
                                if (dist == 2 || dist == 8) colour = true;
                            }
                            // Check that the pattern isn't done already
                            if (isAlly(todo.getPaint()) &&
                                isSecondary(todo.getPaint()) == colour)
                                continue;
                            if (rc.canAttack(todo.getMapLocation())) {
                                rc.attack(todo.getMapLocation(), colour);
                                turnsWasted = 0;
                                halfBuilt = dest;
                                //std::cout << "Hello halfBuilt " << halfBuilt.toString() << '\n';
                                done = true;
                                break;
                            }
                        }
                    }
                }
            }
            if (!enemyPaintCell.isNull()) {
                //std::cout << lastStuck << " " << turnsWasted << '\n';
                if (lastStuck == rc.getRoundNum() - 1)
                    turnsWasted++;
                else
                    turnsWasted = 1;
                lastStuck = rc.getRoundNum();
                if (turnsWasted == 3 && !toFinish.empty() && toFinish.back().x == dest.x &&
                    toFinish.back().y == dest.y) {
                    toFinish.pop_back();
                    turnAdded.pop_back();
                    movingTowardsToFinish = false;
                }
                if (turnsWasted == 3) {
                    std::cout << (wontBegForMore.isNull() ? string("null")
                                                          : wontBegForMore.toString())
                              << '\n';
                    for (const RobotInfo& ri : rc.senseNearbyRobots(dest, 8, rc.getTeam())) {
                        if (ri.type == UnitType::SOLDIER &&
                            (ri.getPaintAmount() < rc.getPaint() ||
                             (ri.getPaintAmount() == rc.getPaint() && ri.ID < rc.getID()))) {
                            wontBegForMore = dest;
                            return;
                        }
                    }
                    if (wontBegForMore != dest)
                        askForMopper = true;
                    wontBegForMore = dest;
                }
            } else if (rc.isActionReady()) {
                for (const RobotInfo& ri : rc.senseNearbyRobots(dest, 8, rc.getTeam())) {
                    if (ri.type == UnitType::SOLDIER &&
                        (ri.getPaintAmount() > rc.getPaint() ||
                         (ri.getPaintAmount() == rc.getPaint() && ri.ID < rc.getID()))) {
                        turnsWasted = 3;
                        lastStuck = rc.getRoundNum();
                        return;
                    }
                }
                if (toFinish.empty() || toFinish.back().x != dest.x ||
                    toFinish.back().y != dest.y) {
                    toFinish.push_back(dest);
                    turnAdded.push_back(rc.getRoundNum());
                }
            } else {
                turnsWasted = 0;
                enemyPaintCell = MapLocation::NONE;
            }
        }
    } else if (!toFinish.empty()) {
        enemyPaintCell = MapLocation::NONE;
        if (rc.getMoney() > moneyLastTurn &&
            (1000.0 - rc.getMoney()) / (rc.getMoney() - Soldier::moneyLastTurn) <
                1.3 * (max(abs(rc.getLocation().x - toFinish.back().x),
                           abs(rc.getLocation().y - toFinish.back().y)))) {
            movingTowardsToFinish = true;
            rc.setIndicatorString(
                "Moving towards finish " + toFinish.back().toString() + " now " +
                std::to_string((1000.0 - rc.getMoney()) /
                               (rc.getMoney() - Soldier::moneyLastTurn)) +
                " " +
                std::to_string(1.3 * (max(abs(rc.getLocation().x - toFinish.back().x),
                                          abs(rc.getLocation().y - toFinish.back().y)))));
        }
    }
}

}  // namespace SoldierState
}  // namespace philip_06
