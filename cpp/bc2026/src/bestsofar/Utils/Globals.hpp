#pragma once
#include "api.hpp"
#include "Utils/AdditionalClasses/Threat.hpp"
#include "Utils/AdditionalClasses/Thrown.hpp"

namespace Utils {

struct Globals {
    static RobotController rc;

    static constexpr int trapGlobalCheeseThreshold = 250;
    static constexpr int safeCheeseReserve = 600;
    static constexpr int emergencyReserve = 250;
    static constexpr int catSpacing = 4;
    static constexpr int ratSpacing = 2;
    static constexpr int pacifistRounds = 200;
    static constexpr int help1Health = 250;
    static constexpr int help1Enemies = 3;
    static constexpr int help2Health = 100;
    static constexpr int help2Enemies = 2;
    static constexpr int endgame = 1960;
    static constexpr int midgame = 300;
    static constexpr int cheeseThreshold = 50;
    static constexpr int minNumberRats = 12;
    static constexpr int maxNumberRats = 16;
    static constexpr int minCheese = 110;
    static constexpr int doSpawnThreshold = 2500;
    static constexpr int attackerNumber = 2;
    static constexpr int useTrapCheeseThreshold = 500;
    static constexpr int globalCheeseTrapSubstitute = 40;
    static constexpr double secondBestMoveChance = 0.2;
    static constexpr int disintegrationHP = 10;
    static constexpr int minerReturnThreshold = 40;
    static constexpr int maxCheese = 200;
    static constexpr int minerSecondaryReturnThreshold = 20;
    static constexpr int secondaryReturnDistance = 200;
    static constexpr int newKingCheeseThreshold = 200;
    static constexpr int newKingSquaresThreshold = 5;
    static constexpr int newKingSpawnThreshold = 1200;
    static constexpr int botsForNewKing = 9;
    static constexpr int giveUpNewKing = 25;
    static constexpr int closeToKing = 100;

    static Random rng;
    static const vector<Direction> directions;  // NORTH..NORTHWEST, CENTER

    static vector<MapInfo> surroundings;
    static vector<RobotInfo> allyRobots;
    static vector<RobotInfo> enemyRobots;
    static vector<RobotInfo> catRobots;
    static vector<RobotInfo> catsLastTurn;
    static MapLocation kingPos[5];  // Java null slot -> MapLocation::NONE
    static MapLocation catLoc;
    static vector<Message> newestSqueaks;
    static vector<AdditionalClasses::Thrown> alliesThrown;
    static MapLocation closestKing;
    static RobotInfo closestEnemy;
    static MapLocation closestEnemyKing;
    static int squeaksReadLastRound;
    static MapLocation locationLastRound;
    static vector<RobotInfo> moreAllies;  // Java: ArrayList<RobotInfo>

    static int symmetry;
    static bool hasSqueaked;
    static bool enemiesLastRound;
    static bool cantTurn;
    static bool cantMove;

    static int mapWidth;
    static int mapHeight;
    static int spawnRound;

    static int internalRoundNum;
    static int myId;
    static Team myTeam;
    static Team opponentTeam;
    static vector<AdditionalClasses::Threat> threats;
    static vector<Direction> allDirections;  // Java: Direction.values()
    static vector<Direction> adjacentDirections;

    static void init(RobotController robotController);

    static vector<Message> lastRound, thisRound;

    static void startTurn();
    static void endTurn();
    static void debugBytecode(string tag, int interval);
    static void debug(string str, int interval);
    static int approxNumberBabies();
    static vector<MapLocation> getRobotLocations(MapLocation loc, UnitType type);
    static MapLocation closestOnMap(MapLocation ml);
    static bool isWithinVision(MapLocation robotLocation, Direction robotDirection,
                               MapLocation location, int visionRadiusSquared);
    static MapLocation mapLocationAddNoise(MapLocation ml, int maxDist);
    static void dontTurn();
    static void dontMove();
    static void pickUpCheese(MapLocation ml);
};

// api.hpp's RobotInfo has no NONE/isNull sentinel. Java `info == null` /
// `info != null` on a RobotInfo is written `isNullRobot(info)` /
// `!isNullRobot(info)`: a default-constructed RobotInfo has a null location,
// while every real or bot-constructed RobotInfo gets a real one.
inline bool isNullRobot(const RobotInfo& r) { return r.location.isNull(); }

}  // namespace Utils
