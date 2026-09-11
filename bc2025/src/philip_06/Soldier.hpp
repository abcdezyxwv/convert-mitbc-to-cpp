#pragma once
#include "api.hpp"
#include <unordered_set>

namespace philip_06 {

struct Soldier {
    static bool builder;
    static int turnsAlive;
    static MapLocation spawn;
    static std::unordered_set<MapLocation> paintTowers;
    static vector<MapLocation> ruins;
    static bool messenger;
    static MapLocation messageLoc;
    static int priority, roundNum;
    static int message;
    static int moneyLastTurn;
    static bool defaultFill;
    static MapLocation attack;

    static bool onMap(RobotController rc, MapLocation curr) {
        return curr.x >= 0 && curr.x < rc.getMapWidth() && curr.y >= 0 &&
               curr.y < rc.getMapHeight();
    }
    static int scale(int value, int originalMin, int originalMax, int targetMin,
                     int targetMax) {
        return (int)std::lround(targetMin + (double)(value - originalMin) *
                                                (targetMax - targetMin) /
                                                (originalMax - originalMin));
    }


    static void retreat(RobotController rc);
    static void stealPaint(RobotController rc);   // package-private in Java
    static void donatePaint(RobotController rc);  // package-private in Java
    static void run(RobotController rc);
};

}  // namespace philip_06
