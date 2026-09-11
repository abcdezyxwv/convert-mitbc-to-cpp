#include "SoldierState/Retreat.hpp"

#include <algorithm>

#include "RobotPlayer.hpp"
#include "Soldier.hpp"
#include "roles/Mopper.hpp"

namespace philip_06 {
namespace SoldierState {

using roles::Mopper;

void Retreat::run(RobotController rc) {
    MapLocation bestOpt = MapLocation::NONE;
    for (const MapLocation& curr : Soldier::paintTowers) {
        if (rc.canSenseLocation(curr) && rc.senseRobotAtLocation(curr).location.isNull()) {
            Soldier::paintTowers.erase(curr);
            break;
        }
    }
    const MapLocation myLoc = rc.getLocation();
    for (const MapLocation& curr : Soldier::paintTowers) {
        if (bestOpt.isNull() ||
            (myLoc.distanceSquaredTo(curr) < myLoc.distanceSquaredTo(bestOpt) &&
             (!rc.canSenseLocation(bestOpt) ||
              !rc.senseRobotAtLocation(bestOpt).location.isNull()))) {
            bestOpt = curr;
        }
    }
    if (bestOpt.isNull()) {
        bestOpt = MapLocation(RobotPlayer::rng.nextInt(rc.getMapWidth()),
                              RobotPlayer::rng.nextInt(rc.getMapHeight()));
        Mopper::moveTowardsMindfully(rc, bestOpt);
        return;
    }
    int transfer = 100 - rc.getPaint();
    if (rc.canSenseLocation(bestOpt) && !rc.senseRobotAtLocation(bestOpt).location.isNull()) {
        transfer = std::min(transfer, rc.senseRobotAtLocation(bestOpt).getPaintAmount());
        rc.setIndicatorString(std::to_string(transfer));
        if (rc.canTransferPaint(bestOpt, -transfer)) rc.transferPaint(bestOpt, -transfer);
    }
    Mopper::moveTowardsMindfully(rc, bestOpt);
}

}  // namespace SoldierState
}  // namespace philip_06
