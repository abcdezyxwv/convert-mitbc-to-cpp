#include "Roles/Miner.hpp"

#include <algorithm>
#include <cmath>
#include <iostream>

#include "Roles/Multiking.hpp"
#include "Utils/Attack.hpp"
#include "Utils/Comms.hpp"
#include "Utils/Navigator.hpp"
#include "Utils/Vision.hpp"

namespace Roles {

const Direction Miner::mineDirections[9] = {
    Direction::all[Direction::CENTER],    Direction::all[Direction::NORTH],
    Direction::all[Direction::NORTHEAST], Direction::all[Direction::EAST],
    Direction::all[Direction::SOUTHEAST], Direction::all[Direction::SOUTH],
    Direction::all[Direction::SOUTHWEST], Direction::all[Direction::WEST],
    Direction::all[Direction::NORTHWEST],
};

Utils::FastSet Miner::mineBlacklist;

MapLocation Miner::mine = MapLocation::NONE;
MapLocation Miner::cheese = MapLocation::NONE;
bool Miner::returningToKing = false;
MapLocation Miner::newKing = MapLocation::NONE;

MapLocation Miner::needNewKing() {
    MapLocation hasMine = MapLocation::NONE;
    int totalCheese = 0, cheeseSquares = 0;
    for (const MapInfo& mi : surroundings) {
        if (mi.hasCheeseMine()) hasMine = mi.getMapLocation();
        totalCheese += mi.getCheeseAmount();
        cheeseSquares += mi.getCheeseAmount() > 0 ? 1 : 0;
    }
    if (totalCheese >= newKingCheeseThreshold && cheeseSquares >= newKingSquaresThreshold)
        return hasMine;
    return MapLocation::NONE;
}

bool Miner::amOccupyingMine(MapLocation loc) { return rc.getLocation().isAdjacentTo(loc); }

bool Miner::mineIsOccupied(MapLocation loc) {
    for (const Direction& dir : mineDirections) {
        // tile in the 3x3 around the cheese mine

        // if its your current location, then you own the mine :)
        if (loc.add(dir) == rc.getLocation()) {
            return false;
        }

        if (!rc.canSenseRobotAtLocation(loc.add(dir))) {
            continue;
        }
        return true;
    }
    return false;
}

// returns true if a vacant cheese mine is found
bool Miner::findMine() {
    for (const MapInfo& info : surroundings) {
        if (info.hasCheeseMine()) {
            MapLocation loc = info.getMapLocation();
            if (mineIsOccupied(loc)) continue;

            mine = loc;
            return true;
        }
    }
    return false;
}

// finds a cheese to go and pickup
bool Miner::findCheese() {
    for (const MapInfo& info : surroundings) {
        if (info.getCheeseAmount() > 0) {
            cheese = info.getMapLocation();
            return true;
        }
    }
    return false;
}

bool Miner::checkMineVacancy() {
    if (mineIsOccupied(mine)) {
        // return to king if i have a respectable amount of cheese
        if (rc.getRawCheese() >= minerSecondaryReturnThreshold ||
            rc.getRawCheese() >= rc.getGlobalCheese()) {
            returningToKing = true;
            returnToKing(false);
        }
        // otherwise ditch mine and become soldier
        else {
            mine = MapLocation::NONE;
            cheese = MapLocation::NONE;
            returningToKing = false;
        }
        return false;
    }
    return true;
}

void Miner::returnToKing(bool urgent) {
    if (rc.getRawCheese() == 0 && (rc.readSharedArray(60) == 0 || Utils::Comms::getNumKings() > 1)) {
        returningToKing = false;
        return;
    }
    rc.setIndicatorString("miner: returning to king");
    Direction dir = rc.getLocation().directionTo(closestKing);
    MapLocation location = closestKing.add(closestKing.directionTo(rc.getLocation()));
    if (rc.canTransferCheese(location, rc.getRawCheese())) {
        rc.transferCheese(location, rc.getRawCheese());
        if (!newKing.isNull()) {
            Utils::Comms::squeakNewKing(newKing);
            newKing = MapLocation::NONE;
        }
        if (rc.canTurn()) Utils::Vision::turn(dir.opposite());
        return;
    }

    if (rc.getLocation().distanceSquaredTo(location) <= 25) {
        if (rc.canTurn()) Utils::Vision::turn(dir);
        if (rc.canTransferCheese(location, rc.getRawCheese())) {
            rc.transferCheese(location, rc.getRawCheese());
            if (!newKing.isNull()) {
                Utils::Comms::squeakNewKing(newKing);
                newKing = MapLocation::NONE;
            }
            return;
        }

    } else {
        if (!urgent && rc.getRawCheese() < 80) {
            for (const MapInfo& mi : surroundings) {
                if (mi.getCheeseAmount() > 5 &&
                    rc.getLocation().distanceSquaredTo(mi.getMapLocation()) <= 8) {
                    if (rc.getLocation().distanceSquaredTo(mi.getMapLocation()) < 4) {
                        pickUpCheese(mi.getMapLocation());
                        break;
                    }
                    Direction d = rc.getLocation().directionTo(mi.getMapLocation());
                    if (rc.getLocation().add(d).isAdjacentTo(mi.getMapLocation()) && rc.canMove(d)) {
                        rc.move(d);
                        pickUpCheese(mi.getMapLocation());
                        break;
                    }
                    d = d.rotateLeft();
                    if (rc.getLocation().add(d).isAdjacentTo(mi.getMapLocation()) && rc.canMove(d)) {
                        rc.move(d);
                        pickUpCheese(mi.getMapLocation());
                        break;
                    }
                    d = d.rotateRight().rotateRight();
                    if (rc.getLocation().add(d).isAdjacentTo(mi.getMapLocation()) && rc.canMove(d)) {
                        rc.move(d);
                        pickUpCheese(mi.getMapLocation());
                        break;
                    }
                }
            }
        }
    }

    Utils::Navigator::moveTo(closestKing, true);

    location = closestKing.add(closestKing.directionTo(rc.getLocation()));

    if (!urgent) {
        for (const Direction& d : adjacentDirections) {
            if (rc.canPickUpCheese(rc.getLocation().add(d))) {
                pickUpCheese(rc.getLocation().add(d));
            }
        }
    }

    if (rc.canTransferCheese(location, rc.getRawCheese())) {
        rc.transferCheese(location, rc.getRawCheese());
        if (!newKing.isNull()) {
            Utils::Comms::squeakNewKing(newKing);
            newKing = MapLocation::NONE;
        }
        cheese = MapLocation::NONE;
        returningToKing = false;
    }
}

bool Miner::shouldBeMiner() {
    if (rc.getRawCheese() == 0) returningToKing = false;
    if (rc.getRawCheese() >= minerReturnThreshold ||
        (rc.getRawCheese() >= minerSecondaryReturnThreshold &&
         rc.getLocation().distanceSquaredTo(closestKing) <= secondaryReturnDistance))
        returningToKing = true;
    if (!mine.isNull() || !cheese.isNull() || returningToKing) return true;
    if (findMine() || findCheese()) return true;
    return false;
}

int Miner::knownSym = 0;

void Miner::run() {
    if (newKing.isNull()) {
        bool mightNeedKing = true;
        MapLocation newMine = needNewKing();
        if (!newMine.isNull()) {
            for (const MapLocation& ml : kingPos)
                if (!ml.isNull() && ml.distanceSquaredTo(newMine) <= closeToKing)
                    mightNeedKing = false;
            if (mightNeedKing) {
                std::cout << "NEED NEW KING!!!" << '\n';
                newKing = newMine;
            }
        }
    }

    if (!cheese.isNull()) {
        rc.setIndicatorLine(rc.getLocation(), cheese, 0, 255, 0);
    }

    // read the help signals
    if (rc.readSharedArray(60) > 0 && Utils::Comms::getNumKings() == 1) {
        returnToKing(true);
        return;
    }

    MapLocation needSacrifice = Utils::Comms::getSacrifices();
    if (!needSacrifice.isNull()) {
        bool squeakToo = true;
        if (needSacrifice.x >= 1000) {
            squeakToo = false;
            needSacrifice = MapLocation(needSacrifice.x - 1000, needSacrifice.y - 1000);
        }
        Multiking::newKingPos = needSacrifice;
        Multiking::moveTo();
        if (rc.getLocation().distanceSquaredTo(needSacrifice) <= 8 && rc.canBecomeRatKing())
            rc.becomeRatKing();
        if (squeakToo) Utils::Comms::squeakForSacrificesToo(needSacrifice);
        return;
    }

    // return to king
    if (returningToKing) {
        returnToKing(false);
        return;
    }

    // choose the closest thing to attack
    if (enemyRobots.size() > 0) {
        if (rc.getGlobalCheese() > emergencyReserve && rc.getRawCheese() <= 20) {
            // attack the enemy
            RobotInfo target;  // Java: null
            bool targetIsNull = true;
            for (const RobotInfo& robot : enemyRobots)
                if (robot.getType() == UnitType::BABY_RAT) {
                    if (targetIsNull) {
                        target = robot;
                        targetIsNull = false;
                    } else if (rc.getLocation().distanceSquaredTo(target.getLocation()) >
                               rc.getLocation().distanceSquaredTo(robot.getLocation())) {
                        target = robot;
                    }
                }
            if (!targetIsNull) {
                Utils::Attack::attackBaby();
                return;
            }
        } else {
            // run to safety with the cheese
            returningToKing = true;
            returnToKing(true);
            if (returningToKing) return;
        }
    }

    // pick up cheese
    if (!cheese.isNull()) {
        if (!mine.isNull() && !checkMineVacancy()) return;

        rc.setIndicatorString("miner: picking up cheese");

        // check that the cheese is still there
        if (rc.canSenseLocation(cheese) && rc.senseMapInfo(cheese).getCheeseAmount() <= 0) {
            cheese = MapLocation::NONE;
        }

        // cheese still there
        else {
            Utils::Navigator::moveTo(cheese, true);

            if (rc.canPickUpCheese(cheese)) {
                if (rc.getRawCheese() < maxCheese) pickUpCheese(cheese);

                cheese = MapLocation::NONE;

                // check to return if i have a lot of cheese
                if (rc.getRawCheese() >= minerReturnThreshold ||
                    rc.getRawCheese() >= rc.getGlobalCheese()) {
                    returningToKing = true;
                    returnToKing(false);
                }

                // look for next cheese, and turn towards
                if (findCheese()) {
                    if (rc.canTurn()) {
                        Utils::Vision::turn(rc.getLocation().directionTo(cheese));
                    }
                }
                // no cheese found, turn towards the mine
                else {
                    if (rc.canTurn()) {
                        Utils::Vision::turn(rc.getLocation().directionTo(mine));
                    }
                }
            }
            return;
        }
    }

    // move towards the mine, and then circle on the mine, looking for cheese
    if (!mine.isNull()) {
        if (!checkMineVacancy()) return;

        rc.setIndicatorString("miner: occupying mine, looking for cheese");

        // try to place a trap at (+1, +1) and (-1, -1)
        // if (rc.canPlaceRatTrap(mine.add(Direction::all[Direction::NORTHEAST]))) rc.placeRatTrap(mine.add(Direction::all[Direction::NORTHEAST]));
        // if (rc.canPlaceRatTrap(mine.add(Direction::all[Direction::SOUTHWEST]))) rc.placeRatTrap(mine.add(Direction::all[Direction::SOUTHWEST]));

        // if im at the mine, scan
        if (rc.getLocation() == mine) {
            if (rc.canTurn()) {
                if (__builtin_popcount((unsigned)rc.getID()) % 2 == 0)
                    Utils::Vision::turn(rc.getDirection().rotateRight().rotateRight());
                else
                    Utils::Vision::turn(rc.getDirection().rotateLeft().rotateLeft());
            }
        }
        // otherwise move towards the mine
        else {
            Utils::Navigator::moveTo(mine, std::max(std::abs(mine.x - rc.getLocation().x),
                                                    std::abs(mine.y - rc.getLocation().y)) > 2);
            if (rc.canTurn()) {
                Utils::Vision::turn(rc.getLocation().directionTo(mine));
                checkMineVacancy();
            }
        }

        // look for cheese
        findCheese();
    }
}

}  // namespace Roles
