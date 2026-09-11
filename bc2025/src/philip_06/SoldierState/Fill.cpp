#include "SoldierState/Fill.hpp"
#include "RobotPlayer.hpp"
#include "Soldier.hpp"
#include "roles/Mopper.hpp"
#include "roles/Splasher.hpp"
#include <algorithm>
#include <cstring>

namespace philip_06 {
namespace SoldierState {

// java.util.Random.nextBoolean() has no equivalent on api.hpp's Random.
static inline bool rngNextBoolean() { return RobotPlayer::rng.nextInt(2) != 0; }

// ---- Fill::Move -----------------------------------------------------------
Direction Fill::Move::edge;        // Java: = null
MapLocation Fill::Move::vertexA;   // Java: = null
MapLocation Fill::Move::vertexB;   // Java: = null
int Fill::Move::roundsExploring = 0;

bool Fill::Move::stuck = false;
bool Fill::Move::moveRight = false;
vector<MapLocation> Fill::Move::pastLocs;

// utility functions
void Fill::Move::init(RobotController rc) {
    roundsExploring = 0;
    moveRight = rngNextBoolean();
    // init explore stuff
    bool nsEdge = false;
    MapLocation loc = rc.getLocation();
    int maxX = rc.getMapWidth(), maxY = rc.getMapHeight();
    // find closest edge
    if (std::min(loc.x, maxX - loc.x) > std::min(loc.y, maxY - loc.y)) nsEdge = true;
    if (std::min(loc.x, maxX - loc.x) < std::min(loc.y, maxY - loc.y)) nsEdge = false;
    if (std::min(loc.x, maxX - loc.x) == std::min(loc.y, maxY - loc.y)) nsEdge = rngNextBoolean();
    if (nsEdge)
        edge = loc.y < maxY / 2 ? Direction::all[Direction::SOUTH] : Direction::all[Direction::NORTH];
    else
        edge = loc.x < maxX / 2 ? Direction::all[Direction::WEST] : Direction::all[Direction::EAST];
    // randomise a point
    if (edge == Direction::all[Direction::NORTH]) {
        vertexA = MapLocation(2 + RobotPlayer::rng.nextInt(maxX - 4),
                              maxY - 1 - RobotPlayer::rng.nextInt(6));
        vertexB = MapLocation(vertexA.x, 2);
    }
    if (edge == Direction::all[Direction::SOUTH]) {
        vertexA = MapLocation(2 + RobotPlayer::rng.nextInt(maxX - 4), RobotPlayer::rng.nextInt(6));
        vertexB = MapLocation(vertexA.x, maxY - 2);
    }
    if (edge == Direction::all[Direction::EAST]) {
        vertexA = MapLocation(maxX - 1 - RobotPlayer::rng.nextInt(6),
                              2 + RobotPlayer::rng.nextInt(maxY - 4));
        vertexB = MapLocation(2, vertexA.y);
    }
    if (edge == Direction::all[Direction::WEST]) {
        vertexA = MapLocation(RobotPlayer::rng.nextInt(6), 2 + RobotPlayer::rng.nextInt(maxY - 4));
        vertexB = MapLocation(maxX - 2, vertexA.y);
    }
}

// action functions
void Fill::Move::explore(RobotController rc) {
    roundsExploring += 1;
    if (vertexA.isNull() && vertexB.isNull()) init(rc);
    if (!vertexA.isNull()) {
        roles::Mopper::moveTowardsMindlessly(rc, vertexA);
        if (roundsExploring > 69) { vertexA = MapLocation::NONE; roundsExploring = 0; }
        else if (rc.canSenseLocation(vertexA) && !rc.senseMapInfo(vertexA).isPassable()) { vertexA = MapLocation::NONE; roundsExploring = 0; }
        else if (rc.getLocation().isWithinDistanceSquared(vertexA, 2)) { vertexA = MapLocation::NONE; roundsExploring = 0; }
    }
    else if (!vertexB.isNull()) {
        roles::Mopper::moveTowardsMindlessly(rc, vertexB);
        if (roundsExploring > 69) { vertexB = MapLocation::NONE; roundsExploring = 0; }
        else if (rc.canSenseLocation(vertexB) && !rc.senseMapInfo(vertexB).isPassable()) { vertexB = MapLocation::NONE; roundsExploring = 0; }
        else if (rc.getLocation().isWithinDistanceSquared(vertexB, 2)) { vertexB = MapLocation::NONE; roundsExploring = 0; }
    }
}

// ---- Fill -----------------------------------------------------------------
const Direction Fill::directions[8] = {
    Direction::all[Direction::NORTH],
    Direction::all[Direction::NORTHEAST],
    Direction::all[Direction::EAST],
    Direction::all[Direction::SOUTHEAST],
    Direction::all[Direction::SOUTH],
    Direction::all[Direction::SOUTHWEST],
    Direction::all[Direction::WEST],
    Direction::all[Direction::NORTHWEST],
};

vector<MapInfo> Fill::marked;
bool Fill::colours[9][9] = {};

bool Fill::isCorrect(RobotController rc, MapLocation mp) {
    bool curr = isSecondary(rc.senseMapInfo(mp).getPaint());
    return curr == getCacheCol(rc, mp);
}

void Fill::attack(RobotController rc, MapLocation mp) {
    bool colour = getCacheCol(rc, mp);
    if (rc.canAttack(mp)) rc.attack(mp, colour);
}

bool Fill::interfere(RobotController rc, MapLocation mp) {
    if (rc.getNumberTowers() == GameConstants::MAX_NUMBER_OF_TOWERS) return false;
    // api.hpp has no null RobotInfo; a default RobotInfo's location is
    // MapLocation::NONE, used here as the "no robot there" proxy.
    for (const MapLocation& ruin : Soldier::ruins)
        if (rc.senseRobotAtLocation(ruin).getLocation().isNull()) {
            if (ruin.isWithinDistanceSquared(mp, 8)) return true;
        }
    return false;
}

MapLocation Fill::dest;  // Java: = null

void Fill::run(RobotController rc) {
    rc.setIndicatorString("Filler");
//         Check if it needs to be turned into an attacker
    dest = MapLocation::NONE;
    // Precompute the desired colours
    marked.clear();
    std::memset(colours, 0, sizeof(colours));  // Java: colours = new boolean[9][9]
    MapLocation closestNotDone;                // Java: = null
    for (const MapInfo& map : rc.senseNearbyMapInfos()) {
        if (isAlly(map.getMark()) && isSecondary(map.getMark())) {
            if (rc.canSenseLocation(map.getMapLocation().add(Direction::all[Direction::NORTH])) &&
                !rc.senseMapInfo(map.getMapLocation().add(Direction::all[Direction::NORTH])).hasRuin()) {
                marked.push_back(map);
            }
            if (!rc.canSenseLocation(map.getMapLocation().add(Direction::all[Direction::NORTH]))) {
                // Hope and pray :skull:
                marked.push_back(map);
            }
        }
        /*
        if (map.getPaint() == PaintType::EMPTY && !map.hasRuin() && !map.isWall() && (dest.isNull() || rc.getLocation().distanceSquaredTo(map.getMapLocation()) < rc.getLocation().distanceSquaredTo(dest))) {
            dest = map.getMapLocation();
            rc.setIndicatorDot(dest, 255, 0, 0);
        }
         */
    }
    for (const MapInfo& m : marked) {
        for (int i = -2; i <= 2; i++) {
            for (int j = -2; j <= 2; j++) {
                MapLocation curr(m.getMapLocation().x + i, m.getMapLocation().y + j);
                if (rc.onTheMap(curr) && rc.canSenseLocation(curr)) {
                    bool colour = false;
                    int dist = curr.distanceSquaredTo(m.getMapLocation());
                    if (dist == 0 || dist == 5 || dist == 8) colour = true;
                    colours[rc.getLocation().x - curr.x + 4][rc.getLocation().y - curr.y + 4] = colour;
                    if (rc.senseMapInfo(curr).getPaint() != getCachePaint(rc, curr) &&
                        !isEnemy(rc.senseMapInfo(curr).getPaint()) &&
                        (closestNotDone.isNull() ||
                         rc.getLocation().distanceSquaredTo(curr) <
                             rc.getLocation().distanceSquaredTo(closestNotDone))) {
                        closestNotDone = curr;
                    }
                }
            }
        }
    }
//        See if it needs to move (cleared everything)

    //`rc.setIndicatorString(std::to_string(rem));
    if (closestNotDone.isNull()) {
        if (rc.getRoundNum() < 200) {
            for (int i = 0; i < 4; i++) {
                if (!roles::Mopper::randomDestination.isNull() &&
                    roles::Mopper::randomDestination.distanceSquaredTo(rc.getLocation()) >
                        roles::Mopper::randomDestination.distanceSquaredTo(
                            MapLocation(rc.getMapWidth() / 2, rc.getMapHeight() / 2))) {
                    roles::Mopper::resetDest(rc);
                } else
                    break;
            }
        }
        if (isEnemy(rc.senseMapInfo(rc.getLocation()).getPaint())) {
            roles::Mopper::findAnyAllyCell(rc);
            if (roles::Mopper::allyCell.isNull())
                Move::explore(rc);
            else
                roles::Mopper::moveTowardsMindlessly(rc, roles::Mopper::allyCell);
        } else
            Move::explore(rc);
        if (!isAlly(rc.senseMapInfo(rc.getLocation()).getPaint()) && rc.canAttack(rc.getLocation()))
            rc.attack(rc.getLocation(), true);
        for (const Direction& direction : directions) {
            if (rc.onTheMap(rc.getLocation().add(direction)) &&
                !isAlly(rc.senseMapInfo(rc.getLocation().add(direction)).getPaint()) &&
                rc.canAttack(rc.getLocation().add(direction))) {
                rc.attack(rc.getLocation().add(direction), true);
            }
        }
    } else {
        // Try to paint current square first (minimises paint loss)
        if (isAlly(rc.senseMapInfo(rc.getLocation()).getPaint()) ||
            isEnemy(rc.senseMapInfo(rc.getLocation()).getPaint())) {
            for (const MapInfo& mp : rc.senseNearbyMapInfos(4)) {
                MapLocation hit = mp.getMapLocation();
                if (!isEnemy(rc.senseMapInfo(hit).getPaint()) &&
                    (rc.senseMapInfo(hit).getPaint() != getCachePaint(rc, hit))) {
                    MapInfo point = rc.senseMapInfo(hit);
                    if (!point.hasRuin() && !point.isWall() && rc.canAttack(hit) &&
                        !interfere(rc, hit)) {
                        attack(rc, hit);
                    }
                }
            }
            if (!closestNotDone.isNull())
                roles::Mopper::moveTowardsMindfully(rc, closestNotDone);
        } else {
            attack(rc, rc.getLocation());
        }
        roles::Mopper::moveTowardsMindfully(rc, closestNotDone);
    }
    //roles::Mopper::explore(rc);
    if (!isAlly(rc.senseMapInfo(rc.getLocation()).getPaint()) && rc.canAttack(rc.getLocation()))
        rc.attack(rc.getLocation(), true);
    for (const Direction& direction : directions) {
        if (rc.onTheMap(rc.getLocation().add(direction)) &&
            !isAlly(rc.senseMapInfo(rc.getLocation().add(direction)).getPaint()) &&
            rc.canAttack(rc.getLocation().add(direction))) {
            rc.attack(rc.getLocation().add(direction), true);
        }
    }
}

}  // namespace SoldierState
}  // namespace philip_06
