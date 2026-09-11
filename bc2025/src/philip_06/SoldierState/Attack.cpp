#include "SoldierState/Attack.hpp"

#include "RobotPlayer.hpp"
#include "roles/Mopper.hpp"
#include "roles/Splasher.hpp"

namespace philip_06 {
namespace SoldierState {

using roles::Mopper;

const Direction Attack::directions[8] = {
    Direction::all[Direction::NORTH],
    Direction::all[Direction::NORTHEAST],
    Direction::all[Direction::EAST],
    Direction::all[Direction::SOUTHEAST],
    Direction::all[Direction::SOUTH],
    Direction::all[Direction::SOUTHWEST],
    Direction::all[Direction::WEST],
    Direction::all[Direction::NORTHWEST],
};

MapLocation Attack::target;  // Java: null
MapLocation Attack::next;    // Java: null
bool Attack::found = false;

void Attack::run(RobotController rc) {
    // Check if there are any close ones
    vector<MapLocation> ruins = rc.senseNearbyRuins(-1);
    for (const MapLocation& ruin : ruins) {
        RobotInfo robot = rc.senseRobotAtLocation(ruin);
        if (!robot.location.isNull() && robot.getTeam() != rc.getTeam() && !(ruin == target)) {
            if (ruin == next) {
                target = next;
                next = ruin;
                break;
            }
            if (found) {
                next = ruin;
            } else {
                found = true;
                target = ruin;
            }
            break;
        }
    }

    if (target.isNull()) target = roles::Splasher::getNextCorner(rc);
    if (rc.canSenseLocation(target) && (rc.senseRobotAtLocation(target).location.isNull() ||
                                        rc.senseRobotAtLocation(target).getTeam() == rc.getTeam())) {
        target = next;
        next = MapLocation::NONE;
    }
    if (target.isNull()) {
        RobotPlayer::rush = false;
        RobotPlayer::fill = true;
        RobotPlayer::build = false;
        target = roles::Splasher::getNextCorner(rc);
    }

    // Begin kiting
    if (rc.getLocation().isWithinDistanceSquared(target, 20)) {
        if (rc.senseRobotAtLocation(target).location.isNull()) {
            // Destroyed building
            if (!next.isNull()) {
                target = next;
                next = MapLocation::NONE;
                found = true;
            } else {
                found = false;
                RobotPlayer::rush = false;
                RobotPlayer::fill = true;
                RobotPlayer::build = false;
                target = roles::Splasher::getNextCorner(rc);
            }
        } else {
            // Kiting
            if (rc.getLocation().isWithinDistanceSquared(target, 9)) {
                if (rc.canAttack(target)) rc.attack(target);
                Direction dir = rc.getLocation().directionTo(target);
                for (int i = 0; i < 4; i++) {
                    if (rc.canMove(dir.opposite())) rc.move(dir.opposite());
                    dir = dir.rotateLeft();
                }
            } else if (rc.isActionReady()) {
                if (rc.canMove(rc.getLocation().directionTo(target)))
                    rc.move(rc.getLocation().directionTo(target));
                else
                    Mopper::moveTowardsMindlessly(rc, target);
                if (rc.canAttack(target)) rc.attack(target);
            }
        }
    } else {
        Mopper::moveTowardsMindlessly(rc, target);
    }
}

}  // namespace SoldierState
}  // namespace philip_06
