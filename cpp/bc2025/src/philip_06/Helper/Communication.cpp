#include "Helper/Communication.hpp"

namespace philip_06 {
namespace Helper {

int Communication::encode(RobotController rc, int pri, MapLocation ML, int msg) {
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
    message += rc.getRoundNum();
    message = (message << 3);
    // What message
    message += msg;
    return message;
}

vector<int> Communication::decode(int message) {
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

}  // namespace Helper
}  // namespace philip_06
