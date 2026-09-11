#include "Baby.hpp"

#include "Roles/Hunter.hpp"
#include "Roles/Miner.hpp"
#include "Roles/Multiking.hpp"
#include "Roles/Rush.hpp"
#include "Utils/Attack.hpp"
#include "Utils/CatsAreWalls.hpp"
#include "Utils/Comms.hpp"
#include "Utils/FastSet.hpp"
#include "Utils/Movement.hpp"
#include "Utils/Symmetry.hpp"
#include "Utils/Vision.hpp"

MapLocation Baby::spawn = MapLocation::NONE;

bool Baby::isNewKing = false;
bool Baby::explorer = false;

int Baby::roundsBeingHeld = 0;

void Baby::evadeCats() {
    // evade cats
    Utils::FastSet fst;
    for (const RobotInfo& cat : catRobots) {
        MapLocation fakeID = MapLocation(cat.getID() % 64, (cat.getID() % 4096) >> 6);
        if (!fst.contains(fakeID)) {
            fst.add(fakeID);
            Utils::CatsAreWalls::pretend(cat.location, cat.direction);
        }
    }
    for (const RobotInfo& cat : catsLastTurn) {
        MapLocation fakeID = MapLocation(cat.getID() % 64, (cat.getID() % 4096) >> 6);
        if (!fst.contains(fakeID)) {
            fst.add(fakeID);
            Utils::CatsAreWalls::pretend(cat.location, cat.direction);
            Utils::CatsAreWalls::pretend(cat.location.add(cat.direction), cat.direction);
        }
    }
}

void Baby::unevadeCats() {
    // unevade cats
    Utils::FastSet fst;
    for (const RobotInfo& cat : catRobots) {
        MapLocation fakeID = MapLocation(cat.getID() % 64, (cat.getID() % 4096) >> 6);
        if (!fst.contains(fakeID)) {
            fst.add(fakeID);
            Utils::CatsAreWalls::unpretend(cat.location, cat.direction);
        }
    }
    for (const RobotInfo& cat : catsLastTurn) {
        MapLocation fakeID = MapLocation(cat.getID() % 64, (cat.getID() % 4096) >> 6);
        if (!fst.contains(fakeID)) {
            fst.add(fakeID);
            Utils::CatsAreWalls::unpretend(cat.location, cat.direction);
            Utils::CatsAreWalls::unpretend(cat.location.add(cat.direction), cat.direction);
        }
    }
}

void Baby::burnCooldown() {
    // `closestEnemy == null` -> the default-constructed RobotInfo sentinel, whose
    // location is MapLocation::NONE.
    if (closestEnemy.location.isNull() ||
        rc.getLocation().distanceSquaredTo(closestEnemy.location) > 8) {
        if (rc.getRawCheese() < maxCheese) {
            for (int i = 0; i < 9; i++) {
                if (rc.canPickUpCheese(rc.getLocation().add(Direction::DIRECTION_ORDER[i]))) {
                    pickUpCheese(rc.getLocation().add(Direction::DIRECTION_ORDER[i]));
                    break;
                }
            }
        }
    }

    if (enemyRobots.size() == 0 && closestEnemy.location.isNull()) {
        for (const Direction& direction : Direction::DIRECTION_ORDER) {
            if (rc.canAttack(rc.getLocation().add(direction))) {
                rc.attack(rc.getLocation().add(direction));
                break;
            }
        }
    }

    MapLocation transferLoc = closestKing.add(closestKing.directionTo(rc.getLocation()));
    if (rc.canTransferCheese(transferLoc, rc.getRawCheese()))
        rc.transferCheese(transferLoc, rc.getRawCheese());
}

void Baby::run() {
    // newborn
    if (spawn.isNull()) {
        spawn = rc.getLocation();

        explorer = true;
    }

    // disintegration to disarm opponent
    if (rc.isBeingCarried()) {
        roundsBeingHeld++;
        if (roundsBeingHeld >= 2 && squeaksReadLastRound >= 2 && rc.getHealth() < 50)
            rc.disintegrate();
    } else {
        roundsBeingHeld = 0;
    }

    // check for emergency mode
    if (rc.readSharedArray(60) > 0 && rc.canBecomeRatKing()) {
        rc.becomeRatKing();
        return;
    }

    if (!rc.isBeingThrown() && !rc.isBeingCarried()) {
        // return to king unless can SEE enemies
        if (Roles::Miner::returningToKing && enemyRobots.size() == 0) {
            Roles::Miner::run();
            burnCooldown();
            return;
        }
        // attack micro
        bool didAttack = Utils::Attack::attack();

        if (!didAttack) {
            evadeCats();

            if (isNewKing) {
                Roles::Multiking::run();
            } else {
                if (enemyRobots.size() == 0 && closestEnemy.location.isNull())
                    Roles::Hunter::run();

                // miner
                if (Roles::Miner::shouldBeMiner() && enemyRobots.size() == 0) {
                    rc.setIndicatorDot(MapLocation(0, 0), 255, 255, 0);
                    Roles::Miner::run();
                    if (Roles::Miner::returningToKing) hasSqueaked = true;
                    Utils::Vision::turnJustBecause();
                }
                // explorer
                else if (explorer) {
                    rc.setIndicatorDot(MapLocation(0, 0), 0, 255, 0);
                    Utils::Movement::explore();
                    Utils::Vision::turnJustBecause();
                } else {
                    Roles::Rush::run(spawn);
                    Utils::Vision::turnJustBecause();
                }
            }
            unevadeCats();
        }
        burnCooldown();
    }

    // Inform nearby allies of enemy information
    Utils::Comms::squeakEnemies();

    // symmetry stuff
    Utils::Symmetry::updateSymmetryFromGlobal();
    Utils::Symmetry::updateNearbySymmetry();
    Utils::Symmetry::hearNearbySymmetrySqueaks();
    Utils::Symmetry::commSymmetryToNearby();
}
