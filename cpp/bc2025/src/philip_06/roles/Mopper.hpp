#pragma once
#include "api.hpp"
#include <unordered_map>

// std::hash<Direction> is needed for directionsOrder (Java HashMap<Direction,Integer>)
// but is not provided by api.hpp (which only specialises hash<MapLocation>).
namespace std {
template <>
struct hash<Direction> {
    size_t operator()(const Direction& d) const { return (size_t)d.ordinal(); }
};
}  // namespace std

namespace philip_06 {
namespace roles {

struct Mopper {
    static const Direction directions[8];
    static std::unordered_map<Direction, int> directionsOrder;

    enum class State { NICE, BULLY, CONFUSED };
    static State mood;

    static void shuffleArray(vector<MapInfo>& array);  // private in Java

    static MapLocation destination;
    static int TurnsWasted;
    static bool canMoveMopper(RobotController rc, Direction dir);
    static void wander(RobotController rc);

    static MapLocation randomDestination;
    static bool explore(RobotController rc);
    static void resetDest(RobotController rc);

    static bool moveRight, stuck;
    static vector<MapLocation> pastLocs;
    static bool noBacktrack(RobotController rc, Direction dir);
    static bool moveTowardsMindlessly(RobotController rc, MapLocation loc);

    static int lastRefresh;
    static bool social[8];
    static void refresh(RobotController rc);

    // Java has BOTH a method `RobotInfo closestEnemyTower(RobotController)`
    // (line 456) and a field `MapLocation closestEnemyTower` (line 1219) in the
    // same class - legal in Java, not in C++. The METHOD is renamed to
    // closestEnemyTowerInfo; the FIELD keeps the original name.
    static RobotInfo closestEnemyTowerInfo(RobotController rc);
    static MapLocation closestEnemyTower;

    static bool moveTowardsMindfully(RobotController rc, MapLocation loc);

    static MapLocation enemyCell, allyCell;
    static void findEnemyCell(RobotController rc);
    static void findAnyAllyCell(RobotController rc);
    static void findAllyCell(RobotController rc);
    static bool cleanUpSomePaint(RobotController rc, MapLocation loc);
    static bool paintEnemyCell(RobotController rc);
    static void donatePaint(RobotController rc);
    static void stealPaint(RobotController rc);
    static void move(RobotController rc);

    static MapLocation orderedTo;
    static void followOrders(RobotController rc);
    static void doStuff(RobotController rc);

    static MapLocation victim;
    static void findClosestVictim(RobotController rc);
    static bool attackVictim(RobotController rc);
    static void beBully(RobotController rc);

    static int paint(MapInfo loc);

    static void run(RobotController rc);
};

}  // namespace roles
}  // namespace philip_06
