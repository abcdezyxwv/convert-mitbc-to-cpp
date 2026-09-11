#include "Utils/Globals.hpp"

#include <iostream>

#include "Baby.hpp"
#include "Roles/Multiking.hpp"
#include "Utils/Comms.hpp"
#include "Utils/FastSet.hpp"
#include "Utils/Movement.hpp"
#include "Utils/Reachability.hpp"
#include "Utils/Vision.hpp"

namespace Utils {

RobotController Globals::rc;

Random Globals::rng;
const vector<Direction> Globals::directions = {
        Direction::all[Direction::NORTH],
        Direction::all[Direction::NORTHEAST],
        Direction::all[Direction::EAST],
        Direction::all[Direction::SOUTHEAST],
        Direction::all[Direction::SOUTH],
        Direction::all[Direction::SOUTHWEST],
        Direction::all[Direction::WEST],
        Direction::all[Direction::NORTHWEST],
        Direction::all[Direction::CENTER]
};

vector<MapInfo> Globals::surroundings;
vector<RobotInfo> Globals::allyRobots;
vector<RobotInfo> Globals::enemyRobots;
vector<RobotInfo> Globals::catRobots;
vector<RobotInfo> Globals::catsLastTurn;
MapLocation Globals::kingPos[5];
MapLocation Globals::catLoc;
vector<Message> Globals::newestSqueaks;
vector<AdditionalClasses::Thrown> Globals::alliesThrown;
MapLocation Globals::closestKing;
RobotInfo Globals::closestEnemy;
MapLocation Globals::closestEnemyKing;
int Globals::squeaksReadLastRound = 0;
MapLocation Globals::locationLastRound;
vector<RobotInfo> Globals::moreAllies;

int Globals::symmetry = 0;
bool Globals::hasSqueaked = false;
bool Globals::enemiesLastRound = false;
bool Globals::cantTurn = false;
bool Globals::cantMove = false;

int Globals::mapWidth = 0;
int Globals::mapHeight = 0;
int Globals::spawnRound = 0;

int Globals::internalRoundNum = 0;
int Globals::myId = 0;
Team Globals::myTeam = Team::NEUTRAL;
Team Globals::opponentTeam = Team::NEUTRAL;
vector<AdditionalClasses::Threat> Globals::threats;
vector<Direction> Globals::allDirections = Direction::allDirections();
vector<Direction> Globals::adjacentDirections = {
        Direction::all[Direction::NORTH],
        Direction::all[Direction::EAST],
        Direction::all[Direction::SOUTH],
        Direction::all[Direction::WEST],
        Direction::all[Direction::NORTHEAST],
        Direction::all[Direction::SOUTHEAST],
        Direction::all[Direction::SOUTHWEST],
        Direction::all[Direction::NORTHWEST]
};

vector<Message> Globals::lastRound, Globals::thisRound;

void Globals::init(RobotController robotController) {
    rc = robotController;

    mapWidth = rc.getMapWidth();
    mapHeight = rc.getMapHeight();

    spawnRound = rc.getRoundNum();

    internalRoundNum = rc.getRoundNum() - 1;
    myId = rc.getID();
    myTeam = rc.getTeam();
    opponentTeam = opponent(myTeam);

    // Java: kingPos = new MapLocation[5] (all null)
    for (int i = 0; i < 5; i++) kingPos[i] = MapLocation::NONE;

    newestSqueaks.clear();
    alliesThrown.clear();

    cantMove = false;
    cantTurn = false;

    rng = Random(rc.getID());

    symmetry = Comms::getSymmetry();

    if (rc.getType() == UnitType::BABY_RAT)
        Baby::isNewKing = Roles::Multiking::isMultiking();

    Vision::init();
    Comms::init();
    Movement::init();


}

void Globals::startTurn() {

    Comms::startTurn();


    surroundings = rc.senseNearbyMapInfos();
    allyRobots = rc.senseNearbyRobots(-1, myTeam);

    FastSet knownAllies;
    for (const RobotInfo& r : allyRobots) knownAllies.add(MapLocation(r.getID()%64, (r.getID()>>6)%64));

    enemyRobots = rc.senseNearbyRobots(-1, opponentTeam);
    catRobots = rc.senseNearbyRobots(-1, Team::NEUTRAL);

    lastRound = rc.readSqueaks(rc.getRoundNum()-1);
    thisRound = rc.readSqueaks(rc.getRoundNum());

    internalRoundNum += 1;

    if (rc.getRoundNum() != internalRoundNum) {
        // oh no
        newestSqueaks.assign(thisRound.size(), Message());
        for (int i = 0; i < (int)thisRound.size(); i++) newestSqueaks[i] = thisRound[i];
        internalRoundNum = rc.getRoundNum();
        if (rc.getRoundNum() > spawnRound+5) std::cout << "bytecode limit exceeeeeeeeded :(" << '\n';
    } else if ((int)lastRound.size() >= squeaksReadLastRound) {
        newestSqueaks.assign(lastRound.size() - squeaksReadLastRound + thisRound.size(), Message());

        for (int i = squeaksReadLastRound; i < (int)lastRound.size(); i++)
            newestSqueaks[i - squeaksReadLastRound] = lastRound[i];
        for (int i = 0; i < (int)thisRound.size(); i++)
            newestSqueaks[i + (int)lastRound.size() - squeaksReadLastRound] = thisRound[i];
    }

    MapLocation enemyKingHeard = MapLocation::NONE;

    int sz = 0, sza = 0;
    for (const Message& msg : newestSqueaks) {
        int m = msg.getBytes();
        if (msg.getBytes() < 0) sz++;
        else if (8 <= msg.getBytes() && msg.getBytes() < 16) sza++;
        else if (enemyKingHeard.isNull() && (m&(1 << 25)) > 0) {
            int x, y;
            y = m&0b111111;
            m = m >> 6;
            x = m&0b111111;
            enemyKingHeard = MapLocation(x, y);
        }
    }

    vector<AdditionalClasses::Threat> threats(sz);
    alliesThrown.assign(sza, AdditionalClasses::Thrown());

    moreAllies.clear();


    int ptr = 0;
    sz = 0;
    for (const Message& m : newestSqueaks) {
        if (m.getBytes() <= -1) {
            int msg = -m.getBytes();
            // strongest first

            int hp = msg%1024;
            msg >>= 12;
            Direction dir = Direction::DIRECTION_ORDER[1+msg%8];
            if (!knownAllies.contains(MapLocation(m.getSenderID()%64, (m.getSenderID()>>6)%64))) {
                // api.hpp RobotInfo field order: ID, team, health, location,
                // direction, chirality, type, rawCheeseAmount. The Java's
                // trailing `null` carryingRobot argument has no api.hpp field.
                moreAllies.push_back(RobotInfo{m.getSenderID(), myTeam, hp, m.getSource(), dir, 0, UnitType::BABY_RAT, 0});
            }
            msg >>= 3;

            // weakest second
            dir = Comms::decodeDir(msg & 0b111);
            msg = msg >> 3;
            int y = (msg & 0b111111);
            msg = msg >> 6;
            int x = (msg & 0b111111);
            threats[ptr++] = AdditionalClasses::Threat(MapLocation(x, y), dir, false);
        } else if (8 <= m.getBytes() && m.getBytes() < 16) {
            alliesThrown[sz++] = AdditionalClasses::Thrown(m.getSource(), Direction::DIRECTION_ORDER[m.getBytes()-7]);
        }
    }




    hasSqueaked = false;
    int closest = 0;
    for (int i = 1; i < 5; i++) {
        if (kingPos[i].isNull()) break;
        if (rc.getLocation().distanceSquaredTo(kingPos[closest]) > rc.getLocation().distanceSquaredTo(kingPos[i]))
            closest = i;
    }
    closestKing = kingPos[closest];

    if (rc.isBeingThrown())
        Comms::beingThrown();



    Vision::startTurn();
    if (rc.getRoundNum() != spawnRound && rc.getType() == UnitType::BABY_RAT && enemyRobots.size() > 0) {

        for (const RobotInfo& ri : allyRobots) {
            if (ri.getType() == UnitType::BABY_RAT) {
                Vision::isWall[ri.location.x] |= 1LL<<ri.location.y;
            } else {
                for (const MapLocation& ml : rc.getAllLocationsWithinRadiusSquared(ri.location, 2)) {
                    if (Vision::hasSeenLocation(ml)) Vision::isWall[ri.location.x] |= 1LL<<ri.location.y;
                }
            }
        }


        Reachability::checkReachability(rc.getDirection());
        //for (MapLocation ml : rc.getAllLocationsWithinRadiusSquared(rc.getLocation(), -1))
        //    if (Vision.hasSeenLocation(ml) && Vision.canReach(ml))
        //        rc.setIndicatorDot(ml, 125, 125, 125);


        for (const RobotInfo& ri : allyRobots) {
            if (ri.getType() == UnitType::BABY_RAT) {
                Vision::isWall[ri.location.x] &= ~(1LL<<ri.location.y);
            } else {
                for (const MapLocation& ml : rc.getAllLocationsWithinRadiusSquared(ri.location, 2)) {
                    if (Vision::hasSeenLocation(ml)) Vision::isWall[ri.location.x] &= ~(1LL<<ri.location.y);
                }
            }
        }
    }


    closestEnemy = RobotInfo();
    closestEnemyKing = MapLocation::NONE;
    vector<RobotInfo> reachableEnemies;
    for (const RobotInfo& info : enemyRobots) {
        if (Vision::hasSeenLocation(info.location) && !Vision::canReach(info.location)) continue;
        if (info.type == UnitType::RAT_KING) {
            if (closestEnemyKing.isNull() || rc.getLocation().distanceSquaredTo(info.location) < rc.getLocation().distanceSquaredTo(closestEnemyKing)) {
                closestEnemyKing = info.location;
            }
        }
        else if (isNullRobot(closestEnemy) || rc.getLocation().distanceSquaredTo(info.location) < rc.getLocation().distanceSquaredTo(closestEnemy.location) || (info.health<closestEnemy.health && rc.getLocation().distanceSquaredTo(info.location) <= rc.getLocation().distanceSquaredTo(closestEnemy.location))) {
            closestEnemy = info;
        }
        reachableEnemies.push_back(info);
    }
    if (closestEnemyKing.isNull()) closestEnemyKing = enemyKingHeard;

    enemyRobots = reachableEnemies;

    for (const AdditionalClasses::Threat& t : threats) {
        rc.setIndicatorDot(t.loc, 255, 0, 0);
        if (Vision::hasSeenLocation(t.loc) && !Vision::canReach(t.loc)) continue;
        if (isNullRobot(closestEnemy) || rc.getLocation().distanceSquaredTo(t.loc) < rc.getLocation().distanceSquaredTo(closestEnemy.location)) {
            closestEnemy = RobotInfo{-1, opponentTeam, 100, t.loc, t.dir, 0, UnitType::BABY_RAT, 0};
        }
    }

    catLoc = MapLocation::NONE;
    for (const RobotInfo& ri : catRobots) {
        if (Vision::hasSeenLocation(ri.location) && !Vision::canReach(ri.location)) continue;
        catLoc = ri.location;
    }


}

void Globals::endTurn() {
    // TODO: OPTIMISE THIS
    squeaksReadLastRound = (int)rc.readSqueaks(rc.getRoundNum()).size();
    locationLastRound = rc.getLocation();
    Vision::endTurn();
    if (!closestEnemyKing.isNull()) Comms::squeakEnemyKing(closestEnemyKing);
    catsLastTurn = catRobots;
    enemiesLastRound = enemyRobots.size() > 0;
}

void Globals::debugBytecode(string tag, int interval) {
    if (rc.getRoundNum() % interval != 0) return;
    std::cout << "Bytecode used: " + std::to_string(Clock::getBytecodeNum()) + " - " + tag << '\n';
}

void Globals::debug(string str, int interval) {
    if (rc.getRoundNum() % interval != 0) return;
    std::cout << str << '\n';
}

int Globals::approxNumberBabies() {
    return 4 * ((rc.getCurrentRatCost() / 10) - 1);
}

vector<MapLocation> Globals::getRobotLocations(MapLocation loc, UnitType type) {
    if (type == UnitType::RAT_KING) {
        return vector<MapLocation> {
                loc.add(directions[0]),
                loc.add(directions[1]),
                loc.add(directions[2]),
                loc.add(directions[3]),
                loc.add(directions[4]),
                loc.add(directions[5]),
                loc.add(directions[6]),
                loc.add(directions[7]),
                loc.add(directions[8])
        };
    }
    if (type == UnitType::CAT) {
        return vector<MapLocation> {
                loc.add(Direction::all[Direction::NORTH]),
                loc.add(Direction::all[Direction::NORTHEAST]),
                loc.add(Direction::all[Direction::EAST]),
                loc.add(Direction::all[Direction::CENTER])
        };
    }
    return vector<MapLocation> {loc};
}

MapLocation Globals::closestOnMap(MapLocation ml) {
    return MapLocation(ml.x < mapWidth ? (ml.x >= 0 ? ml.x : 0) : mapWidth-1, ml.y < mapHeight ? (ml.y >= 0 ? ml.y : 0) : mapHeight-1);
}

bool Globals::isWithinVision(MapLocation robotLocation, Direction robotDirection, MapLocation location, int visionRadiusSquared) {
    if (visionRadiusSquared != -1 && visionRadiusSquared < robotLocation.distanceSquaredTo(location))
        return false;
    location = MapLocation(location.x - robotLocation.x, location.y - robotLocation.y);
    if (robotDirection.getDirectionOrderNum() <= 4) {
        if (robotDirection.getDirectionOrderNum() <= 2) {
            if (robotDirection.getDirectionOrderNum() == 1) {
                // WEST
                return location.x <= location.y && location.y <= -location.x;
            }
            // NORTHWEST
            return location.x <= 0 && location.y >= 0;
        }
        if (robotDirection.getDirectionOrderNum() == 3) {
            // NORTH
            return -location.y <= location.x && location.x <= location.y;
        }
        // NORTHEAST
        return location.x >= 0 && location.y >= 0;
    }
    if (robotDirection.getDirectionOrderNum() <= 6) {
        if (robotDirection.getDirectionOrderNum() == 5) {
            // EAST
            return -location.x <= location.y && location.y <= location.x;
        }
        // SOUTHEAST
        return location.x >= 0 && location.y <= 0;
    }
    if (robotDirection.getDirectionOrderNum() == 7) {
        // SOUTH
        return location.y <= location.x && location.x <= -location.y;
    }
    // SOUTHWEST
    return location.x <= 0 && location.y <= 0;
}

MapLocation Globals::mapLocationAddNoise(MapLocation ml, int maxDist) {
    ml = ml.translate(rng.nextInt() % maxDist, rng.nextInt() % maxDist);
    return closestOnMap(ml);
}

void Globals::dontTurn() { cantTurn = false; }
void Globals::dontMove() { cantMove = false; }

void Globals::pickUpCheese(MapLocation ml) {
    if (!rc.canPickUpCheese(ml)) return;
    int x = rc.senseMapInfo(ml).getCheeseAmount();
    if (x+rc.getRawCheese() > maxCheese)
        rc.pickUpCheese(ml, maxCheese-rc.getRawCheese());
    else
        rc.pickUpCheese(ml);
}

}  // namespace Utils
