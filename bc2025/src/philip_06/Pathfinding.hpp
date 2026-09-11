#pragma once
#include "api.hpp"

namespace philip_06 {

// Mixed static/instance class: Constants::pathfind holds an instance,
// but most members are static in the Java source.
struct Pathfinding {
    Direction exploreDirection;          // instance field (Java: = null)

    static MapLocation dest;
    static MapLocation destination;
    static int TurnsWasted;

    static void setDest(RobotController rc, MapLocation loc);
    static void makeMove(RobotController rc);
    static void move(RobotController rc, MapLocation loc);

    void explore(RobotController rc);    // instance methods in Java
    void rush(RobotController rc);
    void turtle(RobotController rc);
    void retreat(RobotController rc);

    static bool canMoveFriendly(RobotController rc, Direction dir);
    static void wander(RobotController rc);
    static MapInfo findClosestAllyCell(RobotController rc);
    static MapInfo findFurthestAllyCell(RobotController rc);
    static MapInfo findClosestEnemyCell(RobotController rc);
    static MapInfo findFurthestEnemyCell(RobotController rc);
};

}  // namespace philip_06
