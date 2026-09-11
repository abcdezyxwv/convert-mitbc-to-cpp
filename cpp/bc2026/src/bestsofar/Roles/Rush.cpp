#include "Roles/Rush.hpp"
#include "Baby.hpp"
#include "Utils/Attack.hpp"
#include "Utils/Navigator.hpp"
#include "Utils/Symmetry.hpp"
#include "Utils/Vision.hpp"

using namespace Utils;

namespace Roles {

MapLocation Rush::spawnLoc = MapLocation::NONE;
MapLocation Rush::rush = MapLocation::NONE;
MapLocation Rush::approx = MapLocation::NONE;
int Rush::remainingSym = 0;
int Rush::guessedSym = 0;
int Rush::susFactor[5] = {};
int Rush::turnsStuck = 0;
int Rush::bestDist;
int Rush::approxRound = 0;
bool Rush::kingFound = false;

// static import of java.lang.Integer.bitCount
static inline int bitCount(int x) { return __builtin_popcount((unsigned)x); }

MapLocation Rush::getNewRushLocation() {

//        // If all the symmetries have been tried
//        if (remainingSym == 7) {
//            Baby.explorer = true;
//            guessedSym = 0;
//            return new MapLocation(rng.nextInt(mapWidth), rng.nextInt(mapHeight));
//        }

    vector<int> possibleSymmetries = Symmetry::getPossibleSymmetries();
    MapLocation possibleRushLocations[6];
    int guesses[6] = {};
    int prlSize = 0;

    for (const int& s : possibleSymmetries) {
        guesses[prlSize] = s;
        possibleRushLocations[prlSize++] = Symmetry::symmetricallyOpposite(spawnLoc, s);

        if (s == 4) {
            guesses[prlSize] = s;
            possibleRushLocations[prlSize++] = Symmetry::symmetricallyOpposite(spawnLoc, s);
            guesses[prlSize] = s;
            possibleRushLocations[prlSize++] = Symmetry::symmetricallyOpposite(spawnLoc, s);
            guesses[prlSize] = s;
            possibleRushLocations[prlSize++] = Symmetry::symmetricallyOpposite(spawnLoc, s);
        }
    }

    int pray = rng.nextInt(prlSize);
    guessedSym = guesses[pray];

    return mapLocationAddNoise(possibleRushLocations[pray], 3);
}

void Rush::run(MapLocation spawn) {
    if (spawnLoc.isNull()) spawnLoc = spawn;
    spawnLoc = spawn;

    if (rc.canTurn()) {
        for (int i = 0; i < (int)enemyRobots.size(); i++) {
            const RobotInfo& ri = enemyRobots[i];
            if (ri.getType() == UnitType::RAT_KING) {
                kingFound = true;
                Direction dir = rc.getLocation().directionTo(ri.location);
                Vision::turn(dir);
                break;
            }
        }
    }

    // return to save the king
    int mode = rc.readSharedArray(60);
    if (mode == 2) {
        // very urgent
        if (!kingFound) {
            Navigator::moveTo(kingPos[0], true);
        }
    } else if (mode == 1) {
        // see which one is closer
        if (rc.getLocation().distanceSquaredTo(rush) > rc.getLocation().distanceSquaredTo(kingPos[0])) {
            Navigator::moveTo(kingPos[0], true);
        }
    }

    // guess symmetry
//        remainingSym |= Symmetry.symm;
    if (kingFound) guessedSym = 0;
    if (guessedSym > 0) {
        if ((Symmetry::symm & guessedSym) > 0) {
            guessedSym = 0;
            rush = MapLocation::NONE;
        }
    }
    if (rush.isNull()) {
        rush = getNewRushLocation();
        bestDist = rc.getLocation().distanceSquaredTo(rush);
    }
    if (!kingFound && (rc.getLocation().isWithinDistanceSquared(rush, 4))) {
        turnsStuck = 0;
//            susFactor[guessedSym] += 1;
//            if (susFactor[guessedSym] > 3) remainingSym |= guessedSym;
        if (bitCount(Symmetry::symm) == 2) {
            Baby::explorer = true;
            return;
        }
        rush = getNewRushLocation();
        bestDist = rc.getLocation().distanceSquaredTo(rush);
    }
    if (!kingFound && !approx.isNull() && rc.getLocation().isWithinDistanceSquared(approx, 2)) {
        approx = MapLocation(approx.x + rng.nextInt() % 3, approx.y + rng.nextInt() % 3);
    }
    if (!kingFound && (rc.getLocation().isWithinDistanceSquared(rush, 2) || turnsStuck > 19)) {
        turnsStuck = 0;
//            susFactor[guessedSym] += 1;
//            if (susFactor[guessedSym] > 3) remainingSym |= guessedSym;
        rush = getNewRushLocation();
        bestDist = rc.getLocation().distanceSquaredTo(rush);
    }
    // if it can see the enemy king, direct it towards it
    for (const RobotInfo& robot : enemyRobots) if (robot.getType() == UnitType::RAT_KING) {
        rush = robot.getLocation();
        kingFound = true;
        break;
    }
    // read the squeaks
    for (const Message& message : rc.readSqueaks(-1)) {
        int m = message.getBytes();
        if ((m & (1 << 30)) == 0) continue;
        m ^= (1 << 30);
        int r = m / 10000;
        int x = (m % 10000) / 100;
        int y = m % 100;
        if (r > approxRound) {
            approxRound = r;
            approx = MapLocation(x, y);
        }
    }
    if (kingFound) {
        int msg = 10000 * (rc.getRoundNum() + 20) + 100 * rush.x + rush.y;
        msg |= (1 << 30);
        rc.squeak(msg);
        hasSqueaked = true;
    } else if (!approx.isNull()) {
        int msg = 10000 * approxRound + 100 * approx.x + approx.y;
        msg |= (1 << 30);
        rc.squeak(msg);
        hasSqueaked = true;
    }
    // no need to return, should be suicidal
    if (!rush.isNull()) {
        if (kingFound) Navigator::moveTo(rush, true);
        else if (!approx.isNull()) Navigator::moveTo(closestOnMap(approx), true);
        else {
            Navigator::moveTo(rush, true);
            int newDist = rc.getLocation().distanceSquaredTo(rush);
            if (newDist < bestDist) {
                bestDist = newDist;
                turnsStuck = 0;
            } else turnsStuck++;
        }
    }

    Attack::attackKing();
    Attack::attackBaby();
}

}  // namespace Roles
