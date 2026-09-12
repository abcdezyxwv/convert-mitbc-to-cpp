# Port of bestsofar/Utils/Vision.java. See py/CONVENTIONS.md.
import math

from api import *
from Utils.AdditionalClasses.Thrown import Thrown
from Utils.Globals import Globals


class _Bits(list):
    # The Java Vision has BOTH a `public static long[]` field AND a same-named
    # `public static boolean <name>(MapLocation)` method for isWall and
    # isDangerous. A Python class attribute cannot be both, so these are lists
    # that are also callable: `Vision.isWall[x]` indexes the bitset and
    # `Vision.isWall(loc)` runs the method's exact logic (same trick as the
    # C++ port's IsWallBits functor).
    def __init__(self):
        super().__init__([0] * 60)

    def __call__(self, loc):
        # Java method body: ((<field>[loc.x] >> loc.y) & 1) > 0
        return ((self[loc.x] >> loc.y) & 1) > 0


class _IsDirtBits(_Bits):
    def __call__(self, loc):
        # Java isDirt(MapLocation) reads the hasSeen field plus its own bits
        return ((Vision.hasSeen[loc.x] >> loc.y) & 1) > 0 and ((self[loc.x] >> loc.y) & 1) > 0


class Vision(Globals):

    hasSeen = [0] * 60
    isWall = _Bits()
    isDirt = _IsDirtBits()
    hasCheeseMine = [0] * 60
    isReachable = [0] * 60

    isDangerous = _Bits()

    enemies = None  # RobotInfo[]
    walls = None  # MapLocation[]
    numWalls = 0
    mines = None  # MapLocation[]
    numMines = 0

    turnLeft = False

    @staticmethod
    def lookAround():
        # System.out.println(Clock.getBytecodeNum());

        for mi in Globals.rc.senseNearbyMapInfos():
            x = mi.getMapLocation().x
            y = mi.getMapLocation().y

            if ((Vision.hasSeen[x] >> y) & 1) == 0 or ((Vision.isWall[x] >> y) & 1) == 0:
                Vision.hasSeen[x] |= 1 << y
                if mi.isWall():
                    Vision.isWall[x] |= 1 << y
                if mi.hasCheeseMine():
                    Vision.hasCheeseMine[x] |= 1 << y
                if mi.isDirt():
                    Vision.isDirt[x] |= 1 << y
                else:
                    Vision.isDirt[x] &= ~(1 << y)

        # System.out.println(Clock.getBytecodeNum());

    @staticmethod
    def turn(dir):
        if dir == Direction.CENTER or dir == Globals.rc.getDirection() or Globals.cantTurn or not Globals.rc.canTurn():
            return
        Globals.rc.turn(dir)
        Vision.lookAround()

    @staticmethod
    def bestTurn():
        sumX = Globals.rc.getLocation().x
        sumY = Globals.rc.getLocation().y
        for i in range(len(Globals.newestSqueaks)):
            sumX += Globals.newestSqueaks[i].getSource().x
            sumY += Globals.newestSqueaks[i].getSource().y
        # all operands non-negative: Java int division
        sumX = (sumX + (len(Globals.newestSqueaks) + 1) // 2) // (len(Globals.newestSqueaks) + 1)
        sumY = (sumY + (len(Globals.newestSqueaks) + 1) // 2) // (len(Globals.newestSqueaks) + 1)
        d = Globals.rc.getLocation().directionTo(MapLocation(sumX, sumY)).opposite()
        if d == Direction.CENTER:
            Vision.turnLeft = not Vision.turnLeft
            if Vision.turnLeft:
                return Globals.rc.getDirection().rotateLeft().rotateLeft()
            return Globals.rc.getDirection().rotateRight().rotateRight()
        return d

    @staticmethod
    def turnJustBecause():
        if Globals.rc.canTurn() and len(Globals.enemyRobots) == 0 and len(Globals.newestSqueaks) == 0:
            Vision.turn(Vision.bestTurn())

    @staticmethod
    def senseNearbyEnemies():
        # Java: rc.getType().visionConeRadiusSquared
        Vision.enemies = Globals.rc.senseNearbyRobots(Vision.visionConeRadiusSquared(Globals.rc.getType()), Globals.opponentTeam)

    @staticmethod
    def seenByEnemies():
        for ri in Vision.enemies:
            # Java: rc.getLocation().isWithinDistanceSquared(ri.location,
            #   ri.getType().visionConeRadiusSquared, ri.getDirection(),
            #   ri.getType().visionConeAngle)
            if Vision.isWithinDistanceSquaredCone(Globals.rc.getLocation(), ri.location,
                                                  Vision.visionConeRadiusSquared(ri.getType()),
                                                  ri.getDirection(),
                                                  Vision.visionConeAngle(ri.getType())):
                return True
        return False

    @staticmethod
    def digDirt(loc):
        Vision.isDirt[loc.x] &= ~(1 << loc.y)

    @staticmethod
    def placeDirt(loc):
        Vision.isDirt[loc.x] |= 1 << loc.y

    @staticmethod
    def hasSeenLocation(loc):
        return Globals.rc.onTheMap(loc) and ((Vision.hasSeen[loc.x] >> loc.y) & 1) > 0

    @staticmethod
    def hasSeenLocationKnownToBeOnMap(loc):
        return ((Vision.hasSeen[loc.x] >> loc.y) & 1) > 0

    @staticmethod
    def sensePassability(loc):
        return ((Vision.isWall[loc.x] >> loc.y) & 1) == 0 and ((Vision.isDirt[loc.x] >> loc.y) & 1) == 0

    # Java: isDirt(MapLocation), isWall(MapLocation), isDangerous(MapLocation)
    # live on the bitset objects' __call__ (they share their field's name).

    @staticmethod
    def canReach(loc):
        return ((Vision.isReachable[loc.x] >> loc.y) & 1) > 0

    @staticmethod
    def isPassableWithDig(loc):
        return ((Vision.isWall[loc.x] >> loc.y) & 1) == 0

    @staticmethod
    def isMine(loc):
        return ((Vision.hasCheeseMine[loc.x] >> loc.y) & 1) > 0

    @staticmethod
    def init():
        pass

    @staticmethod
    def startTurn():
        if Globals.rc.getType() == UnitType.BABY_RAT:
            Vision.lookAround()
        # TODO: optimise by detecting canDig nearby or canMove nearby
        for throwns in Globals.alliesThrown:
            loc = throwns.loc.add(throwns.dir)
            if Vision.hasSeenLocation(loc):
                Vision.isDangerous[loc.x] |= (1 << loc.y)
            loc = loc.add(throwns.dir)
            if Vision.hasSeenLocation(loc):
                Vision.isDangerous[loc.x] |= (1 << loc.y)

    @staticmethod
    def endTurn():
        for throwns in Globals.alliesThrown:
            loc = throwns.loc.add(throwns.dir)
            if Vision.hasSeenLocation(loc):
                Vision.isDangerous[loc.x] &= ~(1 << loc.y)
            loc = loc.add(throwns.dir)
            if Vision.hasSeenLocation(loc):
                Vision.isDangerous[loc.x] &= ~(1 << loc.y)

    # api.py's UnitType is a plain int and MapLocation only offers the
    # 2-argument isWithinDistanceSquared, so the engine's UnitType vision-cone
    # constants and the cone overload are mirrored here (values/logic copied
    # verbatim from battlecode.common.UnitType / MapLocation, same as the C++
    # port). See notes: these belong in api.py.
    @staticmethod
    def visionConeRadiusSquared(t):
        if t == UnitType.BABY_RAT:
            return 20
        if t == UnitType.RAT_KING:
            return 25
        if t == UnitType.CAT:
            return 17
        return 0

    @staticmethod
    def visionConeAngle(t):
        if t == UnitType.BABY_RAT:
            return 90
        if t == UnitType.RAT_KING:
            return 360
        if t == UnitType.CAT:
            return 180
        return 0

    # mirrors MapLocation.isWithinDistanceSquared(location, distanceSquared,
    # facingDir, theta) (useBottomLeft == false)
    @staticmethod
    def isWithinDistanceSquaredCone(self_, location, distanceSquared, facingDir, theta):
        if self_ == location:
            return True

        adjustment = 1e-3

        isValidDistance = self_.distanceSquaredTo(location) <= distanceSquared

        dx = location.x - self_.x
        dy = location.y - self_.y

        if facingDir == Direction.CENTER:
            isValidAngle = True
        else:
            cosSim = (facingDir.dx * dx + facingDir.dy * dy) / \
                math.sqrt((dx * dx + dy * dy) * (facingDir.dx * facingDir.dx + facingDir.dy * facingDir.dy))
            halfAngle = abs(math.acos(cosSim)) * 180.0 / math.pi
            isValidAngle = halfAngle - adjustment <= theta / 2
        return isValidDistance and isValidAngle
