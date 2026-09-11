#include "Helper/Comms.hpp"
#include "RobotPlayer.hpp"
#include "Soldier.hpp"
#include "SoldierState/Build.hpp"
#include "utils/Actions.hpp"
#include "roles/Mopper.hpp"
#include "roles/Splasher.hpp"
#include "roles/Tower.hpp"
#include <iostream>
#include <utility>

namespace philip_06 {
namespace Helper {

MapLocation Comms::needMopperHelp;  // Java: = null
int Comms::turnLastSeen = -1000;

int Comms::encode(RobotController rc, int pri, MapLocation ML, int roundNum, int msg) {
    int message = 0;
    // UnitType 0: tower, 1: soldier, 2: mopper, 3: splasher
    if (rc.getType() == UnitType::SOLDIER) message = 1;
    else if (rc.getType() == UnitType::MOPPER) message = 2;
    else if (rc.getType() == UnitType::SPLASHER) message = 3;
    message = (message << 3);
    // Priority
    message += pri;
    message = (message << 6);
    // Map Location
    message += ML.x;
    message = (message << 6);
    message += ML.y;
    message = (message << 11);
    // Which round
    message += roundNum;
    message = (message << 3);
    // What message
    message += msg;
    return message;
}

vector<int> Comms::decode(int message) {
    vector<int> ans(6);
    ans[5] = message % (1 << 3);
    message = (message >> 3);
    ans[4] = message % (1 << 11);
    message = (message >> 11);
    ans[3] = message % (1 << 6);
    message = (message >> 6);
    ans[2] = message % (1 << 6);
    message = (message >> 6);
    ans[1] = message % (1 << 3);
    message = (message >> 3);
    ans[0] = message;
    // Returns an array containing:
    // {Unit Type, Priority, Map Location, Round info, Message}
    return ans;
}

void Comms::getMsg(RobotController rc) {
    if (isRobotType(rc.getType())) {
        if (rc.getType() == UnitType::MOPPER) {
            for (const Message& msg : rc.readMessages(rc.getRoundNum() - 1)) {
                if (decodeLocation(msg.getBytes()) == MapLocation(61, 61)) continue;
                roles::Mopper::orderedTo = decodeLocation(msg.getBytes());
            }
            return;
        }
        for (const Message& msg : rc.readMessages(rc.getRoundNum() - 1)) {
            if (msg.getBytes() >> 30 == 1) RobotPlayer::lastSeenEnemy = 0;
            if (decodeLocation(msg.getBytes()) == MapLocation(61, 61)) continue;
            std::cout << decodeLocation(msg.getBytes()).toString() << '\n';
            Soldier::attack = decodeLocation(msg.getBytes());
            roles::Splasher::destination = decodeLocation(msg.getBytes());
        }
    } else {
        for (const Message& msg : rc.readMessages(rc.getRoundNum() - 1)) {
            int val = msg.getBytes();
            if (val >> 30 != 0) {
                needMopperHelp = decodeLocation(val);
                turnLastSeen = (val >> 12) % (1 << 12);
                roles::Tower::toSpawn.clear();
                roles::Tower::toSpawn.push_back(
                    std::make_pair(UnitType::MOPPER, needMopperHelp));
                //std::cout << "Need mopper help at " << needMopperHelp.toString() << '\n';
                continue;
            }
            if ((val >> 12) % 2 == 0)
                utils::Actions::spawn(rc, UnitType::MOPPER, decodeLocation(val));
            else {
                if (decodeLocation(val) == MapLocation(61, 61)) continue;
                RobotPlayer::lastSeenEnemy = rc.getRoundNum();
                roles::Tower::target = decodeLocation(val);
                roles::Tower::targetRound = rc.getRoundNum();
                rc.setIndicatorLine(rc.getLocation(), decodeLocation(val), 0, 0, 0);
                roles::Tower::toSpawn.push_back(
                    std::make_pair(UnitType::SOLDIER, decodeLocation(val)));
                roles::Tower::toSpawn.push_back(
                    std::make_pair(UnitType::SOLDIER, decodeLocation(val)));
            }
            if (val >> 13 % 2 == 0 && rc.canBroadcastMessage())
                rc.broadcastMessage(val + (1 << 13));
        }
    }
}

void Comms::sendMsg(RobotController rc) {
    if (isTowerType(rc.getType())) {
        if (!needMopperHelp.isNull() &&
            rc.getRoundNum() - turnLastSeen <= (rc.getMapHeight() + rc.getMapWidth()) / 5) {
            for (const RobotInfo& ri : rc.senseNearbyRobots(-1, rc.getTeam())) {
                if (ri.type == UnitType::MOPPER) {
                    if (rc.canSendMessage(ri.location)) {
                        rc.sendMessage(ri.location, encodeLocation(needMopperHelp));
                        //std::cout << "Send message " << needMopperHelp.toString()
                        //          << " to " << ri.location.toString() << '\n';
                    }
                }
            }
        }
        return;
    }
    if (!SoldierState::Build::enemyPaintCell.isNull() &&
        (rc.getRoundNum() - SoldierState::Build::turnEnemyPaintCell <=
             (rc.getMapWidth() + rc.getMapHeight()) / 7 ||
         SoldierState::Build::askForMopper)) {
        for (const RobotInfo& ri : rc.senseNearbyRobots(-1, rc.getTeam())) {
            if (isTowerType(ri.getType())) {
                if (rc.canSendMessage(ri.getLocation())) {
                    rc.sendMessage(ri.getLocation(),
                                   encodeReport(SoldierState::Build::enemyPaintCell,
                                                SoldierState::Build::turnEnemyPaintCell +
                                                    (1 << 18)));
                    SoldierState::Build::enemyPaintCell = MapLocation::NONE;
                    SoldierState::Build::askForMopper = false;
                    return;
                    /// + (1<<19) so the 30th bit is set
                    // encode the location, then the turn the location was last
                    // seen to be disrupting
                }
            }
        }
    }
    if (!RobotPlayer::lastEnemyTower.isNull()) {
        for (const MapLocation& loc : rc.senseNearbyRuins(-1)) {
            // RobotInfo has no NONE sentinel in api.hpp; a default RobotInfo's
            // location is MapLocation::NONE, used here as the null proxy.
            if (!rc.senseRobotAtLocation(loc).getLocation().isNull() &&
                rc.senseRobotAtLocation(loc).getTeam() == rc.getTeam()) {
                if (rc.canSendMessage(loc)) {
                    rc.sendMessage(loc, encodeReport(RobotPlayer::lastEnemyTower, 1));
                    RobotPlayer::lastEnemyTower = MapLocation::NONE;
                    return;
                }
            }
        }
    }
}

}  // namespace Helper
}  // namespace philip_06
