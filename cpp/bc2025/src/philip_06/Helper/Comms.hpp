#pragma once
#include "api.hpp"

namespace philip_06 {
namespace Helper {

struct Comms {
    static int encode(RobotController rc, int pri, MapLocation ML, int roundNum, int msg);
    static vector<int> decode(int message);
    static int encodeLocation(MapLocation loc) { return (loc.x << 6) + loc.y; }
    static MapLocation decodeLocation(int k) { return MapLocation((k >> 6) % 64, k % 64); }
    static int encodeReport(MapLocation loc, int type) {
        /* types:
           0: Spawn Mopper to go to (x,y) (mainly to cleanup paint ruining ruins)
           1: Attack (x,y), spawn an army of bots to the location */
        return (loc.x << 6) + loc.y + (type << 12);
    }

    static MapLocation needMopperHelp;
    static int turnLastSeen;

    static void getMsg(RobotController rc);
    static void sendMsg(RobotController rc);
};

}  // namespace Helper
}  // namespace philip_06
