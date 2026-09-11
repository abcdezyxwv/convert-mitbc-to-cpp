#include "Utils/Movement.hpp"

#include "Utils/Globals.hpp"
#include "Utils/Navigator.hpp"
#include "Utils/Vision.hpp"

namespace Utils {

MapLocation Movement::targetLoc = MapLocation::NONE;
MapLocation Movement::explorePoints[144] = {};
int Movement::epSize = 0;
int Movement::turnsStuck = 0;
int Movement::bestDist = 0;

void Movement::indicateAllExplorePoints() {
    for (const MapLocation& loc : explorePoints) {
        rc.setIndicatorDot(loc, 100, 255, 255);
    }
}

void Movement::setNextExplorePoint() {
    targetLoc = explorePoints[rng.nextInt(epSize)];
    turnsStuck = 0;
    bestDist = rc.getLocation().distanceSquaredTo(targetLoc);
}

void Movement::explore() {
    // if theres no target, or reached target, or see target but unreachable
    if (targetLoc.isNull() || rc.getLocation() == targetLoc || turnsStuck > 14 ||
        (Vision::hasSeenLocation(targetLoc) && !Vision::sensePassability(targetLoc))) {
        setNextExplorePoint();
    }

    Navigator::moveTo(targetLoc, true);

    int newDist = rc.getLocation().distanceSquaredTo(targetLoc);
    if (newDist < bestDist) {
        bestDist = newDist;
        turnsStuck = 0;
    } else turnsStuck++;
}

void Movement::init() {
    // Java: explorePoints = new MapLocation[144] (a fresh, all-null array)
    for (int i = 0; i < 144; i++) explorePoints[i] = MapLocation::NONE;

    for (int i = mapWidth / 15; i < mapWidth / 2; i += (i + 6) / 2) {
        for (int j = mapHeight / 15; j < mapHeight / 2; j += (j + 6) / 2) {
            explorePoints[epSize++] = MapLocation(i, j);
            explorePoints[epSize++] = MapLocation(mapWidth - i - 1, j);
            explorePoints[epSize++] = MapLocation(i, mapHeight - j - 1);
            explorePoints[epSize++] = MapLocation(mapWidth - i - 1, mapHeight - j - 1);
        }
    }
}

void Movement::exploreSafe() {
}

void Movement::circle(MapLocation loc) {
    if (!rc.isMovementReady()) return;
    MapLocation target = loc.add(rc.getLocation().directionTo(loc).rotateLeft());
    if (!rc.onTheMap(target)) target = loc;
    Navigator::moveTo(target, false);
}

}  // namespace Utils
