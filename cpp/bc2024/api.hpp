// Minimal C++ shim of the Battlecode 2024 (battlecode.common) API surface.
// Engine-facing calls are declarations only - there is no C++ engine; value
// types are fully implemented so bot logic is preserved exactly.
#pragma once

#include <array>
#include <cmath>
#include <cstdint>
#include <functional>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

using std::string;
using std::vector;

// ---------------------------------------------------------------------------
// Small fast PRNG used in place of java.util.Random
// ---------------------------------------------------------------------------
struct Random {
    uint64_t s;
    explicit Random(int64_t seed = 0)
        : s(seed ? (uint64_t)seed * 0x9E3779B97F4A7C15ull : 0x243F6A8885A308D3ull) {}
    uint32_t next() {
        s ^= s << 13;
        s ^= s >> 7;
        s ^= s << 17;
        return (uint32_t)s;
    }
    int nextInt(int bound) { return (int)(next() % (uint32_t)bound); }
    int nextInt() { return (int)next(); }
    double nextDouble() { return next() / 4294967296.0; }
};

inline int signum(int x) { return (x > 0) - (x < 0); }

// ---------------------------------------------------------------------------
// Enums
// ---------------------------------------------------------------------------
enum class Team { A, B, NEUTRAL };
inline Team opponent(Team t) {
    return t == Team::A ? Team::B : (t == Team::B ? Team::A : Team::NEUTRAL);
}

enum class TrapType { EXPLOSIVE, WATER, STUN, NONE };
enum class SkillType { ATTACK, BUILD, HEAL };
enum class GlobalUpgrade { ATTACK, HEALING, CAPTURING, ACTION };

enum class GameActionExceptionType {
    INTERNAL_ERROR, NOT_ENOUGH_RESOURCE, CANT_MOVE_THERE, IS_NOT_READY,
    CANT_SENSE_THAT, OUT_OF_RANGE, CANT_DO_THAT, NO_ROBOT_THERE
};

class GameActionException : public std::exception {
public:
    GameActionExceptionType type;
    string message;
    GameActionException(GameActionExceptionType type = GameActionExceptionType::INTERNAL_ERROR,
                        const string& message = "")
        : type(type), message(message) {}
    GameActionExceptionType getType() const { return type; }
    const char* what() const noexcept override { return message.c_str(); }
};

// ---------------------------------------------------------------------------
// Direction - keeps dx/dy fields and member helpers like the Java enum
// ---------------------------------------------------------------------------
struct Direction {
    enum E : int8_t { NORTH, NORTHEAST, EAST, SOUTHEAST, SOUTH, SOUTHWEST, WEST, NORTHWEST, CENTER };
    E e;
    int dx, dy;
    constexpr Direction(E e = CENTER, int dx = 0, int dy = 0) : e(e), dx(dx), dy(dy) {}

    int ordinal() const { return (int)e; }
    int getDeltaX() const { return dx; }
    int getDeltaY() const { return dy; }
    Direction opposite() const {
        if (e >= CENTER) return *this;
        return all[(e + 4) % 8];
    }
    Direction rotateLeft() const {
        if (e >= CENTER) return *this;
        return all[(e + 7) % 8];
    }
    Direction rotateRight() const {
        if (e >= CENTER) return *this;
        return all[(e + 1) % 8];
    }

    bool operator==(const Direction& o) const { return e == o.e; }
    bool operator!=(const Direction& o) const { return e != o.e; }

    static const Direction all[9];
    static std::vector<Direction> allDirections() { return {all, all + 9}; }
    static std::vector<Direction> cardinalDirections() {
        return {all[NORTH], all[EAST], all[SOUTH], all[WEST]};
    }
};

inline const Direction Direction::all[9] = {
    Direction(Direction::NORTH, 0, 1),      Direction(Direction::NORTHEAST, 1, 1),
    Direction(Direction::EAST, 1, 0),       Direction(Direction::SOUTHEAST, 1, -1),
    Direction(Direction::SOUTH, 0, -1),     Direction(Direction::SOUTHWEST, -1, -1),
    Direction(Direction::WEST, -1, 0),      Direction(Direction::NORTHWEST, -1, 1),
    Direction(Direction::CENTER, 0, 0),
};

// ---------------------------------------------------------------------------
// MapLocation - default-constructed value is the Java `null` sentinel
// ---------------------------------------------------------------------------
struct MapLocation {
    static constexpr int kNull = -1000000;
    int x, y;
    constexpr MapLocation() : x(kNull), y(kNull) {}
    constexpr MapLocation(int x, int y) : x(x), y(y) {}

    bool isNull() const { return x == kNull; }
    static const MapLocation NONE;

    int distanceSquaredTo(MapLocation l) const {
        int dx = l.x - x, dy = l.y - y;
        return dx * dx + dy * dy;
    }
    bool isWithinDistanceSquared(MapLocation l, int r2) const {
        return distanceSquaredTo(l) <= r2;
    }
    bool isAdjacentTo(MapLocation l) const {
        int dx = l.x - x, dy = l.y - y;
        return dx * dx <= 2 && dy * dy <= 2 && !(dx == 0 && dy == 0);
    }
    Direction directionTo(MapLocation l) const {
        double dx = l.x - x, dy = l.y - y;
        using E = Direction::E;
        if (std::abs(dx) >= 2.414 * std::abs(dy)) {
            if (dx > 0) return Direction::all[E::EAST];
            if (dx < 0) return Direction::all[E::WEST];
            return Direction::all[E::CENTER];
        }
        if (std::abs(dy) >= 2.414 * std::abs(dx)) {
            return Direction::all[dy > 0 ? E::NORTH : E::SOUTH];
        }
        if (dy > 0) return Direction::all[dx > 0 ? E::NORTHEAST : E::NORTHWEST];
        return Direction::all[dx > 0 ? E::SOUTHEAST : E::SOUTHWEST];
    }
    MapLocation add(Direction d) const { return {x + d.dx, y + d.dy}; }
    MapLocation subtract(Direction d) const { return {x - d.dx, y - d.dy}; }
    MapLocation translate(int dx, int dy) const { return {x + dx, y + dy}; }

    bool operator==(const MapLocation& o) const { return x == o.x && y == o.y; }
    bool operator!=(const MapLocation& o) const { return !(*this == o); }
    string toString() const { return "(" + std::to_string(x) + ", " + std::to_string(y) + ")"; }
};
inline const MapLocation MapLocation::NONE{};

namespace std {
template <> struct hash<MapLocation> {
    size_t operator()(const MapLocation& l) const { return (size_t)l.x * 1000003u + (size_t)l.y; }
};
}  // namespace std

// ---------------------------------------------------------------------------
// Info objects
// ---------------------------------------------------------------------------
struct RobotInfo {
    int ID = 0;
    Team team = Team::NEUTRAL;
    int health = 0;
    MapLocation location;
    bool hasFlag = false;
    int attackLevel = 0, healLevel = 0, buildLevel = 0;

    int getID() const { return ID; }
    Team getTeam() const { return team; }
    int getHealth() const { return health; }
    MapLocation getLocation() const { return location; }
    bool getHasFlag() const { return hasFlag; }
    int getAttackLevel() const { return attackLevel; }
    int getHealLevel() const { return healLevel; }
    int getBuildLevel() const { return buildLevel; }
};

struct MapInfo {
    MapLocation loc;
    bool passable = false, wall = false, dam = false, water = false;
    int spawnZone = 0;
    int crumbsAmount = 0;
    TrapType trapType = TrapType::NONE;
    Team territory = Team::NEUTRAL;

    bool isPassable() const { return passable; }
    bool isWall() const { return wall; }
    bool isDam() const { return dam; }
    bool isSpawnZone() const { return spawnZone != 0; }
    int getSpawnZoneTeam() const { return spawnZone; }
    bool isWater() const { return water; }
    int getCrumbs() const { return crumbsAmount; }
    TrapType getTrapType() const { return trapType; }
    MapLocation getMapLocation() const { return loc; }
    Team getTeamTerritory() const { return territory; }
};

struct FlagInfo {
    MapLocation loc;
    Team team = Team::NEUTRAL;
    bool pickedUp = false;
    int id = 0;
    MapLocation getLocation() const { return loc; }
    Team getTeam() const { return team; }
    bool isPickedUp() const { return pickedUp; }
    int getID() const { return id; }
};

// ---------------------------------------------------------------------------
// Constants / Clock
// ---------------------------------------------------------------------------
struct GameConstants {
    static constexpr int MAP_MIN_HEIGHT = 20, MAP_MAX_HEIGHT = 60;
    static constexpr int MAP_MIN_WIDTH = 20, MAP_MAX_WIDTH = 60;
    static constexpr int MIN_FLAG_SPACING_SQUARED = 36;
    static constexpr int GAME_MAX_NUMBER_OF_ROUNDS = 2000;
    static constexpr int BYTECODE_LIMIT = 25000;
    static constexpr int SHARED_ARRAY_LENGTH = 64;
    static constexpr int MAX_SHARED_ARRAY_VALUE = (1 << 16) - 1;
    static constexpr int DEFAULT_HEALTH = 1000;
    static constexpr int ROBOT_CAPACITY = 50;
    static constexpr int NUMBER_FLAGS = 3;
    static constexpr int DIG_COST = 20, FILL_COST = 30;
    static constexpr int FLAG_BROADCAST_UPDATE_INTERVAL = 100;
    static constexpr int FLAG_BROADCAST_NOISE_RADIUS = 100;
    static constexpr int FLAG_DROPPED_RESET_ROUNDS = 4;
    static constexpr int INITIAL_CRUMBS_AMOUNT = 400;
    static constexpr int PASSIVE_CRUMBS_INCREASE = 10;
    static constexpr int KILL_CRUMB_REWARD = 30;
    static constexpr int SETUP_ROUNDS = 200;
    static constexpr int GLOBAL_UPGRADE_ROUNDS = 600;
    static constexpr int JAILED_ROUNDS = 25;
    static constexpr int VISION_RADIUS_SQUARED = 20;
    static constexpr int ATTACK_RADIUS_SQUARED = 4;
    static constexpr int HEAL_RADIUS_SQUARED = 4;
    static constexpr int INTERACT_RADIUS_SQUARED = 2;
    static constexpr int COOLDOWN_LIMIT = 10;
    static constexpr int COOLDOWNS_PER_TURN = 10;
    static constexpr int MOVEMENT_COOLDOWN = 10;
    static constexpr int FLAG_MOVEMENT_COOLDOWN = 20;
    static constexpr int PICKUP_DROP_COOLDOWN = 10;
    static constexpr int ATTACK_COOLDOWN = 20;
    static constexpr int HEAL_COOLDOWN = 30;
};

struct Clock {
    static void yield();
    static int getBytecodesLeft();
    static int getBytecodeNum();
};

// ---------------------------------------------------------------------------
// RobotController - declarations only (implemented by the Java engine)
// ---------------------------------------------------------------------------
class RobotController {
public:
    int getRoundNum();
    int getMapWidth();
    int getMapHeight();
    int getID();
    Team getTeam();
    MapLocation getLocation();
    int getHealth();
    int getExperience(SkillType skill);
    int getLevel(SkillType skill);
    int getCrumbs();
    bool onTheMap(MapLocation loc);
    bool canSenseLocation(MapLocation loc);
    bool isLocationOccupied(MapLocation loc);
    bool canSenseRobotAtLocation(MapLocation loc);
    RobotInfo senseRobotAtLocation(MapLocation loc);
    bool canSenseRobot(int id);
    RobotInfo senseRobot(int id);
    vector<RobotInfo> senseNearbyRobots();
    vector<RobotInfo> senseNearbyRobots(int radiusSquared);
    vector<RobotInfo> senseNearbyRobots(int radiusSquared, Team team);
    vector<RobotInfo> senseNearbyRobots(MapLocation center, int radiusSquared, Team team);
    vector<MapLocation> senseNearbyCrumbs(int radiusSquared);
    bool sensePassability(MapLocation loc);
    MapInfo senseMapInfo(MapLocation loc);
    vector<MapInfo> senseNearbyMapInfos();
    vector<MapInfo> senseNearbyMapInfos(int radiusSquared);
    vector<MapInfo> senseNearbyMapInfos(MapLocation center);
    vector<MapInfo> senseNearbyMapInfos(MapLocation center, int radiusSquared);
    vector<FlagInfo> senseNearbyFlags(int radiusSquared);
    vector<FlagInfo> senseNearbyFlags(int radiusSquared, Team team);
    vector<MapLocation> senseBroadcastFlagLocations();
    bool senseLegalStartingFlagPlacement(MapLocation loc);
    MapLocation adjacentLocation(Direction dir);
    vector<MapLocation> getAllLocationsWithinRadiusSquared(MapLocation center, int radiusSquared);
    bool isSpawned();
    bool isActionReady();
    int getActionCooldownTurns();
    bool isMovementReady();
    int getMovementCooldownTurns();
    bool canMove(Direction dir);
    void move(Direction dir);
    bool canBuild(TrapType building, MapLocation loc);
    void build(TrapType building, MapLocation loc);
    bool canDig(MapLocation loc);
    void dig(MapLocation loc);
    bool canFill(MapLocation loc);
    void fill(MapLocation loc);
    bool canAttack(MapLocation loc);
    void attack(MapLocation loc);
    bool canHeal(MapLocation loc);
    void heal(MapLocation loc);
    vector<MapLocation> getAllySpawnLocations();
    bool canSpawn(MapLocation loc);
    void spawn(MapLocation loc);
    bool hasFlag();
    bool canPickupFlag(MapLocation loc);
    void pickupFlag(MapLocation loc);
    bool canDropFlag(MapLocation loc);
    void dropFlag(MapLocation loc);
    bool canBuyGlobal(GlobalUpgrade ug);
    void buyGlobal(GlobalUpgrade ug);
    int readSharedArray(int index);
    void writeSharedArray(int index, int value);
    void setIndicatorDot(MapLocation loc, int red, int green, int blue);
    void setIndicatorLine(MapLocation start, MapLocation end, int red, int green, int blue);
    void setIndicatorString(const string& s);
};
