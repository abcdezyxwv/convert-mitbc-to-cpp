#pragma once
#include "api.hpp"
#include <unordered_map>

namespace philip_06 {
namespace utils {

struct Actions {
    static bool spawn(RobotController rc, UnitType type, MapLocation dest);
    static std::unordered_map<MapLocation, int> badRuins;
    static void makeTower(RobotController rc, MapLocation ruin);
    static void getPaint(RobotController rc);
};

}  // namespace utils
}  // namespace philip_06
