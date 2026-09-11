#include "Utils/Attack.hpp"

#include "Roles/Rush.hpp"
#include "Utils/AdditionalClasses/Thrown.hpp"
#include "Utils/BugNavigator.hpp"
#include "Utils/Globals.hpp"
#include "Utils/Vision.hpp"

#include <algorithm>
#include <climits>
#include <cmath>
#include <iostream>

using std::min;

namespace Utils {

int Attack::holdingRounds = 0;
const int Attack::cheeseToUse[] = {0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 1, 2, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 2, 2, 0, 0
        , 0, 0, 0, 0, 1, 2, 2, 2, 2, 2, 0, 0, 0, 0, 1, 2,
    2, 2, 2, 2, 2, 2, 0, 0, 1, 2, 2, 2, 2, 2, 2, 2, 2,
    2, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2
        , 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
    2, 2, 2, 2, 2, 2, 2, 2};

bool Attack::containsDir(const vector<Direction>& arr, Direction dir) {
    for (const Direction& d : arr) {
        if (d == dir) return true;
    }
    return false;
}

vector<Direction> Attack::getSafeDirections() {
    vector<Direction> safeDirections;
    for (const Direction& attempt : Direction::DIRECTION_ORDER) {
        bool safe = true;
        MapLocation loc = rc.getLocation().add(attempt);
        if ((!rc.canMove(attempt) && !rc.canRemoveDirt(loc)) && !(attempt == Direction::CENTER))
            continue;
        bool multiple = false;
        for (AdditionalClasses::Thrown& uhoh : alliesThrown) {
            if (!uhoh.isSafe(loc)) {
                safe = false;
                break;
            }
        }
        if (!safe) continue;

        RobotInfo gangb;

        for (const RobotInfo& enemy : enemyRobots) {
            int dist = loc.distanceSquaredTo(enemy.location);
            if (dist > 8 || enemy.getType() == UnitType::RAT_KING ||
                !isNullRobot(getCarryingRobot(enemy)))
                continue;
            if (!Vision::isWithinVision(enemy.location, enemy.direction, loc,
                                        visionConeRadiusSquared(enemy.getType())))
                continue;

            if (rc.canCarryRat(enemy.location)) {
                if (multiple) {
                    safe = false;
                    break;
                }
                multiple = true;
            } else {
                if (dist <= 2) {
                    if (!isNullRobot(getCarryingRobot(enemy))) {
                        if (rc.isActionReady() &&
                            (rc.getHealth() > enemy.health ||
                             !isWithinVision(enemy.location, enemy.direction, loc,
                                             visionConeRadiusSquared(enemy.type)))) {
                            if (multiple) {
                                safe = false;
                                break;
                            }
                            multiple = true;
                            continue;
                        }
                        safe = false;
                        break;
                    }
                    if (enemy.health <= 12) {
                        if (multiple) {
                            safe = false;
                            break;
                        }
                        multiple = true;
                        continue;
                    }
                    if (dist == 2) {
                        if (multiple) {
                            safe = false;
                            break;
                        }
                        multiple = true;
                    } else if (dist == 1) {
                        MapLocation left = loc.add(loc.directionTo(enemy.location).rotateLeft().rotateLeft());
                        MapLocation right = loc.add(loc.directionTo(enemy.location).rotateRight().rotateRight());
                        if ((Vision::hasSeenLocation(left) && !Vision::isPassableWithDig(left)) && (Vision::hasSeenLocation(right) && !Vision::isPassableWithDig(right))) {
                            if (multiple) {
                                safe = false;
                                break;
                            }
                            multiple = true;
                        } else {
                            gangb = enemy;
                            if (multiple) {
                                safe = false;
                                break;
                            }
                            multiple = true;
                        }
                    }
                } else {
                    if (dist != 5 && !isNullRobot(getCarryingRobot(enemy))) {
                        safe = false;
                        break;
                    }
                    if (enemy.health - (rc.getLocation().isAdjacentTo(enemy.location) && rc.isActionReady() ? 12 : 0) > rc.getHealth()) {
                        safe = false;
                        break;
                    }
                    if (multiple) {
                        safe = false;
                        break;
                    } else {
                        multiple = true;
                    }
                }
            }
        }

        if (safe) {

            //check gb

            /*
            if (gangb != null) {
                for (RobotInfo ally: allyRobots) {
                    ...
                }
            }

             */

            if (isNullRobot(gangb)) {
                safeDirections.push_back(attempt);
                rc.setIndicatorDot(loc, 0, 0, 0);
            }
        }
    }
    return safeDirections;
}

bool Attack::canUseTrap() {
    return (rc.getRawCheese() >= 20 || (rc.getGlobalCheese() >= useTrapCheeseThreshold - rc.getRawCheese() * globalCheeseTrapSubstitute && rc.getCurrentRatCost() > 50)) && (int)enemyRobots.size() >= 2;
}

RobotInfo Attack::enemy;
int Attack::unknown = 0;

vector<MapLocation> Attack::blindSpot(RobotInfo bad) {
    MapLocation m = bad.getLocation();
    MapLocation m1 = MapLocation(m.x - 1, m.y + 1);
    MapLocation m2 = MapLocation(m.x, m.y + 1);
    MapLocation m3 = MapLocation(m.x + 1, m.y + 1);
    MapLocation m4 = MapLocation(m.x - 1, m.y);
    MapLocation m5 = MapLocation(m.x + 1, m.y);
    MapLocation m6 = MapLocation(m.x - 1, m.y - 1);
    MapLocation m7 = MapLocation(m.x, m.y - 1);
    MapLocation m8 = MapLocation(m.x + 1, m.y - 1);
    switch (bad.getDirection().e) {
        case Direction::NORTH: return vector<MapLocation>{m4, m5, m6, m7, m8};
        case Direction::NORTHEAST: return vector<MapLocation>{m1, m4, m6, m7, m8};
        case Direction::EAST: return vector<MapLocation>{m1, m2, m4, m6, m7};
        case Direction::SOUTHEAST: return vector<MapLocation>{m1, m2, m3, m4, m6};
        case Direction::SOUTH: return vector<MapLocation>{m1, m2, m3, m4, m5};
        case Direction::SOUTHWEST: return vector<MapLocation>{m1, m2, m3, m5, m8};
        case Direction::WEST: return vector<MapLocation>{m2, m3, m5, m7, m8};
        case Direction::NORTHWEST: return vector<MapLocation>{m3, m5, m6, m7, m8};
        default: return vector<MapLocation>{};
    }
}

RobotInfo Attack::lastKnown;
int Attack::lastRound = 0;

bool Attack::onevone() {
    if (!isNullRobot(rc.getCarrying()))
        gunner();
    if (isNullRobot(enemy) || unknown > 1) {
        // 1v1 the closest bot
        RobotInfo closest;
        for (const RobotInfo& bot : enemyRobots) if (bot.getLocation() != rc.getLocation()) {
            if (isNullRobot(closest) || rc.getLocation().distanceSquaredTo(closest.getLocation()) > rc.getLocation().distanceSquaredTo(bot.getLocation())) {
                closest = bot;
            }
        }
        if (!isNullRobot(closest) || unknown > 1) enemy = closest;
    }
    if (isNullRobot(enemy)) return false;

    // Fun part: try to 1v1 someone now
    if (!rc.canSenseRobot(enemy.ID)) {
        // cannot sense (NOT GOOD)
        // turn towards it's last known direction
        Direction dir = rc.getLocation().directionTo(enemy.getLocation());
        if (dir != rc.getDirection()) {
            if (rc.canTurn(dir)) Vision::turn(dir);
        } else {
            // either turn left or right
            Direction d = rc.getDirection();
            if (rc.canTurn()) {
                if (rng.nextInt(2) == 0) Vision::turn(d.rotateRight().rotateRight());
                else Vision::turn(d.rotateLeft().rotateLeft());
            }
        }
    }
    if (!rc.canSenseRobot(enemy.ID)) {
        unknown++;
        if (rc.canMoveForward()) rc.moveForward();
        if (unknown >= 3) enemy = RobotInfo();
        return true;
    }
    enemy = rc.senseRobot(enemy.ID);
    MapLocation enemyLoc = enemy.getLocation();

    // Try the dumb pickup sequence
    if (rc.canCarryRat(enemyLoc)) {
        rc.carryRat(enemyLoc);
        if (enemyRobots.size() == 1 && rc.canMove(rc.getDirection().opposite())) rc.move(rc.getDirection().opposite());
        return true;
    }

    // If we have more HP, pick it up
    if (rc.getHealth() > enemy.getHealth() && rc.isActionReady() && rc.isMovementReady() && isNullRobot(rc.getCarrying())) {
        Direction dir = rc.getLocation().directionTo(enemy.getLocation());
        MapLocation dest = rc.getLocation().add(dir);
        if (dest.isAdjacentTo(enemyLoc) && rc.canMove(dir) && dest != enemyLoc && rc.canSenseRobotAtLocation(enemyLoc)) {
            rc.move(dir);
            rc.carryRat(enemyLoc);
            return true;
        }
    }

    // Try move into blind spot + pick up combo
    if (rc.isMovementReady() && rc.isTurningReady() && rc.isActionReady() && isNullRobot(rc.getCarrying())) {
        for (const MapLocation& m : blindSpot(enemy)) if (rc.getLocation().isAdjacentTo(m)) {
            // ez combo ggs
            if (!rc.canMove(rc.getLocation().directionTo(m))) continue;
            rc.move(rc.getLocation().directionTo(m));
            if (!rc.canSenseRobot(enemy.ID)) Vision::turn(rc.getLocation().directionTo(enemy.getLocation()));
            if (rc.canSenseRobot(enemy.ID) && rc.canCarryRat(enemy.getLocation())) {
                rc.carryRat(enemy.getLocation());
                return true;
            }
        }
    }

    // Move into their blind spot haha if they are strafing
    if (rc.getRoundNum() - lastRound == 1 && isNullRobot(rc.getCarrying())) {
        // check for strafing conditions
        if (enemyLoc != lastKnown.getLocation() && enemy.getID() == lastKnown.getID() && rc.isMovementReady() && rc.isTurningReady()) {
            // direction of movement
            Direction dir = lastKnown.getLocation().directionTo(enemyLoc);
            if (dir != enemy.getDirection() && dir != lastKnown.getDirection()) {
                rc.setIndicatorString("THEY STRAFED!!");
                // they strafed ggs ez W
                // if we face them front on we just win
                MapLocation m1 = MapLocation(enemyLoc.x, enemyLoc.y + 1);
                MapLocation m2 = MapLocation(enemyLoc.x, enemyLoc.y - 1);
                MapLocation m3 = MapLocation(enemyLoc.x + 1, enemyLoc.y);
                MapLocation m4 = MapLocation(enemyLoc.x - 1, enemyLoc.y);
                for (const MapLocation& attempt : vector<MapLocation>{m1, m2, m3, m4}) if (rc.getLocation().isAdjacentTo(attempt)) {
                    Direction dirr = rc.getLocation().directionTo(attempt);
                    if (!isWithinVision(attempt, dirr, enemyLoc, 2)) continue;
                    if (!rc.canMove(rc.getLocation().directionTo(attempt))) continue;
                    if (dirr != rc.getDirection()) Vision::turn(dirr);
                    rc.move(rc.getLocation().directionTo(attempt));
                    if (rc.canCarryRat(enemyLoc)) {
                        rc.carryRat(enemyLoc);
                    } else {
                        std::cout << "did not work?!?! why did i not pick up" << '\n';
                    }
                }
            }
        }
    }


    if (rc.canAttack(enemyLoc)) {
        // check how much to attack with
        if (rc.getHealth() > enemy.getHealth()) {
            std::cout << "WHY DID I NOT PICK UP??" << '\n';
        }
        int diff = enemy.getHealth() - rc.getHealth();
        if (diff <= 11) {
            rc.attack(enemy.getLocation(), 2);
        } else if (diff == 12 || diff == 13) {
            // we need a lot to come back
            rc.attack(enemy.getLocation(), 5);
        } else if (diff > 30 && rc.isActionReady() && rc.isMovementReady()) {
            // place a trap and move backwards
            if (rc.canMove(rc.getDirection().opposite())) {
                rc.move(rc.getDirection().opposite());
                rc.placeRatTrap(rc.getLocation().add(rc.getDirection()));
            }
        } else {
            rc.attack(enemyLoc);
        }
        // NEVER BACK DOWN (strafing is nearly a guaranteed loss)
        // step back once in a while
        if (rc.isMovementReady() && rng.nextInt(3) == 0 && rc.getLocation().distanceSquaredTo(enemyLoc) == 2) {
            if (rc.canMove(rc.getDirection().opposite())) rc.move(rc.getDirection().opposite());
        }
    }
    // never move towards them if you need to strafe
    MapLocation next = rc.getLocation().add(rc.getDirection());
    if (next.distanceSquaredTo(enemyLoc) >= 2 && rc.getLocation().distanceSquaredTo(enemyLoc) > next.distanceSquaredTo(enemyLoc)) {
        // moves us closer
        if (rc.canMoveForward()) rc.moveForward();
    } else if (rc.getLocation().distanceSquaredTo(enemyLoc) >= 9 && rc.isMovementReady()) {
        // turn and move closer
        Direction dir = rc.getLocation().directionTo(enemyLoc);
        if (rc.canTurn()) Vision::turn(dir);
        if (rc.canMoveForward()) rc.moveForward();
    }

    // Turn to face the enemy
    if (rc.canTurn()) {
        Direction dir = rc.getLocation().directionTo(enemyLoc);
        if (dir != rc.getDirection() && dir != Direction::CENTER) Vision::turn(dir);
    }
    if (rc.canAttack(enemyLoc)) {
        // check how much to attack with
        if (rc.getHealth() > enemy.getHealth()) {
            std::cout << "WHY DID I NOT PICK UP??" << '\n';
        }
        int diff = enemy.getHealth() - rc.getHealth();
        if (diff <= 12) {
            rc.attack(enemy.getLocation(), 2);
        } else if (diff == 13) {
            // we need a lot to come back
            rc.attack(enemy.getLocation(), 5);
        } else if (diff > 30 && rc.isActionReady() && rc.isMovementReady() && rc.canMove(rc.getDirection().opposite())) {
            // place a trap and move backwards
            rc.move(rc.getDirection().opposite());
            rc.placeRatTrap(rc.getLocation().add(rc.getDirection()));
        } else {
            rc.attack(enemyLoc);
        }
        // NEVER BACK DOWN (strafing is nearly a guaranteed loss)
        // step back once in a while
        if (rc.isMovementReady() && rng.nextInt(3) == 0 && rc.getLocation().distanceSquaredTo(enemyLoc) == 2) {
            if (rc.canMove(rc.getDirection().opposite())) rc.move(rc.getDirection().opposite());
        }
    }

    // ggs we won
    if (!isNullRobot(rc.getCarrying()) && rc.getCarrying().ID == enemy.ID) enemy = RobotInfo();

    if (!isNullRobot(enemy) && rc.canSenseRobot(enemy.getID())) lastKnown = enemy;
    else lastKnown = enemy;
    if (!isNullRobot(lastKnown)) lastRound = rc.getRoundNum();

    return true;
}

vector<Direction> Attack::getInvisDirections() {
    vector<Direction> safeDirections;
    for (const Direction& attempt : Direction::DIRECTION_ORDER) {
        bool invis = true;
        MapLocation loc = rc.getLocation().add(attempt);
        if (!rc.canMove(attempt) && !rc.canRemoveDirt(loc))
            continue;
        for (const RobotInfo& enemy : enemyRobots) {
            if (enemy.getType() == UnitType::RAT_KING || !isNullRobot(getCarryingRobot(enemy))) continue;
            if (!Vision::isWithinVision(enemy.location, enemy.direction, loc,
                                        visionConeRadiusSquared(enemy.getType())))
                continue;
            invis = false;
            break;
        }
        if (invis) {
            safeDirections.push_back(attempt);
            rc.setIndicatorDot(loc, 0, 0, 0);
        }
    }
    return safeDirections;
}

bool Attack::trapType(UnitType type) {
    if (!rc.isActionReady()) return false;
    if (rc.getRawCheese() < 5) return false;
    if (rc.getGlobalCheese() - 5 < trapGlobalCheeseThreshold) return false;

    // TS UNFINISHED /////////////////////////////////

    // find attackable robot of type
    for (const RobotInfo& nearbyRobot : enemyRobots) {
        if (nearbyRobot.getType() == type) {
            // build a trap next to them if I can: CAT
            if (type == UnitType::CAT) {
                // loop through directions starting from a random one
                int st = rng.nextInt(8);
                for (int i = 0; i < 8; i++) {
                    MapLocation adjLoc = nearbyRobot.getLocation().add(directions[(st + i) % 8]);
                    if (rc.canPlaceCatTrap(adjLoc)) {
                        rc.placeCatTrap(adjLoc);
                        return true;
                    }
                }
            }
            // build a trap next to them if I can: RAT
            else {
                if (rc.canPlaceRatTrap(nearbyRobot.getLocation())) {
                    rc.placeRatTrap(nearbyRobot.getLocation());
                    return true;
                }
            }
        }
    }
    return false;
}

bool Attack::trapKing() {
    return trapType(UnitType::RAT_KING);
}

bool Attack::trapBaby() {
    return trapType(UnitType::BABY_RAT);
}

bool Attack::trapCat() {
    return trapType(UnitType::CAT);
}

bool Attack::canPickUp(MapLocation pos, RobotInfo enemy) {
    if (!rc.isActionReady()) return false;
    if (!isNullRobot(rc.getCarrying())) return false;
    int d = pos.distanceSquaredTo(enemy.location);
    if (d > 2) return false;
    if (rc.getHealth() > enemy.health) return true;
    Direction d1 = enemy.location.directionTo(pos);
    Direction d2 = enemy.direction;
    return d1.dx * d2.dx + d1.dy * d2.dy <= 0;
}

Direction Attack::bestThrowingDirection() {
    Direction best = DIR_NULL;
    int bestDis = INT_MAX;
    for (const RobotInfo& info : rc.senseNearbyRobots(-1)) {
        if (info.type == UnitType::RAT_KING && info.getTeam() == opponent(rc.getTeam())) { best = rc.getLocation().directionTo(info.location); break; }
        if (info.getTeam() == rc.getTeam()) continue;
        int dx = info.location.x - rc.getLocation().x;
        int dy = info.location.y - rc.getLocation().y;
        if (dx == 0 && bestDis > std::abs(dy)) {
            bestDis = std::abs(dy);
            best = rc.getLocation().directionTo(info.location);
        } else if (dy == 0 && bestDis > std::abs(dx)) {
            bestDis = std::abs(dx);
            best = rc.getLocation().directionTo(info.location);
        } else if (std::abs(dx) == std::abs(dy) && bestDis > std::abs(dx)) {
            bestDis = std::abs(dx);
            best = rc.getLocation().directionTo(info.location);
        }
    }
    if (best != DIR_NULL)
        return best;
    for (const RobotInfo& info : rc.senseNearbyRobots(-1, Team::NEUTRAL)) {
        int dx = info.location.x - rc.getLocation().x;
        int dy = info.location.y - rc.getLocation().y;
        if (dx == 0 && bestDis > std::abs(dy)) {
            bestDis = std::abs(dy);
            best = rc.getLocation().directionTo(info.location);
        } else if (dy == 0 && bestDis > std::abs(dx)) {
            bestDis = std::abs(dx);
            best = rc.getLocation().directionTo(info.location);
        } else if (std::abs(dx) == std::abs(dy) && bestDis > std::abs(dx)) {
            bestDis = std::abs(dx);
            best = rc.getLocation().directionTo(info.location);
        }
    }
    if (best != DIR_NULL)
        return best;

    return rc.getLocation().directionTo(Roles::Rush::rush);
}


Direction Attack::newBestThrowingDirection(RobotInfo enemy) {
    Direction best = DIR_NULL;
    int score = 0;
    for (const Direction& dir : Direction::allDirections()) {
        if (dir == Direction::CENTER)
            continue;
        MapLocation x = rc.getLocation();
        for (int i = 0; i < 8; i++) {
            x = x.add(dir);
            if (!rc.onTheMap(x)) {
                if (score <= 28 - i * 4) {
                    score = 28 - i * 4;
                    best = dir;
                }
                break;
            }
            if (!rc.canSenseLocation(x))
                break;
            MapInfo info = rc.senseMapInfo(x);
            if (!info.isPassable()) {
                if (info.isWall()) {
                    if (score <= min(enemy.health, 28 - i * 4)) {
                        score = min(enemy.health, 28 - i * 4);
                        best = dir;
                    }
                } else if (info.isDirt()) {
                    if (score <= min(enemy.health, 28 - i * 4)) {
                        score = min(enemy.health, 28 - i * 4);
                        best = dir;
                    }
                }
                break;
            } else if (rc.isLocationOccupied(x)) {
                RobotInfo bot = rc.senseRobotAtLocation(x);
                if (bot.team == rc.getTeam() && score <= min(enemy.health, 28 - i * 4) - min(bot.health, 28 - i * 4)) {
                    score = min(enemy.health, 28 - i * 4) - min(bot.health, 28 - i * 4);
                    best = dir;
                } else if (bot.team == opponent(rc.getTeam()) && score <= min(enemy.health, 28 - i * 4) + min(bot.health, 28 - i * 4)) {
                    score = min(enemy.health, 28 - i * 4) + min(bot.health, 28 - i * 4);
                    best = dir;
                } else if (bot.team == Team::NEUTRAL && score <= enemy.health) {
                    score = enemy.health;
                    best = dir;
                }
            }
        }
    }

    return best;

}

int Attack::damageToCheese(int dam) {
    if (dam <= 10)
        return 0;
    return (dam - 11) * (dam - 11) + 1;
}

void Attack::catMicro() {
    for (const RobotInfo& cat : catRobots) {
        Vision::turn(rc.getLocation().directionTo(cat.location));
        if (rc.canPlaceCatTrap(cat.location.add(cat.location.directionTo(rc.getLocation())))) {
            rc.placeCatTrap(cat.location.add(cat.location.directionTo(rc.getLocation())));
            if (rc.canMove(cat.location.directionTo(rc.getLocation())) && cat.location.distanceSquaredTo(rc.getLocation()) <= 8)
                rc.move(cat.location.directionTo(rc.getLocation()));
        }
        if (rc.canAttack(cat.location)) {
            rc.attack(cat.location);
        }
    }

}

bool Attack::scratch() {
    if (!rc.isActionReady()) return false;
    RobotInfo target;
    for (int i = 0; i < (int)enemyRobots.size(); i++) {
        if (rc.canAttack(enemyRobots[i].location) && (isNullRobot(target) || target.health < enemyRobots[i].health)) {
            target = enemyRobots[i];
        }
    }
    if (isNullRobot(target)) return false;
    if (target.health <= 13) {
        //TODO: ANSON CHECK THIS (TRY TO 1 SHOT THEM)
        if (rc.canAttack(target.location, cheeseToUse[target.health])) {
            rc.attack(target.location, cheeseToUse[target.health]);
            enemyRobots = rc.senseNearbyRobots(-1, opponentTeam);
            target = RobotInfo();
            for (const RobotInfo& info : enemyRobots) {
                if (Vision::hasSeenLocation(info.location) && !Vision::canReach(info.location)) continue;
                else if (isNullRobot(target) || rc.getLocation().distanceSquaredTo(info.location) < rc.getLocation().distanceSquaredTo(target.location) || (info.health < target.health && rc.getLocation().distanceSquaredTo(info.location) <= rc.getLocation().distanceSquaredTo(target.location))) {
                    target = info;
                }
            }
        } else
            rc.attack(target.location);
    } else if (target.health > rc.getHealth() && target.health - rc.getHealth() <= 13) {
        if (rc.canAttack(target.location, min(2, damageToCheese(target.health - rc.getHealth()))))
            rc.attack(target.location, min(2, damageToCheese(target.health - rc.getHealth())));
        else
            rc.attack(target.location);
    } else {
        if (rc.canAttack(target.location, 2))
            rc.attack(target.location, 2);
        else
            rc.attack(target.location);
    }
    return true;
}

int Attack::steps(MapLocation start, MapLocation end) {
    return std::max(std::abs(start.x - end.x), std::abs(start.y - end.y));
}

// micro for traps
void Attack::trapMicro() {
    if (!canUseTrap() || (int)newestSqueaks.size() >= (int)enemyRobots.size() + 1) return;
    // ok we are in danger, we want to place traps
    // (don't waste traps) only place adjacent to enemy
    MapLocation bestTrap;
    int score = 0;
    for (const Direction& dir : directions) if (rc.canPlaceRatTrap(rc.getLocation().add(dir))) {
        MapLocation cand = rc.getLocation().add(dir);
        int sscore = 0;
        for (const Direction& dir2 : directions) if (rc.canSenseRobotAtLocation(cand.add(dir2))) {
            RobotInfo poss = rc.senseRobotAtLocation(cand.add(dir2));
            if (poss.getTeam() == opponentTeam) {
                if (poss.getHealth() > 50) sscore += 3;
                else sscore += 2;
            }
        }
        if (sscore > score) {
            score = sscore;
            bestTrap = cand;
        }
    }
    if (!bestTrap.isNull() && rc.canPlaceRatTrap(bestTrap)) rc.placeRatTrap(bestTrap);
}

bool Attack::retreat() {

    if (rc.canCarryRat(closestEnemy.location)) {
        rc.carryRat(closestEnemy.location);
        enemyRobots = rc.senseNearbyRobots(-1, opponentTeam);
        closestEnemy = RobotInfo();
        for (const RobotInfo& info : enemyRobots) {
            if (Vision::hasSeenLocation(info.location) && !Vision::canReach(info.location)) continue;
            else if (isNullRobot(closestEnemy) || rc.getLocation().distanceSquaredTo(info.location) < rc.getLocation().distanceSquaredTo(closestEnemy.location) || (info.health < closestEnemy.health && rc.getLocation().distanceSquaredTo(info.location) <= rc.getLocation().distanceSquaredTo(closestEnemy.location))) {
                closestEnemy = info;
            }
        }
        if (isNullRobot(closestEnemy)) return false;
    }
    trapMicro();
    scratch();
    int minDis = 1000;
    Direction bestDir = Direction::CENTER;
    for (int i = 0; i < 8; i++) {
        if (!rc.canMove(adjacentDirections[i])) continue;
        int minD = 1000;
        for (const RobotInfo& enemy : enemyRobots) {
            minD = min(minD, rc.getLocation().add(adjacentDirections[i]).distanceSquaredTo(enemy.location));
        }
        if (minD < minDis) {
            minDis = minD;
            bestDir = adjacentDirections[i];
        }
    }
    if (bestDir != Direction::CENTER && rc.canMove(bestDir)) rc.move(bestDir);
    scratch();
    return true;
}

// return true if actually attacked
bool Attack::holdLine() {
    vector<Direction> safeDirections = getSafeDirections();
    vector<Direction> invisDirections = getInvisDirections();
    RobotInfo helping;
    for (const RobotInfo& ally : rc.senseNearbyRobots(-1, rc.getTeam())) {
        if (ally.location.distanceSquaredTo(closestEnemy.location) <= rc.getLocation().distanceSquaredTo(closestEnemy.location) || (!isNullRobot(helping) && ally.location.distanceSquaredTo(closestEnemy.location) <= helping.location.distanceSquaredTo(closestEnemy.location))) {
            helping = ally;
        }
    }
    //attempt kidnap
    if (rc.canCarryRat(closestEnemy.location)) {
        rc.carryRat(closestEnemy.location);
        enemyRobots = rc.senseNearbyRobots(-1, opponentTeam);
        closestEnemy = RobotInfo();
        for (const RobotInfo& info : enemyRobots) {
            if (Vision::hasSeenLocation(info.location) && !Vision::canReach(info.location)) continue;
            else if (isNullRobot(closestEnemy) || rc.getLocation().distanceSquaredTo(info.location) < rc.getLocation().distanceSquaredTo(closestEnemy.location) || (info.health < closestEnemy.health && rc.getLocation().distanceSquaredTo(info.location) <= rc.getLocation().distanceSquaredTo(closestEnemy.location))) {
                closestEnemy = info;
            }
        }
        if (isNullRobot(closestEnemy)) return false;
    }
    if (rc.isActionReady() && isNullRobot(rc.getCarrying())) {
        for (const RobotInfo& enemy : enemyRobots) {
            if (enemy.location.distanceSquaredTo(rc.getLocation()) >= 9) continue;
            for (const Direction& dir : invisDirections) {
                if (canPickUp(rc.getLocation().add(dir), enemy)) {
                    //rc.setIndicatorDot(rc.getLocation().add(dir),255,255,255);
                    if (isWithinVision(rc.getLocation().add(dir), rc.getDirection(), enemy.location, visionConeRadiusSquared(enemy.getType()))) {

                    } else if (rc.canTurn() && isWithinVision(rc.getLocation().add(dir), dir, enemy.location, visionConeRadiusSquared(enemy.getType()))) {
                        Vision::turn(dir);
                    }
                    if (rc.canMove(dir)) {
                        if (dir != Direction::CENTER)
                            rc.move(dir);
                        if (rc.canCarryRat(enemy.location)) {
                            rc.carryRat(enemy.location);
                            enemyRobots = rc.senseNearbyRobots(-1, opponentTeam);
                            closestEnemy = RobotInfo();
                            for (const RobotInfo& info : enemyRobots) {
                                if (Vision::hasSeenLocation(info.location) && !Vision::canReach(info.location))
                                    continue;
                                else if (isNullRobot(closestEnemy) || rc.getLocation().distanceSquaredTo(info.location) < rc.getLocation().distanceSquaredTo(closestEnemy.location) || (info.health < closestEnemy.health && rc.getLocation().distanceSquaredTo(info.location) <= rc.getLocation().distanceSquaredTo(closestEnemy.location))) {
                                    closestEnemy = info;
                                }
                            }
                            if (isNullRobot(closestEnemy)) return false;
                        } else if (canPickUp(rc.getLocation(), enemy) && rc.canTurn(rc.getLocation().directionTo(enemy.location))) {
                            Vision::turn(rc.getLocation().directionTo(enemy.location));
                            if (rc.canCarryRat(enemy.location)) {
                                rc.carryRat(enemy.location);
                                enemyRobots = rc.senseNearbyRobots(-1, opponentTeam);
                                closestEnemy = RobotInfo();
                                for (const RobotInfo& info : enemyRobots) {
                                    if (Vision::hasSeenLocation(info.location) && !Vision::canReach(info.location))
                                        continue;
                                    else if (isNullRobot(closestEnemy) || rc.getLocation().distanceSquaredTo(info.location) < rc.getLocation().distanceSquaredTo(closestEnemy.location) || (info.health < closestEnemy.health && rc.getLocation().distanceSquaredTo(info.location) <= rc.getLocation().distanceSquaredTo(closestEnemy.location))) {
                                        closestEnemy = info;
                                    }
                                }
                            }
                            if (isNullRobot(closestEnemy)) return false;
                        }
                    }

                }
            }
        }
    }


    if (rc.isActionReady() && isNullRobot(rc.getCarrying())) {
        for (const RobotInfo& enemy : enemyRobots) {
            if (enemy.location.distanceSquaredTo(rc.getLocation()) >= 9) continue;
            for (const Direction& dir : safeDirections) {
                if (canPickUp(rc.getLocation().add(dir), enemy)) {
                    //rc.setIndicatorDot(rc.getLocation().add(dir),255,255,255);
                    if (isWithinVision(rc.getLocation().add(dir), rc.getDirection(), enemy.location, visionConeRadiusSquared(enemy.getType()))) {

                    } else if (rc.canTurn() && isWithinVision(rc.getLocation().add(dir), dir, enemy.location, visionConeRadiusSquared(enemy.getType()))) {
                        Vision::turn(dir);
                    }
                    if (rc.canMove(dir)) {
                        if (dir != Direction::CENTER)
                            rc.move(dir);
                        if (rc.canCarryRat(enemy.location)) {
                            rc.carryRat(enemy.location);
                            enemyRobots = rc.senseNearbyRobots(-1, opponentTeam);
                            closestEnemy = RobotInfo();
                            for (const RobotInfo& info : enemyRobots) {
                                if (Vision::hasSeenLocation(info.location) && !Vision::canReach(info.location))
                                    continue;
                                else if (isNullRobot(closestEnemy) || rc.getLocation().distanceSquaredTo(info.location) < rc.getLocation().distanceSquaredTo(closestEnemy.location) || (info.health < closestEnemy.health && rc.getLocation().distanceSquaredTo(info.location) <= rc.getLocation().distanceSquaredTo(closestEnemy.location))) {
                                    closestEnemy = info;
                                }
                            }
                            if (isNullRobot(closestEnemy)) return false;
                        } else if (canPickUp(rc.getLocation(), enemy) && rc.canTurn(rc.getLocation().directionTo(enemy.location))) {
                            Vision::turn(rc.getLocation().directionTo(enemy.location));
                            if (rc.canCarryRat(enemy.location)) {
                                rc.carryRat(enemy.location);
                                enemyRobots = rc.senseNearbyRobots(-1, opponentTeam);
                                closestEnemy = RobotInfo();
                                for (const RobotInfo& info : enemyRobots) {
                                    if (Vision::hasSeenLocation(info.location) && !Vision::canReach(info.location))
                                        continue;
                                    else if (isNullRobot(closestEnemy) || rc.getLocation().distanceSquaredTo(info.location) < rc.getLocation().distanceSquaredTo(closestEnemy.location) || (info.health < closestEnemy.health && rc.getLocation().distanceSquaredTo(info.location) <= rc.getLocation().distanceSquaredTo(closestEnemy.location))) {
                                        closestEnemy = info;
                                    }
                                }
                                if (isNullRobot(closestEnemy)) return false;
                            }
                        }
                    }
                }
            }
        }
    }


    if (isNullRobot(closestEnemy)) return false;
    if (rc.canMove(rc.getLocation().directionTo(closestEnemy.location))) {
        if (containsDir(invisDirections, rc.getLocation().directionTo(closestEnemy.location))) {
            if (rc.getLocation().add(rc.getLocation().directionTo(closestEnemy.location)).directionTo(closestEnemy.location) == rc.getLocation().directionTo(closestEnemy.location) && rc.canTurn()) {
                Vision::turn(rc.getLocation().directionTo(closestEnemy.location));
            }
            rc.move(rc.getLocation().directionTo(closestEnemy.location));
        } else if (rc.canMove(rc.getLocation().directionTo(closestEnemy.location).rotateLeft()) && containsDir(invisDirections, rc.getLocation().directionTo(closestEnemy.location).rotateLeft())) {
            if (rc.getLocation().add(rc.getLocation().directionTo(closestEnemy.location).rotateLeft()).directionTo(closestEnemy.location) == rc.getLocation().directionTo(closestEnemy.location).rotateLeft() && rc.canTurn()) {
                Vision::turn(rc.getLocation().directionTo(closestEnemy.location).rotateLeft());
            }
            rc.move(rc.getLocation().directionTo(closestEnemy.location).rotateLeft());
        } else if (rc.canMove(rc.getLocation().directionTo(closestEnemy.location).rotateRight()) && containsDir(invisDirections, rc.getLocation().directionTo(closestEnemy.location).rotateRight())) {
            if (rc.getLocation().add(rc.getLocation().directionTo(closestEnemy.location).rotateRight()).directionTo(closestEnemy.location) == rc.getLocation().directionTo(closestEnemy.location).rotateRight() && rc.canTurn()) {
                Vision::turn(rc.getLocation().directionTo(closestEnemy.location).rotateRight());
            }
            rc.move(rc.getLocation().directionTo(closestEnemy.location).rotateRight());
        } else if (containsDir(safeDirections, rc.getLocation().directionTo(closestEnemy.location)) && steps(rc.getLocation().add(rc.getLocation().directionTo(closestEnemy.location)), closestEnemy.location) % 2 == 0) {
            if (rc.getLocation().add(rc.getLocation().directionTo(closestEnemy.location)).directionTo(closestEnemy.location) == rc.getLocation().directionTo(closestEnemy.location) && rc.canTurn()) {
                Vision::turn(rc.getLocation().directionTo(closestEnemy.location));
            }
            rc.move(rc.getLocation().directionTo(closestEnemy.location));
        } else if (rc.canMove(rc.getLocation().directionTo(closestEnemy.location).rotateRight()) && containsDir(safeDirections, rc.getLocation().directionTo(closestEnemy.location).rotateRight()) && steps(rc.getLocation().add(rc.getLocation().directionTo(closestEnemy.location).rotateRight()), closestEnemy.location) % 2 == 0) {
            if (rc.getLocation().add(rc.getLocation().directionTo(closestEnemy.location).rotateRight()).directionTo(closestEnemy.location) == rc.getLocation().directionTo(closestEnemy.location).rotateRight() && rc.canTurn()) {
                Vision::turn(rc.getLocation().directionTo(closestEnemy.location).rotateRight());
            }
            rc.move(rc.getLocation().directionTo(closestEnemy.location).rotateRight());
        } else if (rc.canMove(rc.getLocation().directionTo(closestEnemy.location).rotateLeft()) && containsDir(safeDirections, rc.getLocation().directionTo(closestEnemy.location).rotateLeft()) && steps(rc.getLocation().add(rc.getLocation().directionTo(closestEnemy.location).rotateLeft()), closestEnemy.location) % 2 == 0) {
            if (rc.getLocation().add(rc.getLocation().directionTo(closestEnemy.location).rotateLeft()).directionTo(closestEnemy.location) == rc.getLocation().directionTo(closestEnemy.location).rotateLeft() && rc.canTurn()) {
                Vision::turn(rc.getLocation().directionTo(closestEnemy.location).rotateLeft());
            }
            rc.move(rc.getLocation().directionTo(closestEnemy.location).rotateLeft());
        }
    } else if (rc.getLocation().distanceSquaredTo(closestEnemy.location) > 15)
        BugNavigator::moveTo(closestEnemy.location, true);

    if (canUseTrap()) trapMicro();

    if (rc.isMovementReady()) {
        for (const Direction& dir : invisDirections) {
            if (rc.canMove(dir) && dir != Direction::CENTER && 15 >= rc.getLocation().add(dir).distanceSquaredTo(closestEnemy.location)) {
                scratch();
                rc.move(dir);
                scratch();
                break;
            }
        }
    }
    if (rc.isMovementReady()) {
        for (const Direction& dir : safeDirections) {
            if (rc.canMove(dir)) {
                if (!canUseTrap()) {
                    scratch();
                }
                if (dir == Direction::CENTER)
                    break;
                rc.move(dir);
                scratch();
                break;
            }
        }
    }
    if (rc.isMovementReady() && rc.getHealth() < closestEnemy.health && rc.getLocation().distanceSquaredTo(closestEnemy.location) <= 8) {
        if (rc.canMove(closestEnemy.location.directionTo(rc.getLocation()))) {
            if (!canUseTrap()) {
                scratch();
                if (isNullRobot(closestEnemy)) return false;
            }
            rc.move(closestEnemy.location.directionTo(rc.getLocation()));
            scratch();
        } else if (rc.canMove(closestEnemy.location.directionTo(rc.getLocation()).rotateLeft())) {
            if (!canUseTrap()) {
                scratch();
                if (isNullRobot(closestEnemy)) return false;
            }
            rc.move(closestEnemy.location.directionTo(rc.getLocation()).rotateLeft());
            scratch();
        } else if (rc.canMove(closestEnemy.location.directionTo(rc.getLocation()).rotateRight())) {
            if (!canUseTrap()) {
                scratch();
                if (isNullRobot(closestEnemy)) return false;
            }
            rc.move(closestEnemy.location.directionTo(rc.getLocation()).rotateRight());
            scratch();
            if (isNullRobot(closestEnemy)) return false;
        }
    }
    if (isNullRobot(closestEnemy)) return false;
    if (rc.canTurn(rc.getLocation().directionTo(closestEnemy.location)))
        Vision::turn(rc.getLocation().directionTo(closestEnemy.location));
    scratch();

    return true;
}

bool Attack::moveIn() {
    vector<Direction> invisDirections = getInvisDirections();
    RobotInfo helping;
    for (const RobotInfo& ally : rc.senseNearbyRobots(-1, rc.getTeam())) {
        if (ally.location.distanceSquaredTo(closestEnemy.location) <= rc.getLocation().distanceSquaredTo(closestEnemy.location) || (!isNullRobot(helping) && ally.location.distanceSquaredTo(closestEnemy.location) <= helping.location.distanceSquaredTo(closestEnemy.location))) {
            helping = ally;
        }
    }
    //attempt kidnap
    if (rc.canCarryRat(closestEnemy.location)) {
        rc.carryRat(closestEnemy.location);
        enemyRobots = rc.senseNearbyRobots(-1, opponentTeam);
        closestEnemy = RobotInfo();
        for (const RobotInfo& info : enemyRobots) {
            if (Vision::hasSeenLocation(info.location) && !Vision::canReach(info.location)) continue;
            else if (isNullRobot(closestEnemy) || rc.getLocation().distanceSquaredTo(info.location) < rc.getLocation().distanceSquaredTo(closestEnemy.location) || (info.health < closestEnemy.health && rc.getLocation().distanceSquaredTo(info.location) <= rc.getLocation().distanceSquaredTo(closestEnemy.location))) {
                closestEnemy = info;
            }
        }
        if (isNullRobot(closestEnemy)) return false;
    }


    if (rc.isActionReady() && isNullRobot(rc.getCarrying())) {
        for (const RobotInfo& enemy : enemyRobots) {
            if (enemy.location.distanceSquaredTo(rc.getLocation()) >= 9) continue;
            for (const Direction& dir : invisDirections) {
                if (canPickUp(rc.getLocation().add(dir), enemy)) {
                    //rc.setIndicatorDot(rc.getLocation().add(dir),255,255,255);
                    if (isWithinVision(rc.getLocation().add(dir), rc.getDirection(), enemy.location, visionConeRadiusSquared(enemy.getType()))) {

                    } else if (rc.canTurn() && isWithinVision(rc.getLocation().add(dir), dir, enemy.location, visionConeRadiusSquared(enemy.getType()))) {
                        Vision::turn(dir);
                    }
                    if (rc.canMove(dir)) {
                        if (dir != Direction::CENTER)
                            rc.move(dir);
                        if (rc.canCarryRat(enemy.location)) {
                            rc.carryRat(enemy.location);
                            enemyRobots = rc.senseNearbyRobots(-1, opponentTeam);
                            closestEnemy = RobotInfo();
                            for (const RobotInfo& info : enemyRobots) {
                                if (Vision::hasSeenLocation(info.location) && !Vision::canReach(info.location))
                                    continue;
                                else if (isNullRobot(closestEnemy) || rc.getLocation().distanceSquaredTo(info.location) < rc.getLocation().distanceSquaredTo(closestEnemy.location) || (info.health < closestEnemy.health && rc.getLocation().distanceSquaredTo(info.location) <= rc.getLocation().distanceSquaredTo(closestEnemy.location))) {
                                    closestEnemy = info;
                                }
                            }
                            if (isNullRobot(closestEnemy)) return false;
                        } else if (canPickUp(rc.getLocation(), enemy) && rc.canTurn(rc.getLocation().directionTo(enemy.location))) {
                            Vision::turn(rc.getLocation().directionTo(enemy.location));
                            if (rc.canCarryRat(enemy.location)) {
                                rc.carryRat(enemy.location);
                                enemyRobots = rc.senseNearbyRobots(-1, opponentTeam);
                                closestEnemy = RobotInfo();
                                for (const RobotInfo& info : enemyRobots) {
                                    if (Vision::hasSeenLocation(info.location) && !Vision::canReach(info.location))
                                        continue;
                                    else if (isNullRobot(closestEnemy) || rc.getLocation().distanceSquaredTo(info.location) < rc.getLocation().distanceSquaredTo(closestEnemy.location) || (info.health < closestEnemy.health && rc.getLocation().distanceSquaredTo(info.location) <= rc.getLocation().distanceSquaredTo(closestEnemy.location))) {
                                        closestEnemy = info;
                                    }
                                }
                            }
                            if (isNullRobot(closestEnemy)) return false;
                        }
                    }
                }
            }
        }
    }


    if (rc.isActionReady() && isNullRobot(rc.getCarrying())) {
        for (const RobotInfo& enemy : enemyRobots) {
            if (enemy.location.distanceSquaredTo(rc.getLocation()) >= 9) continue;
            for (const Direction& dir : Direction::allDirections()) {
                if (canPickUp(rc.getLocation().add(dir), enemy)) {
                    //rc.setIndicatorDot(rc.getLocation().add(dir),255,255,255);
                    if (isWithinVision(rc.getLocation().add(dir), rc.getDirection(), enemy.location, visionConeRadiusSquared(enemy.getType()))) {

                    } else if (rc.canTurn() && isWithinVision(rc.getLocation().add(dir), dir, enemy.location, visionConeRadiusSquared(enemy.getType()))) {
                        Vision::turn(dir);
                    }
                    if (rc.canMove(dir)) {
                        if (dir != Direction::CENTER)
                            rc.move(dir);
                        if (rc.canCarryRat(enemy.location)) {
                            rc.carryRat(enemy.location);
                            enemyRobots = rc.senseNearbyRobots(-1, opponentTeam);
                            closestEnemy = RobotInfo();
                            for (const RobotInfo& info : enemyRobots) {
                                if (Vision::hasSeenLocation(info.location) && !Vision::canReach(info.location))
                                    continue;
                                else if (isNullRobot(closestEnemy) || rc.getLocation().distanceSquaredTo(info.location) < rc.getLocation().distanceSquaredTo(closestEnemy.location) || (info.health < closestEnemy.health && rc.getLocation().distanceSquaredTo(info.location) <= rc.getLocation().distanceSquaredTo(closestEnemy.location))) {
                                    closestEnemy = info;
                                }
                            }
                            if (isNullRobot(closestEnemy)) return false;
                        } else if (canPickUp(rc.getLocation(), enemy) && rc.canTurn(rc.getLocation().directionTo(enemy.location))) {
                            Vision::turn(rc.getLocation().directionTo(enemy.location));
                            if (rc.canCarryRat(enemy.location)) {
                                rc.carryRat(enemy.location);
                                enemyRobots = rc.senseNearbyRobots(-1, opponentTeam);
                                closestEnemy = RobotInfo();
                                for (const RobotInfo& info : enemyRobots) {
                                    if (Vision::hasSeenLocation(info.location) && !Vision::canReach(info.location))
                                        continue;
                                    else if (isNullRobot(closestEnemy) || rc.getLocation().distanceSquaredTo(info.location) < rc.getLocation().distanceSquaredTo(closestEnemy.location) || (info.health < closestEnemy.health && rc.getLocation().distanceSquaredTo(info.location) <= rc.getLocation().distanceSquaredTo(closestEnemy.location))) {
                                        closestEnemy = info;
                                    }
                                }
                                if (isNullRobot(closestEnemy)) return false;
                            }
                        }
                    }
                }
            }
        }
    }
    if (isNullRobot(closestEnemy)) return false;
    scratch();
    if (rc.canMove(rc.getLocation().directionTo(closestEnemy.location))) {
        if (containsDir(invisDirections, rc.getLocation().directionTo(closestEnemy.location))) {
            if (rc.getLocation().add(rc.getLocation().directionTo(closestEnemy.location)).directionTo(closestEnemy.location) == rc.getLocation().directionTo(closestEnemy.location) && rc.canTurn()) {
                Vision::turn(rc.getLocation().directionTo(closestEnemy.location));
            }
            rc.move(rc.getLocation().directionTo(closestEnemy.location));
        } else if (rc.canMove(rc.getLocation().directionTo(closestEnemy.location).rotateLeft()) && containsDir(invisDirections, rc.getLocation().directionTo(closestEnemy.location).rotateLeft())) {
            if (rc.getLocation().add(rc.getLocation().directionTo(closestEnemy.location).rotateLeft()).directionTo(closestEnemy.location) == rc.getLocation().directionTo(closestEnemy.location).rotateLeft() && rc.canTurn()) {
                Vision::turn(rc.getLocation().directionTo(closestEnemy.location).rotateLeft());
            }
            rc.move(rc.getLocation().directionTo(closestEnemy.location).rotateLeft());
        } else if (rc.canMove(rc.getLocation().directionTo(closestEnemy.location).rotateRight()) && containsDir(invisDirections, rc.getLocation().directionTo(closestEnemy.location).rotateRight())) {
            if (rc.getLocation().add(rc.getLocation().directionTo(closestEnemy.location).rotateRight()).directionTo(closestEnemy.location) == rc.getLocation().directionTo(closestEnemy.location).rotateRight() && rc.canTurn()) {
                Vision::turn(rc.getLocation().directionTo(closestEnemy.location).rotateRight());
            }
            rc.move(rc.getLocation().directionTo(closestEnemy.location).rotateRight());
        } else if (rc.canMove(rc.getLocation().directionTo(closestEnemy.location))) {
            if (rc.getLocation().add(rc.getLocation().directionTo(closestEnemy.location)).directionTo(closestEnemy.location) == rc.getLocation().directionTo(closestEnemy.location) && rc.canTurn()) {
                Vision::turn(rc.getLocation().directionTo(closestEnemy.location));
            }
            rc.move(rc.getLocation().directionTo(closestEnemy.location));
        } else if (rc.canMove(rc.getLocation().directionTo(closestEnemy.location).rotateRight())) {
            if (rc.getLocation().add(rc.getLocation().directionTo(closestEnemy.location).rotateRight()).directionTo(closestEnemy.location) == rc.getLocation().directionTo(closestEnemy.location).rotateRight() && rc.canTurn()) {
                Vision::turn(rc.getLocation().directionTo(closestEnemy.location).rotateRight());
            }
            rc.move(rc.getLocation().directionTo(closestEnemy.location).rotateRight());
        } else if (rc.canMove(rc.getLocation().directionTo(closestEnemy.location).rotateLeft())) {
            if (rc.getLocation().add(rc.getLocation().directionTo(closestEnemy.location).rotateLeft()).directionTo(closestEnemy.location) == rc.getLocation().directionTo(closestEnemy.location).rotateLeft() && rc.canTurn()) {
                Vision::turn(rc.getLocation().directionTo(closestEnemy.location).rotateLeft());
            }
            rc.move(rc.getLocation().directionTo(closestEnemy.location).rotateLeft());
        }
    } else if (rc.getLocation().distanceSquaredTo(closestEnemy.location) > 15)
        BugNavigator::moveTo(closestEnemy.location, true);

    //if (canUseTrap()) trapMicro();
    scratch();
    if (rc.isMovementReady()) {
        for (const Direction& dir : invisDirections) {
            if (rc.canMove(dir) && dir != Direction::CENTER && 15 >= rc.getLocation().add(dir).distanceSquaredTo(closestEnemy.location)) {
                scratch();
                rc.move(dir);
                scratch();
                break;
            }
        }
    }
    scratch();
    if (rc.isMovementReady() && rc.getHealth() < closestEnemy.health && rc.getLocation().distanceSquaredTo(closestEnemy.location) <= 8) {
        if (rc.canMove(closestEnemy.location.directionTo(rc.getLocation()))) {
            if (!canUseTrap()) {
                scratch();
                if (isNullRobot(closestEnemy)) return false;
            }
            rc.move(closestEnemy.location.directionTo(rc.getLocation()));
            scratch();
        } else if (rc.canMove(closestEnemy.location.directionTo(rc.getLocation()).rotateLeft())) {
            if (!canUseTrap()) {
                scratch();
                if (isNullRobot(closestEnemy)) return false;
            }
            rc.move(closestEnemy.location.directionTo(rc.getLocation()).rotateLeft());
            scratch();
        } else if (rc.canMove(closestEnemy.location.directionTo(rc.getLocation()).rotateRight())) {
            if (!canUseTrap()) {
                scratch();
                if (isNullRobot(closestEnemy)) return false;
            }
            rc.move(closestEnemy.location.directionTo(rc.getLocation()).rotateRight());
            scratch();
            if (isNullRobot(closestEnemy)) return false;
        }
    }
    if (isNullRobot(closestEnemy)) return false;
    if (rc.canTurn(rc.getLocation().directionTo(closestEnemy.location)))
        Vision::turn(rc.getLocation().directionTo(closestEnemy.location));
    scratch();

    return true;
}

bool Attack::attack() {
    if (!isNullRobot(rc.getCarrying())) {
        if (rc.getCarrying().getTeam() == myTeam) return false;
        gunner();
    }

    //if (rc.getRawCheese() >= minerReturnThreshold) return false;

    //if (enemyRobots.length == 1 && enemyRobots[0].getType() != UnitType.RAT_KING && Miner.shouldBeMiner()) return onevone();
    if (isNullRobot(closestEnemy)) {
        if (catRobots.size() > 0) {
            catMicro();
        }
        return false;
    }
    if (closestEnemy.health - rc.getHealth() > 13 || squeaksReadLastRound + 2 < (int)enemyRobots.size()) {
        holdLine();
    } else if (squeaksReadLastRound >= (int)enemyRobots.size()) {
        moveIn();
    } else {
        holdLine();
    }
    if (rc.isActionReady()) {
        /*
        for (int i = 0; i < 8; i++) {
            if (rc.canCarryRat(rc.getLocation().add(adjacentDirections[i])) && rc.senseRobotAtLocation(rc.getLocation().add(adjacentDirections[i])).getTeam().equals(opponentTeam)) {
                rc.carryRat(rc.getLocation().add(adjacentDirections[i]));
            }
        }

         */
        for (int i = 0; i < 8; i++) {
            if (rc.canAttack(rc.getLocation().add(adjacentDirections[i])) && rc.senseRobotAtLocation(rc.getLocation().add(adjacentDirections[i])).type != UnitType::CAT) {
                rc.attack(rc.getLocation().add(adjacentDirections[i]));
            }
        }
    }
    return true;
}

int Attack::throwDamage(MapLocation pos, Direction dir, RobotInfo enemy) {
    MapLocation x = pos;
    for (int i = 0; i < 8; i++) {
        x = x.add(dir);
        if (i != 0 && !rc.onTheMap(x)) {
            return 46 - i * 4;
        }
        if (!rc.canSenseLocation(x))
            return 0;
        MapInfo info = rc.senseMapInfo(x);
        if (!info.isPassable()) {
            if (i != 0 && (info.isWall() || info.isDirt()))
                return 46 - i * 4;
            return 0;
        } else if (rc.isLocationOccupied(x)) {
            RobotInfo bot = rc.senseRobotAtLocation(x);
            if (i != 0 && bot.team == rc.getTeam()) {
                return min(enemy.health, 46 - i * 4) - min(bot.health, 46 - i * 4);
            } else if (i != 0 && bot.team == opponent(rc.getTeam())) {
                return min(enemy.health, 46 - i * 4) + min(bot.health, 46 - i * 4);
            } else if (i != 0 && bot.team == Team::NEUTRAL) {
                return enemy.health;
            } else
                return 0;
        }
    }
    return 0;
}

void Attack::gunner() {
    holdingRounds++;
    vector<Direction> safeDirs = getSafeDirections();
    if (isNullRobot(rc.getCarrying())) {
        holdingRounds = 0;
        return;
    }
    rc.setIndicatorString("gunner");
    if (rc.canThrowRat() && !closestEnemyKing.isNull()) {
        if (rc.getLocation().distanceSquaredTo(closestEnemyKing) <= 15) {
            if (rc.canTurn() || rc.getLocation().directionTo(closestEnemyKing) == rc.getDirection()) {
                Vision::turn(rc.getLocation().directionTo(closestEnemyKing));
                if (rc.canThrowRat()) rc.throwRat();
            }
        }
    }
    if (!rc.isActionReady() && !isNullRobot(closestEnemy)) {
        for (int i = 0; i < (int)safeDirs.size(); i++) {
            if (safeDirs[i] == Direction::CENTER)
                break;
            if (rc.canMove(safeDirs[i])) {
                rc.move(safeDirs[i]);
                break;
            }
        }
        return;
    }
    rc.setIndicatorString("can shoot");

    if (rc.isActionReady() && containsDir(safeDirs, Direction::CENTER)) {
        Direction shoot = rc.getDirection();
        MapLocation loc = rc.getLocation().add(shoot);
        if (Vision::hasSeenLocation(loc) && Vision::sensePassability(loc) && !rc.canSenseRobotAtLocation(loc) && rc.canSenseRobotAtLocation(loc.add(shoot)) && rc.senseRobotAtLocation(loc.add(shoot)).getTeam() == opponentTeam) {
            rc.throwRat();
        } else if (rc.canTurn()) {
            shoot = shoot.rotateLeft();
            loc = rc.getLocation().add(shoot);
            if (Vision::hasSeenLocation(loc) && Vision::sensePassability(loc) && !rc.canSenseRobotAtLocation(loc) && rc.canSenseRobotAtLocation(loc.add(shoot)) && rc.senseRobotAtLocation(loc.add(shoot)).getTeam() == opponentTeam) {
                Vision::turn(shoot);
                rc.throwRat();
            } else {
                shoot = rc.getDirection().rotateRight();
                loc = rc.getLocation().add(shoot);
                if (Vision::hasSeenLocation(loc) && Vision::sensePassability(loc) && !rc.canSenseRobotAtLocation(loc) && rc.canSenseRobotAtLocation(loc.add(shoot)) && rc.senseRobotAtLocation(loc.add(shoot)).getTeam() == opponentTeam) {
                    Vision::turn(shoot);
                    rc.throwRat();
                }
            }
        }
    }



    //TODO move to frontline/ move in to throw
    if (!isNullRobot(closestEnemy)) {
        for (int i = 0; i < 8; i++) {
            MapLocation x = closestEnemy.location.add(adjacentDirections[i]).add(adjacentDirections[i]);
            if (x.isAdjacentTo(rc.getLocation()) && containsDir(safeDirs, rc.getLocation().directionTo(x)) && (rc.canTurn(rc.getLocation().add(rc.getLocation().directionTo(x)).directionTo(closestEnemy.location)) || rc.getLocation().add(rc.getLocation().directionTo(x)).directionTo(closestEnemy.location) == rc.getDirection())) {
                Direction dir = rc.getLocation().directionTo(x);
                if (rc.canMove(dir) || dir == Direction::CENTER) {
                    if (dir != Direction::CENTER)
                        rc.move(dir);
                    Vision::turn(rc.getLocation().directionTo(closestEnemy.location));
                    if (rc.canThrowRat()) {
                        rc.throwRat();
                        holdingRounds = 0;
                        return;
                    }
                }
            }
        }
    }
    if (!rc.isActionReady())
        return;
    for (int j = 0; j < 8; j++) {
        MapLocation x = rc.getLocation().add(adjacentDirections[j]).add(adjacentDirections[j]);
        if ((Vision::hasSeenLocation(x) && (Vision::isWall(x) || Vision::isDirt(x))) || (!rc.onTheMap(x) && rc.onTheMap(x.add(x.directionTo(rc.getLocation()))))) {
            Vision::turn(adjacentDirections[j]);
            if (rc.canThrowRat()) {
                rc.throwRat();
                holdingRounds = 0;
                return;
            }
        }
    }
    if (holdingRounds == 8 || (!rc.isMovementReady() && !containsDir(safeDirs, Direction::CENTER))) {
        //desperateThrow();
        Direction d = newBestThrowingDirection(rc.getCarrying());
        if (d != DIR_NULL && rc.canTurn(d))
            Vision::turn(d);
        if (rc.canThrowRat())
            rc.throwRat();
        holdingRounds = 0;
    }
}

int Attack::indexOf(const vector<Direction>& arr, Direction dir) {
    for (int i = 0; i < (int)arr.size(); i++) {
        if (arr[i] == dir)
            return i;
    }
    return -1;
}

bool Attack::willGetKidnapped(MapLocation loc, Direction dir, int ignoreID) {
    int arr[8] = {};
    for (int i = 0; i < (int)adjacentDirections.size(); i++) {
        if (rc.canSenseLocation(loc.add(adjacentDirections[i])) && !rc.sensePassability(loc.add(adjacentDirections[i])))
            continue;
        for (int j = 0; j < (int)enemyRobots.size(); j++) {
            if (enemyRobots[j].getID() == ignoreID)
                continue;
            if (enemyRobots[j].location.isAdjacentTo(loc.add(adjacentDirections[i])) || enemyRobots[j].location == loc.add(adjacentDirections[i])) {
                if (arr[i] == 0)
                    arr[i] = 1;
                if (enemyRobots[j].health > rc.getHealth())
                    arr[i] = 2;
            }
        }
    }
    if (dir != DIR_NULL) {
        int x = indexOf(adjacentDirections, dir);
        for (int i = 0; i < 8; i++) {
            if (arr[i] >= 1 && (i - x + 8) % 8 > 1)
                return true;
            if (arr[i] == 2)
                return true;
        }
    }
    for (int i = 0; i < 8; i++) {
        if (arr[(i + 7) % 8] >= 1) {
            for (int j = i + 1; j < 8; j++) {
                if (arr[j] >= 1)
                    return true;
            }
            break;
        }
    }
    return false;
}


bool Attack::attackType(UnitType type) {
    if (!rc.isActionReady()) return false;

    // find attackable robot of type
    if (type == UnitType::CAT) {
        for (const RobotInfo& nearbyRobot : catRobots) {
            MapLocation cat = nearbyRobot.getLocation();
            MapLocation m1 = MapLocation(cat.x, cat.y);
            MapLocation m2 = MapLocation(cat.x + 1, cat.y);
            MapLocation m3 = MapLocation(cat.x, cat.y + 1);
            MapLocation m4 = MapLocation(cat.x + 1, cat.y + 1);
            if (rc.canAttack(m1)) rc.attack(m1);
            if (rc.canAttack(m2)) rc.attack(m2);
            if (rc.canAttack(m3)) rc.attack(m3);
            if (rc.canAttack(m4)) rc.attack(m4);
        }
    } else {
        for (const RobotInfo& nearbyRobot : enemyRobots) {
            if (nearbyRobot.getType() == type) {
                // attack if can
                int boost = 0;
                if (type == UnitType::RAT_KING) {
                    boost = 0;
                } else {
                    if (nearbyRobot.getHealth() == 11) boost = 1;
                    else if (nearbyRobot.getHealth() == 12) boost = 2;
                }
                if (rc.getRawCheese() == 0 && rc.getGlobalCheese() < safeCheeseReserve / 2) boost = 0;
                for (const MapLocation& loc : getRobotLocations(nearbyRobot.getLocation(), type)) {
                    if (rc.canAttack(loc, boost)) {
                        if (boost > 0) {
                            rc.setIndicatorDot(rc.getLocation(), 255, 255, 0);
                            std::cout << "Boosted attack!" << '\n';
                        }
                        rc.attack(loc, boost);
                        return true;
                    }
                }
            }
        }
    }
    return false;
}

bool Attack::attackKing() {
    return attackType(UnitType::RAT_KING);
}

bool Attack::attackBaby() {
    return attackType(UnitType::BABY_RAT);
}

bool Attack::attackCat() {
    return attackType(UnitType::CAT);
}

}  // namespace Utils
