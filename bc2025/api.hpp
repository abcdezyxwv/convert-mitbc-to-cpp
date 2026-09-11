// Minimal C++ shim of the Battlecode 2025 (battlecode.common) API surface.
// Engine-facing calls are declarations only; value types are fully implemented.
#pragma once

#include <array>
#include <cmath>
#include <cstdint>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

using std::string;
using std::vector;

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

enum class Team { A, B, NEUTRAL };
inline Team opponent(Team t) {
    return t == Team::A ? Team::B : (t == Team::B ? Team::A : Team::NEUTRAL);
}

enum class PaintType { EMPTY, ALLY_PRIMARY, ALLY_SECONDARY, ENEMY_PRIMARY, ENEMY_SECONDARY };
inline bool isAlly(PaintType p) {
    return p == PaintType::ALLY_PRIMARY || p == PaintType::ALLY_SECONDARY;
}
inline bool isEnemy(PaintType p) {
    return p == PaintType::ENEMY_PRIMARY || p == PaintType::ENEMY_SECONDARY;
}
inline bool isSecondary(PaintType p) {
    return p == PaintType::ALLY_SECONDARY || p == PaintType::ENEMY_SECONDARY;
}

enum class UnitType {
    SOLDIER, SPLASHER, MOPPER,
    LEVEL_ONE_PAINT_TOWER, LEVEL_TWO_PAINT_TOWER, LEVEL_THREE_PAINT_TOWER,
    LEVEL_ONE_MONEY_TOWER, LEVEL_TWO_MONEY_TOWER, LEVEL_THREE_MONEY_TOWER,
    LEVEL_ONE_DEFENSE_TOWER, LEVEL_TWO_DEFENSE_TOWER, LEVEL_THREE_DEFENSE_TOWER
};
inline bool isTowerType(UnitType t) { return (int)t >= 3; }
inline bool isRobotType(UnitType t) { return (int)t < 3; }
inline UnitType getBaseType(UnitType t) {
    if (t < UnitType::LEVEL_ONE_PAINT_TOWER) return t;
    int kind = ((int)t - 3) / 3;
    return (UnitType)(3 + kind * 3);
}
inline UnitType getNextLevel(UnitType t) {
    int i = (int)t;
    return (i >= 3 && i % 3 != 2) ? (UnitType)(i + 1) : t;
}
inline bool canUpgradeType(UnitType t) { return (int)t >= 3 && (int)t % 3 != 2; }

enum class GameActionExceptionType {
    INTERNAL_ERROR, NOT_ENOUGH_RESOURCE, CANT_MOVE_THERE, IS_NOT_READY,
    CANT_SENSE_THAT, OUT_OF_RANGE, CANT_DO_THAT, NO_ROBOT_THERE,
    CANT_SENSE_ROBOT, UNIT_NOT_IN_TOWER
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

struct RobotInfo {
    int ID = 0;
    Team team = Team::NEUTRAL;
    int health = 0;
    MapLocation location;
    UnitType type = UnitType::SOLDIER;
    int paintAmount = 0;

    int getID() const { return ID; }
    Team getTeam() const { return team; }
    int getHealth() const { return health; }
    MapLocation getLocation() const { return location; }
    UnitType getType() const { return type; }
    int getPaintAmount() const { return paintAmount; }
};

struct MapInfo {
    MapLocation loc;
    bool passable = false, wall = false, ruin = false, resourcePatternCenter = false;
    PaintType paint = PaintType::EMPTY;
    PaintType mark = PaintType::EMPTY;

    bool isPassable() const { return passable; }
    bool isWall() const { return wall; }
    bool hasRuin() const { return ruin; }
    PaintType getPaint() const { return paint; }
    PaintType getMark() const { return mark; }
    MapLocation getMapLocation() const { return loc; }
    bool isResourcePatternCenter() const { return resourcePatternCenter; }
};

struct Message {
    int bytes = 0, senderID = 0, round = 0;
    int getSenderID() const { return senderID; }
    int getRound() const { return round; }
    int getBytes() const { return bytes; }
};

struct GameConstants {
    static constexpr int GAME_MAX_NUMBER_OF_ROUNDS = 2000;
    static constexpr int BYTECODE_LIMIT = 40000;
    static constexpr int SHARED_ARRAY_LENGTH = 64;
    static constexpr int MAX_SHARED_ARRAY_VALUE = (1 << 16) - 1;
    static constexpr int MAP_MIN_HEIGHT = 20, MAP_MAX_HEIGHT = 60;
    static constexpr int MAP_MIN_WIDTH = 20, MAP_MAX_WIDTH = 60;
    static constexpr int MAX_NUMBER_OF_TOWERS = 25;
    static constexpr int GAME_DEFAULT_SEED = 6370;
};

struct Clock {
    static void yield();
    static int getBytecodesLeft();
    static int getBytecodeNum();
};

class RobotController {
public:
    int getRoundNum();
    int getMapWidth();
    int getMapHeight();
    int getID();
    Team getTeam();
    MapLocation getLocation();
    int getHealth();
    int getPaint();
    int getMoney();
    int getNumberTowers();
    UnitType getType();
    int getActionCooldownTurns();
    bool isActionReady();
    bool isMovementReady();
    bool onTheMap(MapLocation loc);
    bool canSenseLocation(MapLocation loc);
    MapInfo senseMapInfo(MapLocation loc);
    vector<MapInfo> senseNearbyMapInfos();
    vector<MapInfo> senseNearbyMapInfos(MapLocation center);
    vector<MapInfo> senseNearbyMapInfos(MapLocation center, int radiusSquared);
    vector<MapInfo> senseNearbyMapInfos(int radiusSquared);
    vector<MapLocation> senseNearbyRuins(int radiusSquared);
    RobotInfo senseRobotAtLocation(MapLocation loc);
    vector<RobotInfo> senseNearbyRobots();
    vector<RobotInfo> senseNearbyRobots(int radiusSquared);
    vector<RobotInfo> senseNearbyRobots(int radiusSquared, Team team);
    vector<RobotInfo> senseNearbyRobots(MapLocation center, int radiusSquared, Team team);
    vector<MapLocation> getAllLocationsWithinRadiusSquared(MapLocation center, int radiusSquared);
    vector<vector<bool>> getTowerPattern(UnitType type);
    bool canMove(Direction dir);
    void move(Direction dir);
    bool canAttack(MapLocation loc);
    void attack(MapLocation loc);
    void attack(MapLocation loc, bool useSecondaryColor);
    bool canMark(MapLocation loc);
    void mark(MapLocation loc, bool secondary);
    bool canRemoveMark(MapLocation loc);
    void removeMark(MapLocation loc);
    bool canBuildRobot(UnitType type, MapLocation loc);
    void buildRobot(UnitType type, MapLocation loc);
    bool canCompleteTowerPattern(UnitType type, MapLocation loc);
    void completeTowerPattern(UnitType type, MapLocation loc);
    bool canCompleteResourcePattern(MapLocation loc);
    void completeResourcePattern(MapLocation loc);
    bool canUpgradeTower(MapLocation loc);
    void upgradeTower(MapLocation loc);
    bool canTransferPaint(MapLocation loc, int amount);
    void transferPaint(MapLocation loc, int amount);
    bool canBroadcastMessage();
    void broadcastMessage(int messageContent);
    bool canSendMessage(MapLocation loc);
    bool canSendMessage(MapLocation loc, int messageContent);
    void sendMessage(MapLocation loc, int messageContent);
    vector<Message> readMessages(int roundNum);
    void disintegrate();
    void setIndicatorDot(MapLocation loc, int red, int green, int blue);
    void setIndicatorLine(MapLocation start, MapLocation end, int red, int green, int blue);
    void setIndicatorString(const string& s);
};
