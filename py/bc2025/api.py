"""Minimal Python shim of the Battlecode 2025 (battlecode.common) API surface.

Engine-facing calls (RobotController, Clock) are stubs - there is no Python
engine; value types are fully implemented so bot logic is preserved exactly.
"""

from enum import Enum


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


class PaintType(Enum):
    EMPTY = 0
    ALLY_PRIMARY = 1
    ALLY_SECONDARY = 2
    ENEMY_PRIMARY = 3
    ENEMY_SECONDARY = 4

    def isAlly(self):
        return self in (PaintType.ALLY_PRIMARY, PaintType.ALLY_SECONDARY)

    def isEnemy(self):
        return self in (PaintType.ENEMY_PRIMARY, PaintType.ENEMY_SECONDARY)

    def isSecondary(self):
        return self in (PaintType.ALLY_SECONDARY, PaintType.ENEMY_SECONDARY)


def isAlly(p):
    return p in (PaintType.ALLY_PRIMARY, PaintType.ALLY_SECONDARY)


def isEnemy(p):
    return p in (PaintType.ENEMY_PRIMARY, PaintType.ENEMY_SECONDARY)


def isSecondary(p):
    return p in (PaintType.ALLY_SECONDARY, PaintType.ENEMY_SECONDARY)


class UnitType(Enum):
    # battlecode.common.UnitType: (paintCost, moneyCost, attackCost, health,
    # level, paintCapacity, actionCooldown, actionRadiusSquared,
    # attackStrength, aoeAttackStrength, paintPerTurn, moneyPerTurn,
    # attackMoneyBonus) - values verbatim from the engine enum declaration.
    SOLDIER = (200, 250, 5, 250, -1, 200, 10, 9, 50, -1, 0, 0, 0)
    SPLASHER = (300, 400, 50, 150, -1, 300, 50, 4, -1, 100, 0, 0, 0)
    MOPPER = (100, 300, 0, 50, -1, 100, 30, 2, -1, -1, 0, 0, 0)
    LEVEL_ONE_PAINT_TOWER = (0, 1000, 0, 1000, 1, 1000, 10, 9, 20, 10, 5, 0, 0)
    LEVEL_TWO_PAINT_TOWER = (0, 2500, 0, 1500, 2, 1000, 10, 9, 20, 10, 10, 0, 0)
    LEVEL_THREE_PAINT_TOWER = (0, 5000, 0, 2000, 3, 1000, 10, 9, 20, 10, 15, 0, 0)
    LEVEL_ONE_MONEY_TOWER = (0, 1000, 0, 1000, 1, 1000, 10, 9, 20, 10, 0, 20, 0)
    LEVEL_TWO_MONEY_TOWER = (0, 2500, 0, 1500, 2, 1000, 10, 9, 20, 10, 0, 30, 0)
    LEVEL_THREE_MONEY_TOWER = (0, 5000, 0, 2000, 3, 1000, 10, 9, 20, 10, 0, 40, 0)
    LEVEL_ONE_DEFENSE_TOWER = (0, 1000, 0, 2000, 1, 1000, 10, 16, 40, 20, 0, 0, 20)
    LEVEL_TWO_DEFENSE_TOWER = (0, 2500, 0, 2500, 2, 1000, 10, 16, 50, 25, 0, 0, 30)
    LEVEL_THREE_DEFENSE_TOWER = (0, 5000, 0, 3000, 3, 1000, 10, 16, 60, 30, 0, 0, 40)

    def __init__(self, paintCost, moneyCost, attackCost, health, level,
                 paintCapacity, actionCooldown, actionRadiusSquared,
                 attackStrength, aoeAttackStrength, paintPerTurn, moneyPerTurn,
                 attackMoneyBonus):
        self.paintCost = paintCost
        self.moneyCost = moneyCost
        self.attackCost = attackCost
        self.health = health
        self.level = level
        self.paintCapacity = paintCapacity
        self.actionCooldown = actionCooldown
        self.actionRadiusSquared = actionRadiusSquared
        self.attackStrength = attackStrength
        self.aoeAttackStrength = aoeAttackStrength
        self.paintPerTurn = paintPerTurn
        self.moneyPerTurn = moneyPerTurn
        self.attackMoneyBonus = attackMoneyBonus

    def isRobotType(self):
        return self in _ROBOTS

    def isTowerType(self):
        return self not in _ROBOTS

    def getBaseType(self):
        if self in _ROBOTS:
            return self
        kind = (list(UnitType).index(self) - 3) // 3
        return list(UnitType)[3 + kind * 3]

    def getNextLevel(self):
        i = list(UnitType).index(self)
        return list(UnitType)[i + 1] if i >= 3 and i % 3 != 2 else self

    def canUpgradeType(self):
        i = list(UnitType).index(self)
        return i >= 3 and i % 3 != 2


_ROBOTS = (UnitType.SOLDIER, UnitType.SPLASHER, UnitType.MOPPER)


def isTowerType(t):
    return t not in _ROBOTS


def isRobotType(t):
    return t in _ROBOTS


def getBaseType(t):
    return t.getBaseType()


def getNextLevel(t):
    return t.getNextLevel()


def canUpgradeType(t):
    return t.canUpgradeType()


class GameActionExceptionType:
    INTERNAL_ERROR = 0
    NOT_ENOUGH_RESOURCE = 1
    CANT_MOVE_THERE = 2
    IS_NOT_READY = 3
    CANT_SENSE_THAT = 4
    OUT_OF_RANGE = 5
    CANT_DO_THAT = 6
    NO_ROBOT_THERE = 7
    CANT_SENSE_ROBOT = 8
    UNIT_NOT_IN_TOWER = 9


class GameActionException(Exception):
    def __init__(self, type=GameActionExceptionType.INTERNAL_ERROR, message=""):
        super().__init__(message)
        self.type = type
        self.message = message

    def getType(self):
        return self.type


# ---------------------------------------------------------------------------
# Direction
# ---------------------------------------------------------------------------
class Direction:
    NORTH = NORTHEAST = EAST = SOUTHEAST = SOUTH = SOUTHWEST = WEST = NORTHWEST = CENTER = None

    def __init__(self, e, dx, dy):
        self.e = e
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
                 type=UnitType.SOLDIER, paintAmount=0):
        self.ID = ID
        self.team = team
        self.health = health
        self.location = location
        self.type = type
        self.paintAmount = paintAmount

    def getID(self):
        return self.ID

    def getTeam(self):
        return self.team

    def getHealth(self):
        return self.health

    def getLocation(self):
        return self.location

    def getType(self):
        return self.type

    def getPaintAmount(self):
        return self.paintAmount


class MapInfo:
    def __init__(self, loc=None, passable=False, wall=False, ruin=False,
                 resourcePatternCenter=False, paint=PaintType.EMPTY,
                 mark=PaintType.EMPTY):
        self.loc = loc
        self.passable = passable
        self.wall = wall
        self.ruin = ruin
        self.resourcePatternCenter = resourcePatternCenter
        self.paint = paint
        self.mark = mark

    def isPassable(self):
        return self.passable

    def isWall(self):
        return self.wall

    def hasRuin(self):
        return self.ruin

    def getPaint(self):
        return self.paint

    def getMark(self):
        return self.mark

    def getMapLocation(self):
        return self.loc

    def isResourcePatternCenter(self):
        return self.resourcePatternCenter


class Message:
    def __init__(self, bytes=0, senderID=0, round=0):
        self.bytes = bytes
        self.senderID = senderID
        self.round = round

    def getSenderID(self):
        return self.senderID

    def getRound(self):
        return self.round

    def getBytes(self):
        return self.bytes


# ---------------------------------------------------------------------------
# Constants / Clock
# ---------------------------------------------------------------------------
class GameConstants:
    GAME_MAX_NUMBER_OF_ROUNDS = 2000
    BYTECODE_LIMIT = 40000
    SHARED_ARRAY_LENGTH = 64
    MAX_SHARED_ARRAY_VALUE = (1 << 16) - 1
    MAP_MIN_HEIGHT = 20
    MAP_MAX_HEIGHT = 60
    MAP_MIN_WIDTH = 20
    MAP_MAX_WIDTH = 60
    MAX_NUMBER_OF_TOWERS = 25
    GAME_DEFAULT_SEED = 6370


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
    def getPaint(self): raise NotImplementedError
    def getMoney(self): raise NotImplementedError
    def getNumberTowers(self): raise NotImplementedError
    def getType(self): raise NotImplementedError
    def getActionCooldownTurns(self): raise NotImplementedError
    def isActionReady(self): raise NotImplementedError
    def isMovementReady(self): raise NotImplementedError
    def onTheMap(self, loc): raise NotImplementedError
    def canSenseLocation(self, loc): raise NotImplementedError
    def canSenseRobotAtLocation(self, loc): raise NotImplementedError
    def canSenseRobot(self, id): raise NotImplementedError
    def senseRobot(self, id): raise NotImplementedError
    def isLocationOccupied(self, loc): raise NotImplementedError
    def senseMapInfo(self, loc): raise NotImplementedError
    def senseNearbyMapInfos(self, center=None, radiusSquared=None): raise NotImplementedError
    def senseNearbyRuins(self, radiusSquared): raise NotImplementedError
    def senseRobotAtLocation(self, loc): raise NotImplementedError
    def senseNearbyRobots(self, radiusSquared=None, team=None, center=None): raise NotImplementedError
    def getAllLocationsWithinRadiusSquared(self, center, radiusSquared): raise NotImplementedError
    def getTowerPattern(self, type): raise NotImplementedError
    def canMove(self, dir): raise NotImplementedError
    def move(self, dir): raise NotImplementedError
    def canAttack(self, loc): raise NotImplementedError
    def attack(self, loc, useSecondaryColor=None): raise NotImplementedError
    def canMark(self, loc): raise NotImplementedError
    def mark(self, loc, secondary): raise NotImplementedError
    def canRemoveMark(self, loc): raise NotImplementedError
    def removeMark(self, loc): raise NotImplementedError
    def canBuildRobot(self, type, loc): raise NotImplementedError
    def buildRobot(self, type, loc): raise NotImplementedError
    def canCompleteTowerPattern(self, type, loc): raise NotImplementedError
    def completeTowerPattern(self, type, loc): raise NotImplementedError
    def canCompleteResourcePattern(self, loc): raise NotImplementedError
    def completeResourcePattern(self, loc): raise NotImplementedError
    def canUpgradeTower(self, loc): raise NotImplementedError
    def upgradeTower(self, loc): raise NotImplementedError
    def canTransferPaint(self, loc, amount): raise NotImplementedError
    def transferPaint(self, loc, amount): raise NotImplementedError
    def canBroadcastMessage(self): raise NotImplementedError
    def broadcastMessage(self, messageContent): raise NotImplementedError
    def canSendMessage(self, loc, messageContent=None): raise NotImplementedError
    def sendMessage(self, loc, messageContent): raise NotImplementedError
    def readMessages(self, roundNum): raise NotImplementedError
    def disintegrate(self): raise NotImplementedError
    def setIndicatorDot(self, loc, red, green, blue): raise NotImplementedError
    def setIndicatorLine(self, start, end, red, green, blue): raise NotImplementedError
    def setIndicatorString(self, s): raise NotImplementedError
