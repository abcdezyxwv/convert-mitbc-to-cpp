#include "King.hpp"
#include "Roles/Rush.hpp"
#include "Utils/Attack.hpp"
#include "Utils/BugNavigator.hpp"
#include "Utils/Comms.hpp"
#include "Utils/Symmetry.hpp"
#include <iostream>

using namespace Utils;
using Utils::BugNavigator;  // static import of distance1d

int King::lastCatTrap = -5;
int King::lastRatTrap = -5;

// SPAWNING ------------------------------------------------------------ //

void King::spawn() {
    MapLocation kingLoc = rc.getLocation();
    MapLocation spawnPositionCandidates[28];
    int spdSize = 0;

    // possible spawning locs
    for (const MapLocation& cand : rc.getAllLocationsWithinRadiusSquared(rc.getLocation(), 10)) {
        if (rc.onTheMap(cand) && rc.canBuildRat(cand)) {
            rc.setIndicatorDot(cand, 255, 255, 255);
            spawnPositionCandidates[spdSize++] = cand;
        }
    }

    if (spdSize > 0) {
        // build facing centre
        if (Roles::Rush::spawnLoc.isNull()) Roles::Rush::spawnLoc = rc.getLocation();
        MapLocation target = Roles::Rush::getNewRushLocation(), todo = MapLocation::NONE;
        int bestDist = 1000000;

        for (int i = 0; i < spdSize; i++) {
            // value of building here
            if (spawnPositionCandidates[i].distanceSquaredTo(target) < bestDist) {
                bestDist = spawnPositionCandidates[i].distanceSquaredTo(target);
                todo = spawnPositionCandidates[i];
            }
        }
        if (rc.canTurn()) rc.turn(rc.getLocation().directionTo(todo));
        rc.buildRat(todo);
    }
}

int King::spawnAmountThreshold() {
    // return safeCheeseReserve;

    int res = rc.getCurrentRatCost() * (20 - (15 * rc.getRoundNum() / 2000));

    // should it be dependent on map size?
    // maybe smaller map = lower threshold -> rush

    return res;
}

int King::insaneSpawnAmountThreshold() {
    int res = rc.getCurrentRatCost() * (40 - (15 * rc.getRoundNum() / 2000));
    return std::min(res, (rc.getRoundNum() > midgame ? 1200 : 2000));
}

void King::spawnIf() {
    if ((rc.getGlobalCheese() - rc.getCurrentRatCost() > spawnAmountThreshold() || (rc.getGlobalCheese() >= minCheese && rc.getCurrentRatCost() < (minNumberRats / 4) * 10 + 10))) {
        if (rc.getCurrentRatCost() < (maxNumberRats / 4) * 10 + 10 || rc.getGlobalCheese() - rc.getCurrentRatCost() > insaneSpawnAmountThreshold() || rc.getRoundNum() > endgame)
            spawn();
    }
}

// SURVIVAL ------------------------------------------------------------ //

Direction King::lastDir;
bool King::lastDirNull = true;
MapLocation King::unsafe[20];
int King::unsafeTime[20] = {};

void King::moveSafety() {
    if (rc.getRoundNum() == spawnRound) return;
    // find the place with the minimum penalty

    int score[9] = {0, 0, 0, 0, 0, 0, 0, 0, 0};

    vector<MapLocation> mines;

    bool disabled[9] = {false, false, false, false, false, false, false, false, false};

    for (const MapInfo& mi : surroundings) {


        if (mi.isWall() && BugNavigator::distance1d(rc.getLocation(), mi.getMapLocation()) == 3) {
            /*
            for (int i = 0; i < 9; i++) if (!disabled[i] && BugNavigator.distance1d(rc.getLocation().add(Direction.DIRECTION_ORDER[i]), mi.getMapLocation()) == 2)
                disabled[i] = true;

             */
            continue;
        }

        Direction dir = rc.getLocation().directionTo(mi.getMapLocation());
        int penalty = 30 - (rc.getLocation().add(dir).distanceSquaredTo(mi.getMapLocation()));
        score[rc.getLocation().directionTo(mi.getMapLocation()).getDirectionOrderNum()] -= penalty < 0 ? 0 : penalty * mi.getCheeseAmount();

        if (mi.hasCheeseMine()) mines.push_back(mi.getMapLocation());
    }

    vector<RobotInfo> hasCheese;

    for (const RobotInfo& ri : allyRobots) {
        if (ri.getRawCheeseAmount() > 0) {
            hasCheese.push_back(ri);
        }
    }

    for (const Direction& dir : Direction::DIRECTION_ORDER) {
        int num = dir.getDirectionOrderNum();
        // cat wapoint
//            for (int i = 0; i < 20; i ++) if (unsafe[i] != null && rc.getRoundNum() - unsafeTime[i] < 30) {
//                int penalty = 30 - (rc.getLocation().add(dir).distanceSquaredTo(unsafe[i]));
//                score[num] += 100 * penalty;
//            }
        // robot
        MapLocation loc = rc.getLocation().add(dir);
        for (const RobotInfo& robot : hasCheese) {
            int penalty = 50 - (loc.distanceSquaredTo(robot.getLocation()));
            score[num] -= (/*20 +*/ robot.getRawCheeseAmount()) * penalty * 2;
        }
        for (const RobotInfo& robot : enemyRobots) {
            int penalty = 50 - (loc.distanceSquaredTo(robot.getLocation()));
            score[num] += 200000 * penalty;
        }
        for (const RobotInfo& robot : catRobots) {
            int penalty = 50 - (loc.distanceSquaredTo(robot.getLocation()));
            score[num] += 2000000 * penalty;  // cat super scary
        }
        for (const MapLocation& ml : mines) {
            int penalty = 50 - (loc.distanceSquaredTo(ml));
            penalty = penalty > 40 ? 50 : penalty;
            score[num] -= 2000 * penalty;
        }
    }

    string scores = "";
    for (int i = 0; i < 9; i++) scores += " " + std::to_string(score[i]);
    rc.setIndicatorString(scores);

    int best = 1000000000;
    Direction dir;
    bool dirNull = true;
    if (rc.canMove(Direction::DIRECTION_ORDER[0]) && score[0] < best && !disabled[0]) {
        best = score[0];
        dir = Direction::DIRECTION_ORDER[0];
        dirNull = false;
    }
    if (rc.canMove(Direction::DIRECTION_ORDER[1]) && score[1] < best && !disabled[1]) {
        best = score[1];
        dir = Direction::DIRECTION_ORDER[1];
        dirNull = false;
    }
    if (rc.canMove(Direction::DIRECTION_ORDER[2]) && score[2] < best && !disabled[2]) {
        best = score[2];
        dir = Direction::DIRECTION_ORDER[2];
        dirNull = false;
    }
    if (rc.canMove(Direction::DIRECTION_ORDER[3]) && score[3] < best && !disabled[3]) {
        best = score[3];
        dir = Direction::DIRECTION_ORDER[3];
        dirNull = false;
    }
    if (rc.canMove(Direction::DIRECTION_ORDER[4]) && score[4] < best && !disabled[4]) {
        best = score[4];
        dir = Direction::DIRECTION_ORDER[4];
        dirNull = false;
    }
    if (rc.canMove(Direction::DIRECTION_ORDER[5]) && score[5] < best && !disabled[5]) {
        best = score[5];
        dir = Direction::DIRECTION_ORDER[5];
        dirNull = false;
    }
    if (rc.canMove(Direction::DIRECTION_ORDER[6]) && score[6] < best && !disabled[6]) {
        best = score[6];
        dir = Direction::DIRECTION_ORDER[6];
        dirNull = false;
    }
    if (rc.canMove(Direction::DIRECTION_ORDER[7]) && score[7] < best && !disabled[7]) {
        best = score[7];
        dir = Direction::DIRECTION_ORDER[7];
        dirNull = false;
    }
    if (rc.canMove(Direction::DIRECTION_ORDER[8]) && score[8] < best && !disabled[8]) {
        best = score[8];
        dir = Direction::DIRECTION_ORDER[8];
        dirNull = false;
    }
    if (!dirNull && !(Direction::all[Direction::CENTER] == dir)) {
        if (rc.canMove(dir)) rc.move(dir);
        if (enemyRobots.size() == 0 && catLoc.isNull()) {
            lastDir = dir;
            lastDirNull = false;
        } else {
            lastDirNull = true;
        }
    } else {
        bool doMove = true;
        vector<MapInfo> mi = rc.senseNearbyMapInfos();
        for (int i = 0; i < (int)mi.size(); i++) if (mi[i].hasCheeseMine()) doMove = false;
        if (doMove && !lastDirNull && rc.canMove(lastDir) && !disabled[lastDir.getDirectionOrderNum()])
            rc.move(lastDir);
    }
    if (rc.isMovementReady() && enemyRobots.size() == 0 && catRobots.size() == 0 && lastSeenEnemy > 8) {
        Direction random = adjacentDirections[rng.nextInt(8)];
        if (rc.canMove(random)) rc.move(random);
    }
}

int King::catID[15] = {};
int King::catRound[15] = {};
int King::pointer = 0;

void King::defendCats() {
    // List of the last 15 seen cats with (id, num)
    for (const RobotInfo& cat : catRobots) {
        catID[pointer] = cat.getID();
        catRound[pointer] = rc.getRoundNum();
        pointer++;
        pointer %= 15;
    }
    // Check if the current map location is already documented
//        boolean canSkip = false;
//        for (int j = 0; j < 20; j ++) if (unsafe[j] != null) {
//            if (rc.getLocation().isWithinDistanceSquared(unsafe[j], 8)) {
//                canSkip = true;
//                break;
//            }
//        }
//        // Check if any cats constantly bother us
//        ... (see Java source)

    // Cat defence
    MapLocation catAttack = MapLocation::NONE;
    int distCat = 1000000;

    if (!catLoc.isNull()) {
        if (rc.isActionReady()) {
            /*
            MapLocation attempt = rc.getLocation().add(rc.getLocation().directionTo(catLoc));
            attempt = attempt.add(attempt.directionTo(catLoc));
            if (rc.canPlaceDirt(attempt)) {
                rc.placeDirt(attempt);
            } else {
                attempt = rc.getLocation().add(rc.getLocation().directionTo(catLoc)).add(rc.getLocation().directionTo(catLoc));
                if (rc.canPlaceDirt(attempt)) {
                    rc.placeDirt(attempt);
                }
            }
             */
            // only place cat traps if cat is too close AHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH
            for (const MapLocation& cand : rc.getAllLocationsWithinRadiusSquared(rc.getLocation(), 8)) {
                if (!catLoc.isNull() && rc.canPlaceCatTrap(cand)) {
                    int dist = cand.distanceSquaredTo(catLoc);
                    if (dist < distCat) {
                        distCat = dist;
                        catAttack = cand;
                    }
                }
            }
        }
    }
    if (rc.getRoundNum() - lastCatTrap >= catSpacing && !catAttack.isNull() && rc.canPlaceCatTrap(catAttack)) {
        rc.placeCatTrap(catAttack);
        lastCatTrap = rc.getRoundNum();
    }
}


void King::tryAttack() {
    if (!rc.isActionReady()) return;
    vector<MapLocation> close = rc.getAllLocationsWithinRadiusSquared(rc.getLocation(), 8);
    for (int i = 0; i < (int)close.size(); i++) if (rc.canAttack(close[i])) {
        rc.attack(close[i]);
        return;
    }
}

void King::defendRats() {
    // Only place traps underneath rats
    int minHealth = 120;
    RobotInfo weak;
    bool weakNull = true;
    for (const RobotInfo& bot : enemyRobots) if (rc.getLocation().distanceSquaredTo(bot.getLocation()) <= 8) {
        if (bot.getHealth() < minHealth) {
            minHealth = bot.getHealth();
            weak = bot;
            weakNull = false;
        }
    }
    if (!weakNull && rc.isActionReady()) {
        if (minHealth < 15) {
            // snipe
            int cheeseBoost = 0;
            if (minHealth == 11) cheeseBoost = 1;
            else if (minHealth == 12) cheeseBoost = 2;
            else if (minHealth == 13) cheeseBoost = 5;
            else if (minHealth == 14) cheeseBoost = 10;
            cheeseBoost = std::min(cheeseBoost, rc.getGlobalCheese());
            if (rc.canAttack(weak.getLocation(), cheeseBoost)) rc.attack(weak.getLocation(), cheeseBoost);
        } else {
            // trap them
            if (rc.canPlaceRatTrap(weak.getLocation())) rc.placeRatTrap(weak.getLocation());
        }
    }

    if (allyRobots.size() <= enemyRobots.size() && enemyRobots.size() > 0) {
        int sumX = 0, sumY = 0;
        for (int i = 0; i < (int)enemyRobots.size(); i++) {
            sumX += enemyRobots[i].location.x;
            sumY += enemyRobots[i].location.y;
        }

        sumX = (sumX + ((int)newestSqueaks.size() + 1) / 2) / ((int)newestSqueaks.size() + 1);
        sumY = (sumY + ((int)newestSqueaks.size() + 1) / 2) / ((int)newestSqueaks.size() + 1);

        int bestScore = 10000000;
        MapLocation bestLocation = MapLocation::NONE;

        vector<MapLocation> nearbyLocations = rc.getAllLocationsWithinRadiusSquared(rc.getLocation(), 8);

        MapLocation centroid = MapLocation(sumX, sumY);

        for (int i = 0; i < (int)nearbyLocations.size(); i++) if (rc.canBuildRat(nearbyLocations[i])) {
            int score = nearbyLocations[i].distanceSquaredTo(centroid);
            for (int j = 0; j < (int)enemyRobots.size(); j++) {
                if (nearbyLocations[i].distanceSquaredTo(enemyRobots[j].location) <= 8) {
                    score += 100000;
                }
            }
            if (score < bestScore) {
                bestScore = score;
                bestLocation = nearbyLocations[i];
            }
        }

        if (!bestLocation.isNull()) {
            if (rc.canTurn()) rc.turn(rc.getLocation().directionTo(bestLocation));
            rc.buildRat(bestLocation);
        }

    }

}

void King::tryDigDirt() {
    if (!catLoc.isNull()) return;
    vector<MapLocation> mls = rc.getAllLocationsWithinRadiusSquared(rc.getLocation(), 8);
    for (int i = 0; i < (int)mls.size(); i++) {
        if (rc.canRemoveDirt(mls[i])) {
            rc.removeDirt(mls[i]);
            break;
        }
    }
}

MapLocation King::newKingPos = MapLocation::NONE;

int King::lastSeenEnemy = 0;

void King::needNewKing() {
    newKingPos = Comms::needNewKing();
    if (!newKingPos.isNull()) {
        for (const MapLocation& ml : kingPos) {
            if (!ml.isNull() && ml.distanceSquaredTo(newKingPos) <= closeToKing) {
                newKingPos = MapLocation::NONE;
                Comms::clearNewKing();
                break;
            }
        }
    }
    if (!newKingPos.isNull()) return;
    MapLocation ml = Comms::checkForNewKings();
    if (ml.isNull()) return;
    if (newKingPos.isNull()) newKingPos = ml;
    std::cout << "RECIEVED!!!" << '\n';
    for (const MapLocation& loc : kingPos) {
        if (!loc.isNull() && loc.distanceSquaredTo(newKingPos) <= closeToKing) {
            newKingPos = MapLocation::NONE;
            return;
        }
    }
    Comms::encodeNewKingPos(newKingPos);
}

void King::spawnNewKing() {
    if (newKingPos.isNull()) return;
    int num = Comms::getNumberBots();
    if (num < botsForNewKing) {
        if (rc.getGlobalCheese() - rc.getCurrentRatCost() > newKingSpawnThreshold) {
            int best = 1000000;
            MapLocation ml = MapLocation::NONE;
            for (const MapLocation& loc : rc.getAllLocationsWithinRadiusSquared(rc.getLocation(), 8)) {
                int dist = loc.distanceSquaredTo(newKingPos);
                if (rc.canBuildRat(loc) && dist < best) {
                    best = dist;
                    ml = loc;
                }
            }
            if (!ml.isNull()) {
                std::cout << "SPWANED!" << '\n';
                if (rc.canTurn()) rc.turn(rc.getLocation().directionTo(ml));
                rc.buildRat(ml);
                Comms::incNewKingBotCount(num);
            }
        }
    } else {
        Comms::incNewKingBotCount(num);
        newKingPos = MapLocation::NONE;
        Comms::clearNewKing();
    }
}

void King::run() {

    if (rc.getRoundNum() == spawnRound) {
        Comms::clearNewKing();
        lastDir = rc.getLocation().directionTo(MapLocation(mapWidth / 2, mapHeight / 2));
        lastDirNull = false;
    }

    // symmetry
    Symmetry::updateSymmetryFromGlobal();
    // if (rc.getRoundNum() != 1) Symmetry.updateNearbySymmetry(); // it's bytecode exceeding really bad :(
    Symmetry::hearNearbySymmetrySqueaks();

    // write to global
    if (Comms::getSymmetry() != Symmetry::symm) {
        Comms::updateSymmetry(Symmetry::symm);
    }

    if (enemyRobots.size() > 0 || catRobots.size() > 0) lastSeenEnemy = 0;
    else lastSeenEnemy++;

    moveSafety();

    //if (Clock.getBytecodeNum() > 12000) return;

    // collect cheese
    for (const MapLocation& loc : rc.getAllLocationsWithinRadiusSquared(rc.getLocation(), 8)) {
        if (rc.canPickUpCheese(loc) && rc.getRawCheese() < maxCheese) pickUpCheese(loc);
    }

    defendCats();
    defendRats();

    if (rc.getRoundNum() <= 1200) {
        needNewKing();
        spawnNewKing();
    } else Comms::clearNewKing();

    spawnIf();

    // try to attack baby -> cat -> king
    if (!Attack::attackBaby()) {
        if (!Attack::attackCat()) {
            Attack::attackKing();
        }
    }

    tryDigDirt();

    tryAttack();

    // send emergency signal
    if (rc.getRoundNum() >= endgame || (rc.getHealth() <= help2Health && (int)enemyRobots.size() >= help2Enemies)) {
        rc.writeSharedArray(60, 2);
    }
    else if (rc.getHealth() <= help1Health && (int)enemyRobots.size() >= help1Enemies) {
        rc.writeSharedArray(60, 1);
    }
    else {
        rc.writeSharedArray(60, 0);
    }

    Comms::squeakEnemies();

    if (!newKingPos.isNull()) rc.setIndicatorString(newKingPos.toString());

}
