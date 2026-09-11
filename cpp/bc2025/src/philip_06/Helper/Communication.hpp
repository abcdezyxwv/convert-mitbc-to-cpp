#pragma once
#include "api.hpp"

namespace philip_06 {
namespace Helper {

struct Communication {
    static int encode(RobotController rc, int pri, MapLocation ML, int msg);
    static vector<int> decode(int message);
};

}  // namespace Helper
}  // namespace philip_06
