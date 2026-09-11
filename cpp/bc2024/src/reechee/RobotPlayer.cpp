#include "RobotPlayer.hpp"
#include "Pathfind.hpp"
#include <iostream>

int RobotPlayer::numDefence = 3;
int RobotPlayer::flagMove1 = 3;
int RobotPlayer::flagMove2 = 5;
TrapType RobotPlayer::defensiveTrapType = TrapType::EXPLOSIVE;

int RobotPlayer::roundNum = 0;
int RobotPlayer::id = -1;

Random RobotPlayer::rng;
int RobotPlayer::teamFlagInfo = -1;
MapLocation RobotPlayer::teamFlagLocation;
int RobotPlayer::role = -1;
MapLocation RobotPlayer::flagTargetLocation;
Direction RobotPlayer::oscillationDirections[8] = {
    Direction::all[Direction::NORTH],     Direction::all[Direction::NORTHEAST],
    Direction::all[Direction::EAST],      Direction::all[Direction::SOUTHEAST],
    Direction::all[Direction::SOUTH],     Direction::all[Direction::SOUTHWEST],
    Direction::all[Direction::WEST],      Direction::all[Direction::NORTHWEST],
};
int RobotPlayer::currentOscillationDirection = 0;

void RobotPlayer::run(RobotController rc) {
    rng = Random(rc.getID());

    while (true) {
        try {
            rc.setIndicatorString(std::to_string(id));

            getGlobalUpgrades(rc);
            roundNum = rc.getRoundNum();

            // Get bot id on round one (0 indexed)
            if (roundNum == 1) {
                id = rc.readSharedArray(0);
                rc.writeSharedArray(0, id + 1);
                role = (id < numDefence) ? 0 : 1;
                Clock::yield();
            }
            // Reset shared array after ids are set
            if (roundNum == 2) {
                rc.writeSharedArray(0, 0);
            }

            if (!rc.isSpawned()) {
                if (id > numDefence) {
                    // Arbitrary spawn - removed for testing (as in the Java source)
                } else {
                    // Spawn on a flag location without a defender
                    vector<MapLocation> spawnLocs = rc.getAllySpawnLocations();
                    MapLocation spawnLoc;
                    for (const MapLocation& i : spawnLocs) {
                        bool isTaken = false;
                        for (int j = 0; j < numDefence; j++) {
                            if (j == id) continue;
                            int packed = rc.readSharedArray(j);
                            if (std::abs(i.x - packed / 60) < 4 &&
                                std::abs(i.y - packed % 60) < 4) {
                                isTaken = true;
                            }
                        }
                        if (rc.canSpawn(i) && !isTaken) {
                            spawnLoc = i;
                        }
                    }
                    if (!spawnLoc.isNull()) {
                        rc.spawn(spawnLoc);
                    }
                }
            }

            if (rc.isSpawned()) {
                if (role == 0) {
                    vector<FlagInfo> nearbyFlags = rc.senseNearbyFlags(-1, rc.getTeam());
                    if (!nearbyFlags.empty()) {
                        if (teamFlagInfo == -1) {
                            teamFlagInfo = nearbyFlags[0].getLocation().x * 60 +
                                           nearbyFlags[0].getLocation().y;
                            rc.writeSharedArray(id, teamFlagInfo);
                            teamFlagLocation = nearbyFlags[0].getLocation();
                        }

                        if (roundNum < 150) {
                            // Move the flag towards the corner
                            int x = 0, y = 0, sx = 0, sy = 0;
                            vector<MapLocation> spawnLocs = rc.getAllySpawnLocations();
                            for (const MapLocation& i : spawnLocs) {
                                sx += i.x;
                                sy += i.y;
                            }
                            sx = sx / 27;
                            sy = sy / 27;
                            if (sx < rc.getMapWidth() / flagMove1) x = -1;
                            if (sx < rc.getMapWidth() / flagMove2) x = -2;
                            if (sx > rc.getMapWidth() - rc.getMapWidth() / flagMove1) x = 1;
                            if (sx > rc.getMapWidth() - rc.getMapWidth() / flagMove2) x = 2;
                            if (sy < rc.getMapHeight() / flagMove1) y = -1;
                            if (sy < rc.getMapHeight() / flagMove2) y = -2;
                            if (sy > rc.getMapHeight() - rc.getMapHeight() / flagMove1) y = 1;
                            if (sy > rc.getMapHeight() - rc.getMapHeight() / flagMove2) y = 2;

                            flagTargetLocation =
                                MapLocation(teamFlagLocation.x + x, teamFlagLocation.y + y);

                            rc.setIndicatorString(std::to_string(id) + ": " +
                                                  std::to_string(sx) + " " + std::to_string(sy));

                            if (!(nearbyFlags[0].getLocation() == flagTargetLocation)) {
                                if (rc.canPickupFlag(nearbyFlags[0].getLocation())) {
                                    rc.pickupFlag(nearbyFlags[0].getLocation());
                                }
                                if (rc.hasFlag()) {
                                    if (rc.canDropFlag(flagTargetLocation)) {
                                        rc.dropFlag(flagTargetLocation);
                                    }
                                    Pathfind::moveTowards(rc, flagTargetLocation);
                                    if (rc.canDropFlag(flagTargetLocation)) {
                                        rc.dropFlag(flagTargetLocation);
                                    }
                                }
                            }
                        } else {
                            // Drop flag and oscillate, placing traps
                            if (rc.hasFlag() && rc.canDropFlag(flagTargetLocation)) {
                                rc.dropFlag(flagTargetLocation);
                            }
                            if (rc.getLocation() ==
                                teamFlagLocation.add(
                                    oscillationDirections[currentOscillationDirection])) {
                                currentOscillationDirection =
                                    (currentOscillationDirection + 1) & 7;
                            }
                            Pathfind::moveTowardsV1(
                                rc, teamFlagLocation.add(
                                        oscillationDirections[currentOscillationDirection]));
                            if (roundNum % numDefence == id) placeTrapsNearFlag(rc);
                        }
                    }
                }

                if (role == 1) {
                    if (roundNum < 150) {
                        Pathfind::explore(rc);
                        Clock::yield();
                    }
                }
            }
        } catch (const GameActionException& e) {
            std::cout << "GameActionException" << '\n';
            std::cout << e.what() << '\n';
        } catch (const std::exception& e) {
            std::cout << "Exception" << '\n';
            std::cout << e.what() << '\n';
        }
        Clock::yield();
    }
}

void RobotPlayer::getGlobalUpgrades(RobotController& rc) {
    if (rc.canBuyGlobal(GlobalUpgrade::HEALING)) rc.buyGlobal(GlobalUpgrade::HEALING);
    if (rc.canBuyGlobal(GlobalUpgrade::ACTION)) rc.buyGlobal(GlobalUpgrade::ACTION);
}

void RobotPlayer::spawnBot(RobotController& rc) {
    vector<MapLocation> spawnLocs = rc.getAllySpawnLocations();
    MapLocation spawnLoc;
    for (const MapLocation& i : spawnLocs) {
        if (rc.canSpawn(i)) spawnLoc = i;
    }
    if (!spawnLoc.isNull()) rc.spawn(spawnLoc);
}

void RobotPlayer::xDefense(RobotController& rc) {
    vector<MapInfo> buildLocs = rc.senseNearbyMapInfos(2);
    MapLocation buildLoc;
    int distanceToFlag = 1000000;
    bool isTrap = false;  // if false, water
    for (const MapInfo& i : buildLocs) {
        if (std::abs(i.getMapLocation().x - flagTargetLocation.x) ==
            std::abs(i.getMapLocation().y - flagTargetLocation.y)) {
            if (rc.canBuild(defensiveTrapType, i.getMapLocation()) &&
                flagTargetLocation.distanceSquaredTo(i.getMapLocation()) < distanceToFlag) {
                distanceToFlag = flagTargetLocation.distanceSquaredTo(i.getMapLocation());
                buildLoc = i.getMapLocation();
                isTrap = true;
            }
        } else {
            if (rc.canDig(i.getMapLocation()) &&
                flagTargetLocation.distanceSquaredTo(i.getMapLocation()) < distanceToFlag) {
                distanceToFlag = flagTargetLocation.distanceSquaredTo(i.getMapLocation());
                buildLoc = i.getMapLocation();
                isTrap = false;
            }
        }
    }
    if (!buildLoc.isNull()) {
        if (isTrap) rc.build(defensiveTrapType, buildLoc);
        else rc.dig(buildLoc);
    }
}

void RobotPlayer::placeTrapsNearFlag(RobotController& rc) {
    vector<MapInfo> buildLocs = rc.senseNearbyMapInfos(2);
    MapLocation buildLoc;
    int distanceToFlag = 1000000;
    for (const MapInfo& i : buildLocs) {
        if (rc.canBuild(defensiveTrapType, i.getMapLocation()) &&
            flagTargetLocation.distanceSquaredTo(i.getMapLocation()) < distanceToFlag) {
            distanceToFlag = flagTargetLocation.distanceSquaredTo(i.getMapLocation());
            buildLoc = i.getMapLocation();
        }
    }
    if (!buildLoc.isNull()) {
        rc.build(defensiveTrapType, buildLoc);
    }
}

void RobotPlayer::healNearby(RobotController& rc) {
    vector<RobotInfo> nearbyRobots = rc.senseNearbyRobots(-1);
    MapLocation toHeal;
    int lowestHeal = 99999;
    MapLocation toAttack;
    int lowestAttack = 99999;
    for (const RobotInfo& currRobot : nearbyRobots) {
        if (currRobot.team == rc.getTeam()) {
            if (currRobot.health < lowestHeal && rc.canHeal(currRobot.location)) {
                lowestHeal = currRobot.health;
                toHeal = currRobot.location;
            }
        } else {
            if (currRobot.hasFlag && rc.canAttack(currRobot.location)) {
                toAttack = currRobot.location;
                break;
            }
            if (currRobot.health < lowestAttack && rc.canAttack(currRobot.location)) {
                lowestAttack = currRobot.health;
                toAttack = currRobot.location;
            }
        }
    }
    if (!toHeal.isNull() && rc.canHeal(toHeal)) rc.heal(toHeal);
    if (!toAttack.isNull() && rc.canHeal(toAttack)) rc.attack(toAttack);
}

void RobotPlayer::attackNearby(RobotController& rc) {
    vector<RobotInfo> nearbyRobots = rc.senseNearbyRobots(-1);
    MapLocation toHeal;
    int lowestHeal = 99999;
    MapLocation toAttack;
    int lowestAttack = 99999;
    for (const RobotInfo& currRobot : nearbyRobots) {
        if (currRobot.team == rc.getTeam()) {
            if (currRobot.health < lowestHeal && rc.canHeal(currRobot.location)) {
                lowestHeal = currRobot.health;
                toHeal = currRobot.location;
            }
        } else {
            if (currRobot.hasFlag && rc.canAttack(currRobot.location)) {
                toAttack = currRobot.location;
                break;
            }
            if (currRobot.health < lowestAttack && rc.canAttack(currRobot.location)) {
                lowestAttack = currRobot.health;
                toAttack = currRobot.location;
            }
        }
    }
    if (!toAttack.isNull() && rc.canHeal(toAttack)) rc.attack(toAttack);
    if (!toHeal.isNull() && rc.canHeal(toHeal)) rc.heal(toHeal);
}
