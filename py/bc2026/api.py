"""Minimal Python shim of the Battlecode 2026 (battlecode.common) API surface.

Engine-facing calls (RobotController, Clock) are stubs - there is no Python
engine; value types are fully implemented so bot logic is preserved exactly.
"""


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


class UnitType:
    BABY_RAT = 0
    RAT_KING = 1
    CAT = 2


def isRobotType(t):
    return t != UnitType.CAT


def isThrowableType(t):
    return t == UnitType.BABY_RAT


def isThrowingType(t):
    return t in (UnitType.RAT_KING, UnitType.CAT)


def isBabyRatType(t):
    return t == UnitType.BABY_RAT


def isRatKingType(t):
    return t == UnitType.RAT_KING


def isCatType(t):
    return t == UnitType.CAT


class TrapType:
    RAT_TRAP = 0
    CAT_TRAP = 1
    NONE = 2


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
# Direction - includes DIRECTION_ORDER used by the 2026 engine
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

    def getDirectionOrderNum(self):
        return Direction._orderIndex[self.e]

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
# battlecode 2026 Direction.DIRECTION_ORDER:
# {CENTER, WEST, NORTHWEST, NORTH, NORTHEAST, EAST, SOUTHEAST, SOUTH, SOUTHWEST}
Direction.DIRECTION_ORDER = [
    Direction.CENTER, Direction.WEST, Direction.NORTHWEST, Direction.NORTH,
    Direction.NORTHEAST, Direction.EAST, Direction.SOUTHEAST, Direction.SOUTH,
    Direction.SOUTHWEST,
]
Direction._orderIndex = [3, 4, 5, 6, 7, 8, 1, 2, 0]


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
                 direction=None, chirality=0, type=UnitType.BABY_RAT,
                 rawCheeseAmount=0):
        self.ID = ID
        self.team = team
        self.health = health
        self.location = location
        self.direction = direction
        self.chirality = chirality
        self.type = type
        self.rawCheeseAmount = rawCheeseAmount

    def getID(self):
        return self.ID

    def getTeam(self):
        return self.team

    def getHealth(self):
        return self.health

    def getLocation(self):
        return self.location

    def getDirection(self):
        return self.direction

    def getChirality(self):
        return self.chirality

    def getType(self):
        return self.type

    def getRawCheeseAmount(self):
        return self.rawCheeseAmount


class MapInfo:
    def __init__(self, loc=None, passable=False, wall=False, dirt=False,
                 cheeseMine=False, cheeseAmount=0):
        self.loc = loc
        self.passable = passable
        self.wall = wall
        self.dirt = dirt
        self.cheeseMine = cheeseMine
        self.cheeseAmount = cheeseAmount

    def isPassable(self):
        return self.passable

    def isWall(self):
        return self.wall

    def isDirt(self):
        return self.dirt

    def hasCheeseMine(self):
        return self.cheeseMine

    def getCheeseAmount(self):
        return self.cheeseAmount

    def getMapLocation(self):
        return self.loc


class Message:
    def __init__(self, bytes=0, senderID=0, round=0, sourceLoc=None):
        self.bytes = bytes
        self.senderID = senderID
        self.round = round
        self.sourceLoc = sourceLoc

    def getSenderID(self):
        return self.senderID

    def getRound(self):
        return self.round

    def getBytes(self):
        return self.bytes

    def getSource(self):
        return self.sourceLoc


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
    def getDirection(self): raise NotImplementedError
    def getHealth(self): raise NotImplementedError
    def getType(self): raise NotImplementedError
    def getRawCheese(self): raise NotImplementedError
    def getGlobalCheese(self): raise NotImplementedError
    def getCurrentRatCost(self): raise NotImplementedError
    def isCooperation(self): raise NotImplementedError
    def isActionReady(self): raise NotImplementedError
    def isMovementReady(self): raise NotImplementedError
    def isTurningReady(self): raise NotImplementedError
    def isBeingCarried(self): raise NotImplementedError
    def isBeingThrown(self): raise NotImplementedError
    def getCarrying(self): raise NotImplementedError
    def onTheMap(self, loc): raise NotImplementedError
    def canSenseLocation(self, loc): raise NotImplementedError
    def isLocationOccupied(self, loc): raise NotImplementedError
    def canSenseRobotAtLocation(self, loc): raise NotImplementedError
    def senseRobotAtLocation(self, loc): raise NotImplementedError
    def canSenseRobot(self, id): raise NotImplementedError
    def senseRobot(self, id): raise NotImplementedError
    def sensePassability(self, loc): raise NotImplementedError
    def senseMapInfo(self, loc): raise NotImplementedError
    def senseNearbyMapInfos(self, radiusSquared=None, center=None): raise NotImplementedError
    def senseNearbyRobots(self, radiusSquared=None, team=None, center=None): raise NotImplementedError
    def getAllLocationsWithinRadiusSquared(self, center, radiusSquared): raise NotImplementedError
    def adjacentLocation(self, dir): raise NotImplementedError
    def canMove(self, d): raise NotImplementedError
    def move(self, d): raise NotImplementedError
    def canMoveForward(self): raise NotImplementedError
    def moveForward(self): raise NotImplementedError
    def canTurn(self, d=None): raise NotImplementedError
    def turn(self, d): raise NotImplementedError
    def canAttack(self, loc, cheeseAmount=None): raise NotImplementedError
    def attack(self, loc, cheeseAmount=None): raise NotImplementedError
    def canBuildRat(self, loc): raise NotImplementedError
    def buildRat(self, loc): raise NotImplementedError
    def canBecomeRatKing(self): raise NotImplementedError
    def becomeRatKing(self): raise NotImplementedError
    def canCarryRat(self, loc): raise NotImplementedError
    def carryRat(self, loc): raise NotImplementedError
    def canThrowRat(self): raise NotImplementedError
    def throwRat(self): raise NotImplementedError
    def canPickUpCheese(self, loc): raise NotImplementedError
    def pickUpCheese(self, loc, pickUpAmount=None): raise NotImplementedError
    def canTransferCheese(self, loc, amount): raise NotImplementedError
    def transferCheese(self, loc, amount): raise NotImplementedError
    def canPlaceDirt(self, loc): raise NotImplementedError
    def placeDirt(self, loc): raise NotImplementedError
    def canRemoveDirt(self, loc): raise NotImplementedError
    def removeDirt(self, loc): raise NotImplementedError
    def canPlaceRatTrap(self, loc): raise NotImplementedError
    def placeRatTrap(self, loc): raise NotImplementedError
    def canPlaceCatTrap(self, loc): raise NotImplementedError
    def placeCatTrap(self, loc): raise NotImplementedError
    def squeak(self, messageContent): raise NotImplementedError
    def readSqueaks(self, roundNum): raise NotImplementedError
    def readSharedArray(self, index): raise NotImplementedError
    def writeSharedArray(self, index, value): raise NotImplementedError
    def disintegrate(self): raise NotImplementedError
    def setIndicatorDot(self, loc, red, green, blue): raise NotImplementedError
    def setIndicatorLine(self, start, end, red, green, blue): raise NotImplementedError
    def setIndicatorString(self, s): raise NotImplementedError
