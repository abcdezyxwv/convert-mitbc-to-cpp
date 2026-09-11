#include "Roles/AntiCat.hpp"

#include "Utils/Attack.hpp"
#include "Utils/Movement.hpp"
#include "Utils/Navigator.hpp"
#include "Utils/Vision.hpp"

namespace Roles {

int AntiCat::lastTime = -1;
int AntiCat::inARow = 0;

void AntiCat::suicide() { Utils::Attack::attackCat(); }

bool AntiCat::run(MapLocation catLoc) {
    if (lastTime == rc.getRoundNum() - 1) {
        inARow++;
    } else
        inARow = 1;
    MapLocation kingLoc = kingPos[0];
    if (rc.getLocation().distanceSquaredTo(kingLoc) < 8) {
        Direction dir1 = kingLoc.directionTo(catLoc);
        Direction dir2 = kingLoc.add(dir1).directionTo(catLoc);
        MapLocation attempt = kingLoc.add(dir1).add(dir2);
        attempt = attempt.add(attempt.directionTo(catLoc));
        if (rc.canTurn()) {
            Utils::Vision::turn(rc.getLocation().directionTo(catLoc));
        }
        if (Utils::Vision::isDirt(attempt)) {
            dir2 = dir2.rotateLeft();
            attempt = kingLoc.add(dir1).add(dir2);
            if (Utils::Vision::isDirt(attempt)) {
                dir2 = dir2.rotateRight().rotateRight();
                attempt = kingLoc.add(dir1).add(dir2);
            }
        }
        // The Java reads `if (rc.getLocation() == attempt)`, i.e. Java *reference*
        // equality between two freshly-allocated MapLocation objects, which is
        // never true - this branch is dead code in the original bot. Writing
        // `rc.getLocation() == attempt` in C++ would be value equality and would
        // change behaviour, so the dead branch is preserved as dead.
        if (false /* rc.getLocation() == attempt */) {
            Utils::Movement::circle(kingLoc);
        } else if (!rc.getLocation().isWithinDistanceSquared(attempt, 2))
            Utils::Navigator::moveTo(attempt, false);
        if (rc.canPlaceDirt(attempt)) {
            rc.placeDirt(attempt);
            Utils::Vision::placeDirt(attempt);
        }
        return true;
    }
    if (inARow > 10) {
        suicide();
        return true;
    }
    return false;
}

}  // namespace Roles
