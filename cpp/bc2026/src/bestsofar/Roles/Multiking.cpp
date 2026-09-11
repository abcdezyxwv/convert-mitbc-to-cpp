#include "Roles/Multiking.hpp"
#include "Baby.hpp"
#include "King.hpp"
#include "Utils/BugNavigator.hpp"
#include "Utils/Comms.hpp"
#include "Utils/Navigator.hpp"
#include "Utils/Vision.hpp"

using namespace Utils;

namespace Roles {

MapLocation Multiking::newKingPos = MapLocation::NONE;
int Multiking::roundsCircled = 0;

bool Multiking::isMultiking() {
    newKingPos = Comms::needNewKing();
    return Comms::getNumberBots() <= botsForNewKing && !newKingPos.isNull();
}

MapLocation Multiking::targetPos = MapLocation::NONE;

void Multiking::moveTo() {
    if (rc.getLocation() == newKingPos) return;
    if (rc.getLocation().distanceSquaredTo(newKingPos) <= 2) {
        Direction dir = rc.getLocation().directionTo(newKingPos);
        if (rc.canMove(dir)) {
            Vision::turn(dir);
            rc.move(dir);
        }
        return;
    }
    if (!targetPos.isNull() && rc.canSenseRobotAtLocation(targetPos)) {
        targetPos = MapLocation::NONE;
    }
    if (targetPos.isNull() && rc.getLocation().distanceSquaredTo(newKingPos) <= 8) {
        Vision::turn(rc.getLocation().directionTo(newKingPos));
        MapLocation pos = newKingPos;
        if (!rc.canSenseRobotAtLocation(pos)) {
            targetPos = pos;
            BugNavigator::moveTo(targetPos, true);
            return;
        }
        pos = newKingPos.add(newKingPos.directionTo(rc.getLocation()));
        if (!rc.canSenseRobotAtLocation(pos)) {
            targetPos = pos;
            BugNavigator::moveTo(targetPos, true);
            return;
        }
        pos = newKingPos.add(newKingPos.directionTo(rc.getLocation()).rotateLeft());
        if (!rc.canSenseRobotAtLocation(pos)) {
            targetPos = pos;
            BugNavigator::moveTo(targetPos, true);
            return;
        }
        pos = newKingPos.add(newKingPos.directionTo(rc.getLocation()).rotateRight());
        if (!rc.canSenseRobotAtLocation(pos)) {
            targetPos = pos;
            BugNavigator::moveTo(targetPos, true);
            return;
        }
        pos = newKingPos.add(newKingPos.directionTo(rc.getLocation()).rotateLeft().rotateLeft());
        if (!rc.canSenseRobotAtLocation(pos)) {
            targetPos = pos;
            BugNavigator::moveTo(targetPos, true);
            return;
        }
        pos = newKingPos.add(newKingPos.directionTo(rc.getLocation()).rotateRight().rotateRight());
        if (!rc.canSenseRobotAtLocation(pos)) {
            targetPos = pos;
            BugNavigator::moveTo(targetPos, true);
            return;
        }
        pos = newKingPos.add(newKingPos.directionTo(rc.getLocation()).opposite().rotateRight());
        if (!rc.canSenseRobotAtLocation(pos)) {
            targetPos = pos;
            BugNavigator::moveTo(targetPos, true);
            return;
        }
        pos = newKingPos.add(newKingPos.directionTo(rc.getLocation()).opposite().rotateLeft());
        if (!rc.canSenseRobotAtLocation(pos)) {
            targetPos = pos;
            BugNavigator::moveTo(targetPos, true);
            return;
        }
        pos = newKingPos.add(newKingPos.directionTo(rc.getLocation()).opposite());
        if (!rc.canSenseRobotAtLocation(pos)) {
            targetPos = pos;
            BugNavigator::moveTo(targetPos, true);
            return;
        }
        return;
    }
    if (targetPos.isNull()) {
        Navigator::moveTo(newKingPos, true);
        return;
    }
    BugNavigator::moveTo(targetPos, true);
}


void Multiking::run() {
    for (const MapLocation& ml : kingPos) {
        if (ml.isNull()) break;
        if (ml.distanceSquaredTo(newKingPos) <= closeToKing) {
            Baby::isNewKing = false;
            return;
        }
    }
    rc.setIndicatorString(newKingPos.toString());
    moveTo();
    if (rc.getLocation().distanceSquaredTo(newKingPos) <= 8) {
        roundsCircled++;
        Comms::squeakForSacrifices(newKingPos);
    }
    if (rc.getLocation().distanceSquaredTo(newKingPos) <= 8 && rc.canBecomeRatKing()) {
        rc.becomeRatKing();
        King::run();
        return;
    }
    if (roundsCircled >= giveUpNewKing) {
        Baby::isNewKing = false;
    }
}

}  // namespace Roles
