#include "SoldierState/Messenger.hpp"

#include "Helper/Comms.hpp"
#include "RobotPlayer.hpp"
#include "Soldier.hpp"
#include "roles/Mopper.hpp"

namespace philip_06 {
namespace SoldierState {

using Helper::Comms;
using roles::Mopper;

void Messenger::run(RobotController rc) {
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
        Mopper::moveTowardsMindlessly(rc, bestOpt);
        return;
    }
    Mopper::moveTowardsMindlessly(rc, bestOpt);
    // Try to send a message
    if (rc.canSendMessage(bestOpt)) {
        int message = Comms::encode(rc, Soldier::priority, Soldier::messageLoc, Soldier::roundNum,
                                    Soldier::message);
        rc.sendMessage(bestOpt, message);
        Soldier::messenger = false;
        Soldier::messageLoc = MapLocation::NONE;
        Soldier::priority = 0;
        Soldier::roundNum = 0;
        Soldier::message = 0;
    }
}

}  // namespace SoldierState
}  // namespace philip_06
