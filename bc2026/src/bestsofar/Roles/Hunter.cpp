#include "Roles/Hunter.hpp"

#include <iostream>

namespace Roles {

MapLocation Hunter::cat = MapLocation::NONE;
Direction Hunter::catDir = Direction::all[Direction::CENTER];
int Hunter::unknownRounds = 0;

void Hunter::run() {
    if (!rc.isCooperation()) {
        if (!catLoc.isNull()) {
            MapLocation target = rc.getLocation().add(rc.getLocation().directionTo(catLoc));
            if (rc.canAttack(target)) {
                rc.attack(target);
            }
        }
        return;
    }

    if (rc.readSharedArray(62) == 0) return;
    // Maintain cat position
    unknownRounds += 1;
    if (!catLoc.isNull()) {
        std::cout << "Target seen" << '\n';
        cat = catLoc;
        catDir = rc.senseRobotAtLocation(cat).getDirection();
        unknownRounds = 0;
    }

    // Get the latest information if possible
    //        MapLocation possible = Comms::getPreyLoc();
    //        if (unknownRounds > 0 && possible.x > -1 && rc.getLocation().distanceSquaredTo(possible) < 20) {
    //            cat = possible;
    //            if (unknownRounds > 2) catDir = Direction::all[Direction::CENTER];
    //            unknownRounds = 2;
    //        }
    if (cat.isNull() || unknownRounds > 3 ||
        (rc.getRawCheese() == 0 && rc.getGlobalCheese() < safeCheeseReserve))
        return;
    // Try place cat trap
    MapLocation m1 = MapLocation(cat.x, cat.y);
    MapLocation m2 = MapLocation(cat.x + 1, cat.y);
    MapLocation m3 = MapLocation(cat.x, cat.y + 1);
    MapLocation m4 = MapLocation(cat.x + 1, cat.y + 1);
    if (rc.canPlaceCatTrap(m1)) rc.placeCatTrap(m1);
    if (rc.canPlaceCatTrap(m2)) rc.placeCatTrap(m2);
    if (rc.canPlaceCatTrap(m3)) rc.placeCatTrap(m3);
    if (rc.canPlaceCatTrap(m4)) rc.placeCatTrap(m4);
}

}  // namespace Roles
