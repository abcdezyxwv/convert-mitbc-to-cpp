#pragma once
#include "api.hpp"

namespace philip_06 {
namespace SoldierState {

struct Build {
    static MapLocation dest, destination;
    static bool found, built;

    static int lastStuck, turnsWasted, moneyLastTurn;
    static vector<MapLocation> toFinish;   // ArrayList: getLast()->back(), removeLast()->pop_back()
    static vector<int> turnAdded;
    static bool movingTowardsToFinish;
    static MapLocation enemyPaintCell, halfBuilt;
    static int turnEnemyPaintCell;
    static bool askForMopper;
    static MapLocation wontBegForMore;

    static void run(RobotController rc);
};

}  // namespace SoldierState
}  // namespace philip_06
