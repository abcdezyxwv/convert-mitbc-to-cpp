#include "Helper/Pathfind.hpp"
#include "RobotPlayer.hpp"
#include "roles/Mopper.hpp"

namespace philip_06 {
namespace Helper {

MapLocation Pathfind::dest;          // Java: = null
Direction Pathfind::exploreDirection;  // Java: = null (declared, never used)

void Pathfind::setDest(RobotController rc, MapLocation loc) {
    //if (loc == null) {
    //    dest = MapLocation(RobotPlayer::rng.nextInt(rc.getMapWidth()),
    //                       RobotPlayer::rng.nextInt(rc.getMapHeight()));
    //} else {
    dest = loc;
    //}
}

void Pathfind::makeMove(RobotController rc) {
    //if (dest == null) dest = MapLocation(rc.getMapWidth()/2, rc.getMapHeight()/2);
    if (dest.isNull()) {
        explore(rc);
        return;
    }
    rc.setIndicatorLine(rc.getLocation(), dest, 0, 255, 0);
    roles::Mopper::moveTowardsMindlessly(rc, dest);
}

void Pathfind::explore(RobotController rc) {
    roles::Mopper::explore(rc);
}

}  // namespace Helper
}  // namespace philip_06
