"""Minimal Python shim of the Battlecode 2024 (battlecode.common) API surface.

Engine-facing calls (RobotController, Clock) are stubs - there is no Python
engine; value types are fully implemented so bot logic is preserved exactly.
"""

import math


# ---------------------------------------------------------------------------
# Small fast PRNG used in place of java.util.Random
# ---------------------------------------------------------------------------
_MASK64 = 0xFFFFFFFFFFFFFFFF


class Random:
    def __init__(self, seed=0):
        s = seed if seed else 0x243F6A8885A308D3
        self.s = (s * 0x9E3779B97F4A7C15 if seed else s) & _MASK64

    def next(self):
        self.s = (self.s ^ ((self.s << 13) & _MASK64)) & _MASK64
        self.s = (self.s ^ (self.s >> 7)) & _MASK64
        self.s = (self.s ^ ((self.s << 17) & _MASK64)) & _MASK64
        return self.s

    def nextInt(self, bound=None):
        if bound is None:
            return self.next() & 0xFFFFFFFF
        return self.next() % bound

    def nextDouble(self):
        return self.next() / 4294967296.0


def signum(x):
    return (x > 0) - (x < 0)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------
class Team:
    A = 0
    B = 1
    NEUTRAL = 2


def opponent(t):
    return Team.B if t == Team.A else (Team.A if t == Team.B else Team.NEUTRAL)


class TrapType:
    EXPLOSIVE = 0
    WATER = 1
    STUN = 2
    NONE = 3


class SkillType:
    ATTACK = 0
    BUILD = 1
    HEAL = 2


class GlobalUpgrade:
    ATTACK = 0
    HEALING = 1
    CAPTURING = 2
    ACTION = 3


class GameActionExceptionType:
    INTERNAL_ERROR = 0
    NOT_ENOUGH_RESOURCE = 1
    CANT_MOVE_THERE = 2
    IS_NOT_READY = 3
    CANT_SENSE_THAT = 4
    OUT_OF_RANGE = 5
    CANT_DO_THAT = 6
    NO_ROBOT_THERE = 7


class GameActionException(Exception):
    def __init__(self, type=GameActionExceptionType.INTERNAL_ERROR, message=""):
        super().__init__(message)
        self.type = type
        self.message = message

    def getType(self):
        return self.type


# ---------------------------------------------------------------------------
# Direction - keeps dx/dy fields and member helpers like the Java enum
# ---------------------------------------------------------------------------
class Direction:
    NORTH = NORTHEAST = EAST = SOUTHEAST = SOUTH = SOUTHWEST = WEST = NORTHWEST = CENTER = None

    def __init__(self, e, dx, dy):
        self.e = e          # ordinal index into Direction.all
        self.dx = dx
        self.dy = dy

    def ordinal(self):
        return self.e

    def getDeltaX(self):
        return self.dx

    def getDeltaY(self):
        return self.dy

    def opposite(self):
        if self.e >= 8:
            return self
        return Direction.all[(self.e + 4) % 8]

    def rotateLeft(self):
        if self.e >= 8:
            return self
        return Direction.all[(self.e + 7) % 8]

    def rotateRight(self):
        if self.e >= 8:
            return self
        return Direction.all[(self.e + 1) % 8]

    def __eq__(self, other):
        return isinstance(other, Direction) and self.e == other.e

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return self.e

    @staticmethod
    def allDirections():
        return list(Direction.all)

    @staticmethod
    def cardinalDirections():
        return [Direction.NORTH, Direction.EAST, Direction.SOUTH, Direction.WEST]


Direction.NORTH = Direction(0, 0, 1)
Direction.NORTHEAST = Direction(1, 1, 1)
Direction.EAST = Direction(2, 1, 0)
Direction.SOUTHEAST = Direction(3, 1, -1)
Direction.SOUTH = Direction(4, 0, -1)
Direction.SOUTHWEST = Direction(5, -1, -1)
Direction.WEST = Direction(6, -1, 0)
Direction.NORTHWEST = Direction(7, -1, 1)
Direction.CENTER = Direction(8, 0, 0)
Direction.all = [
    Direction.NORTH, Direction.NORTHEAST, Direction.EAST, Direction.SOUTHEAST,
    Direction.SOUTH, Direction.SOUTHWEST, Direction.WEST, Direction.NORTHWEST,
    Direction.CENTER,
]


# ---------------------------------------------------------------------------
# MapLocation
# ---------------------------------------------------------------------------
class MapLocation:
    __slots__ = ("x", "y")

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def distanceSquaredTo(self, l):
        dx = l.x - self.x
        dy = l.y - self.y
        return dx * dx + dy * dy

    def isWithinDistanceSquared(self, l, r2):
        return self.distanceSquaredTo(l) <= r2

    def isAdjacentTo(self, l):
        dx = l.x - self.x
        dy = l.y - self.y
        return dx * dx <= 2 and dy * dy <= 2 and not (dx == 0 and dy == 0)

    def directionTo(self, l):
        dx = l.x - self.x
        dy = l.y - self.y
        if abs(dx) >= 2.414 * abs(dy):
            if dx > 0:
                return Direction.EAST
            if dx < 0:
                return Direction.WEST
            return Direction.CENTER
        if abs(dy) >= 2.414 * abs(dx):
            return Direction.NORTH if dy > 0 else Direction.SOUTH
        if dy > 0:
            return Direction.NORTHEAST if dx > 0 else Direction.NORTHWEST
        return Direction.SOUTHEAST if dx > 0 else Direction.SOUTHWEST

    def add(self, d):
        return MapLocation(self.x + d.dx, self.y + d.dy)

    def subtract(self, d):
        return MapLocation(self.x - d.dx, self.y - d.dy)

    def translate(self, dx, dy):
        return MapLocation(self.x + dx, self.y + dy)

    def __eq__(self, other):
        return isinstance(other, MapLocation) and self.x == other.x and self.y == other.y

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return self.x * 1000003 + self.y

    def __repr__(self):
        return "({}, {})".format(self.x, self.y)


# ---------------------------------------------------------------------------
# Info objects
# ---------------------------------------------------------------------------
class RobotInfo:
    def __init__(self, ID=0, team=Team.NEUTRAL, health=0, location=None,
                 hasFlag=False, attackLevel=0, healLevel=0, buildLevel=0):
        self.ID = ID
        self.team = team
        self.health = health
        self.location = location
        self.hasFlag = hasFlag
        self.attackLevel = attackLevel
        self.healLevel = healLevel
        self.buildLevel = buildLevel

    def getID(self):
        return self.ID

    def getTeam(self):
        return self.team

    def getHealth(self):
        return self.health

    def getLocation(self):
        return self.location

    def getHasFlag(self):
        return self.hasFlag

    def getAttackLevel(self):
        return self.attackLevel

    def getHealLevel(self):
        return self.healLevel

    def getBuildLevel(self):
        return self.buildLevel


class MapInfo:
    def __init__(self, loc=None, passable=False, wall=False, dam=False,
                 water=False, spawnZone=0, crumbsAmount=0,
                 trapType=TrapType.NONE, territory=Team.NEUTRAL):
        self.loc = loc
        self.passable = passable
        self.wall = wall
        self.dam = dam
        self.water = water
        self.spawnZone = spawnZone
        self.crumbsAmount = crumbsAmount
        self.trapType = trapType
        self.territory = territory

    def isPassable(self):
        return self.passable

    def isWall(self):
        return self.wall

    def isDam(self):
        return self.dam

    def isSpawnZone(self):
        return self.spawnZone != 0

    def getSpawnZoneTeam(self):
        return self.spawnZone

    def isWater(self):
        return self.water

    def getCrumbs(self):
        return self.crumbsAmount

    def getTrapType(self):
        return self.trapType

    def getMapLocation(self):
        return self.loc

    def getTeamTerritory(self):
        return self.territory


class FlagInfo:
    def __init__(self, loc=None, team=Team.NEUTRAL, pickedUp=False, id=0):
        self.loc = loc
        self.team = team
        self.pickedUp = pickedUp
        self.id = id

    def getLocation(self):
        return self.loc

    def getTeam(self):
        return self.team

    def isPickedUp(self):
        return self.pickedUp

    def getID(self):
        return self.id


# ---------------------------------------------------------------------------
# Constants / Clock
# ---------------------------------------------------------------------------
class GameConstants:
    MAP_MIN_HEIGHT = 20
    MAP_MAX_HEIGHT = 60
    MAP_MIN_WIDTH = 20
    MAP_MAX_WIDTH = 60
    MIN_FLAG_SPACING_SQUARED = 36
    GAME_MAX_NUMBER_OF_ROUNDS = 2000
    BYTECODE_LIMIT = 25000
    SHARED_ARRAY_LENGTH = 64
    MAX_SHARED_ARRAY_VALUE = (1 << 16) - 1
    DEFAULT_HEALTH = 1000
    ROBOT_CAPACITY = 50
    NUMBER_FLAGS = 3
    DIG_COST = 20
    FILL_COST = 30
    FLAG_BROADCAST_UPDATE_INTERVAL = 100
    FLAG_BROADCAST_NOISE_RADIUS = 100
    FLAG_DROPPED_RESET_ROUNDS = 4
    INITIAL_CRUMBS_AMOUNT = 400
    PASSIVE_CRUMBS_INCREASE = 10
    KILL_CRUMB_REWARD = 30
    SETUP_ROUNDS = 200
    GLOBAL_UPGRADE_ROUNDS = 600
    JAILED_ROUNDS = 25
    VISION_RADIUS_SQUARED = 20
    ATTACK_RADIUS_SQUARED = 4
    HEAL_RADIUS_SQUARED = 4
    INTERACT_RADIUS_SQUARED = 2
    COOLDOWN_LIMIT = 10
    COOLDOWNS_PER_TURN = 10
    MOVEMENT_COOLDOWN = 10
    FLAG_MOVEMENT_COOLDOWN = 20
    PICKUP_DROP_COOLDOWN = 10
    ATTACK_COOLDOWN = 20
    HEAL_COOLDOWN = 30


class Clock:
    @staticmethod
    def doYield():
        raise NotImplementedError

    @staticmethod
    def getBytecodesLeft():
        raise NotImplementedError

    @staticmethod
    def getBytecodeNum():
        raise NotImplementedError


# ---------------------------------------------------------------------------
# RobotController - stubs only (implemented by the Java engine)
# ---------------------------------------------------------------------------
class RobotController:
    def getRoundNum(self): raise NotImplementedError
    def getMapWidth(self): raise NotImplementedError
    def getMapHeight(self): raise NotImplementedError
    def getID(self): raise NotImplementedError
    def getTeam(self): raise NotImplementedError
    def getLocation(self): raise NotImplementedError
    def getHealth(self): raise NotImplementedError
    def getExperience(self, skill): raise NotImplementedError
    def getLevel(self, skill): raise NotImplementedError
    def getCrumbs(self): raise NotImplementedError
    def onTheMap(self, loc): raise NotImplementedError
    def canSenseLocation(self, loc): raise NotImplementedError
    def isLocationOccupied(self, loc): raise NotImplementedError
    def canSenseRobotAtLocation(self, loc): raise NotImplementedError
    def senseRobotAtLocation(self, loc): raise NotImplementedError
    def canSenseRobot(self, id): raise NotImplementedError
    def senseRobot(self, id): raise NotImplementedError
    def senseNearbyRobots(self, radiusSquared=None, team=None, center=None): raise NotImplementedError
    def senseNearbyCrumbs(self, radiusSquared): raise NotImplementedError
    def sensePassability(self, loc): raise NotImplementedError
    def senseMapInfo(self, loc): raise NotImplementedError
    def senseNearbyMapInfos(self, radiusSquared=None, center=None): raise NotImplementedError
    def senseNearbyFlags(self, radiusSquared, team=None): raise NotImplementedError
    def senseBroadcastFlagLocations(self): raise NotImplementedError
    def senseLegalStartingFlagPlacement(self, loc): raise NotImplementedError
    def adjacentLocation(self, dir): raise NotImplementedError
    def getAllLocationsWithinRadiusSquared(self, center, radiusSquared): raise NotImplementedError
    def isSpawned(self): raise NotImplementedError
    def isActionReady(self): raise NotImplementedError
    def getActionCooldownTurns(self): raise NotImplementedError
    def isMovementReady(self): raise NotImplementedError
    def getMovementCooldownTurns(self): raise NotImplementedError
    def canMove(self, dir): raise NotImplementedError
    def move(self, dir): raise NotImplementedError
    def canBuild(self, building, loc): raise NotImplementedError
    def build(self, building, loc): raise NotImplementedError
    def canDig(self, loc): raise NotImplementedError
    def dig(self, loc): raise NotImplementedError
    def canFill(self, loc): raise NotImplementedError
    def fill(self, loc): raise NotImplementedError
    def canAttack(self, loc): raise NotImplementedError
    def attack(self, loc): raise NotImplementedError
    def canHeal(self, loc): raise NotImplementedError
    def heal(self, loc): raise NotImplementedError
    def getAllySpawnLocations(self): raise NotImplementedError
    def canSpawn(self, loc): raise NotImplementedError
    def spawn(self, loc): raise NotImplementedError
    def hasFlag(self): raise NotImplementedError
    def canPickupFlag(self, loc): raise NotImplementedError
    def pickupFlag(self, loc): raise NotImplementedError
    def canDropFlag(self, loc): raise NotImplementedError
    def dropFlag(self, loc): raise NotImplementedError
    def canBuyGlobal(self, ug): raise NotImplementedError
    def buyGlobal(self, ug): raise NotImplementedError
    def readSharedArray(self, index): raise NotImplementedError
    def writeSharedArray(self, index, value): raise NotImplementedError
    def setIndicatorDot(self, loc, red, green, blue): raise NotImplementedError
    def setIndicatorLine(self, start, end, red, green, blue): raise NotImplementedError
    def setIndicatorString(self, s): raise NotImplementedError
