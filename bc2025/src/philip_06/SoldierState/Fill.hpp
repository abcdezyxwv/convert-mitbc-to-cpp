#pragma once
#include "api.hpp"

namespace philip_06 {
namespace SoldierState {

struct Fill {
    // Java: public static class Move
    struct Move {
        static Direction edge;
        static MapLocation vertexA;
        static MapLocation vertexB;
        static int roundsExploring;

        static bool stuck;
        static bool moveRight;
        static vector<MapLocation> pastLocs;

        static void init(RobotController rc);
        static void explore(RobotController rc);
    };

    static const Direction directions[8];

    static vector<MapInfo> marked;
    static bool colours[9][9];  // Java reassigns `new boolean[9][9]` -> memset in .cpp

    static bool getCacheCol(RobotController rc, MapLocation curr) {
        return colours[rc.getLocation().x - curr.x + 4][rc.getLocation().y - curr.y + 4];
    }
    static PaintType getCachePaint(RobotController rc, MapLocation curr) {
        if (colours[rc.getLocation().x - curr.x + 4][rc.getLocation().y - curr.y + 4])
            return PaintType::ALLY_SECONDARY;
        return PaintType::ALLY_PRIMARY;
    }
    static bool isCorrect(RobotController rc, MapLocation mp);
    static void attack(RobotController rc, MapLocation mp);
    static bool interfere(RobotController rc, MapLocation mp);

    static MapLocation dest;

    static void run(RobotController rc);
};

}  // namespace SoldierState
}  // namespace philip_06
