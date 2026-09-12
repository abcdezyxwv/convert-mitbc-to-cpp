# Port of bestsofar/Utils/Comms.java. See py/CONVENTIONS.md.
from api import *
from Utils.Globals import Globals
from Utils.AdditionalClasses.Threat import Threat
from Utils.AdditionalClasses.Thrown import Thrown

EAST = Direction.EAST  # Java: import static battlecode.common.Direction.EAST


class Comms(Globals):

    @staticmethod
    def init():
        if Globals.rc.getType() == UnitType.RAT_KING:
            Globals.rc.writeSharedArray(63, 1)

    @staticmethod
    def startTurn():
        if Globals.rc.getType() == UnitType.RAT_KING:
            # Locations
            x = (Globals.rc.readSharedArray(63) >> 3 * (Globals.rc.getRoundNum() % 3)) % 8
            Globals.rc.writeSharedArray(2 * x, Globals.rc.getLocation().x)
            Globals.rc.writeSharedArray(2 * x + 1, Globals.rc.getLocation().y)

            v = Globals.rc.readSharedArray(63)
            # Java: switch on the round number, evaluated once total
            switchVal = Globals.rc.getRoundNum() % 3
            if switchVal == 0:
                v += 1
                v &= 0b111000111
            elif switchVal == 1:
                v += 8
                v &= 0b111111
            elif switchVal == 2:
                v += 64
                v &= 0b111111000
            Globals.rc.writeSharedArray(63, v)
        n = Comms.getNumKings()
        for i in range(n):
            Globals.kingPos[i] = MapLocation(Globals.rc.readSharedArray(2 * i), Globals.rc.readSharedArray(2 * i + 1))
        for i in range(n, 5):
            Globals.kingPos[i] = None

    @staticmethod
    def getNumKings():
        return (Globals.rc.readSharedArray(63) >> 3 * ((Globals.rc.getRoundNum() + 2) % 3)) % 8

    @staticmethod
    def getSymmetry():
        return Globals.rc.readSharedArray(10)

    @staticmethod
    def updateSymmetry(x):
        Globals.rc.writeSharedArray(10, x)

    @staticmethod
    def encodeDir(dir):
        # Java: switch (dir) { EAST -> 0; ...; default -> 0 }
        if dir == EAST:
            return 0
        if dir == Direction.WEST:
            return 1
        if dir == Direction.NORTH:
            return 2
        if dir == Direction.SOUTH:
            return 3
        if dir == Direction.NORTHEAST:
            return 4
        if dir == Direction.NORTHWEST:
            return 5
        if dir == Direction.SOUTHEAST:
            return 6
        if dir == Direction.SOUTHWEST:
            return 7
        return 0

    @staticmethod
    def decodeDir(dir):
        # Java: switch (dir) { 0 -> EAST; ...; default -> EAST }
        if dir == 0:
            return EAST
        if dir == 1:
            return Direction.WEST
        if dir == 2:
            return Direction.NORTH
        if dir == 3:
            return Direction.SOUTH
        if dir == 4:
            return Direction.NORTHEAST
        if dir == 5:
            return Direction.NORTHWEST
        if dir == 6:
            return Direction.SOUTHEAST
        if dir == 7:
            return Direction.SOUTHWEST
        return EAST

    @staticmethod
    def squeakEnemies():
        # ignore if no threats (trust anson 1v1 micro)
        if (len(Globals.enemyRobots) < 1) or Globals.hasSqueaked or (len(Globals.catRobots) > 0 and isRatKingType(Globals.rc.getType())):
            return
        # evaluate all the threats based off some heuristic
        weakest = None
        strongest = None
        wScore = 1000000
        sScore = 0
        for enemy in Globals.enemyRobots:
            # Rat king is always the strongest
            if enemy.getType() == UnitType.RAT_KING:
                strongest = enemy
                sScore = 1000000
                if weakest is None:
                    weakest = enemy
            else:
                score = 1000 + 2 * enemy.getHealth()
                # distanceSquaredTo >= 0: Java int division
                penalty = max(0, 6 - (Globals.rc.getLocation().distanceSquaredTo(enemy.getLocation()) // 5))
                score += 10 * penalty
                # cheese slows them down
                score -= enemy.getRawCheeseAmount()
                # having a rat is really op
                # Java: api.py's RobotInfo has no getCarryingRobot(); the call
                # is kept to match the Java text (shim gap).
                gun = enemy.getCarryingRobot()
                if gun is not None:
                    if gun.getTeam() == Globals.myTeam:
                        score += 100 * penalty
                    else:
                        score += 60 * penalty
                if score <= wScore:
                    weakest = enemy
                    wScore = score
                if score > sScore:
                    strongest = enemy
                    sScore = score

        # Communicate the weakest + strongest
        # encode weakest
        msg = 0
        if weakest is not None:
            # map x, map y, direction
            wloc = weakest.getLocation()
            Globals.rc.setIndicatorDot(wloc, 0, 255, 0)
            msg += ((wloc.x) << 9) + ((wloc.y) << 3) + Comms.encodeDir(weakest.getDirection())
        msg <<= 15

        msg += Globals.rc.getHealth()

        msg += (Globals.rc.getDirection().getDirectionOrderNum() - 1) << 12

        msg = -msg
        if not Globals.hasSqueaked:
            Globals.rc.squeak(msg)
            Globals.hasSqueaked = True

    @staticmethod
    def readThreats():
        sz = 0
        for m in Globals.newestSqueaks:
            if m.getBytes() <= -1:
                sz += 2
        threats = [None] * sz
        ptr = 0
        for m in Globals.newestSqueaks:
            if m.getBytes() <= -1:
                msg = -m.getBytes()
                # strongest first
                dir = Comms.decodeDir(msg & 0b111)
                msg = msg >> 3
                y = (msg & 0b111111)
                msg = msg >> 6
                x = (msg & 0b111111)
                msg = msg >> 6
                threats[ptr] = Threat(MapLocation(x, y), dir, True)
                ptr += 1
                # weakest second
                dir = Comms.decodeDir(msg & 0b111)
                msg = msg >> 3
                y = (msg & 0b111111)
                msg = msg >> 6
                x = (msg & 0b111111)
                threats[ptr] = Threat(MapLocation(x, y), dir, False)
                ptr += 1
        return threats

    @staticmethod
    def alertHunters(cat):
        if cat.getType() != UnitType.CAT:
            return
        Globals.rc.writeSharedArray(62, cat.getID() % 1024)

    @staticmethod
    def updatePreyLoc(loc):
        msg = (1 << 27) + (loc.x << 6) + loc.y
        if not Globals.hasSqueaked:
            Globals.rc.squeak(msg)
            Globals.hasSqueaked = True

    @staticmethod
    def getPreyLoc():
        for m in Globals.newestSqueaks:
            if m.getBytes() > 0:
                msg = m.getBytes()
                if (msg & (1 << 27)) > 0:
                    y = msg & 0b111111
                    msg = msg >> 6
                    x = msg & 0b111111
                    return MapLocation(x, y)
        return MapLocation(-1, -1)

    @staticmethod
    def squeakEnemyKing(loc):
        msg = (1 << 25) + (loc.x << 6) + loc.y
        if not Globals.hasSqueaked:
            Globals.rc.squeak(msg)
            Globals.hasSqueaked = True

    @staticmethod
    def getEnemyKing():
        for m in Globals.newestSqueaks:
            if m.getBytes() > 0:
                msg = m.getBytes()
                if (msg & (1 << 25)) > 0:
                    y = msg & 0b111111
                    msg = msg >> 6
                    x = msg & 0b111111
                    return MapLocation(x, y)
        return None

    @staticmethod
    def squeakNewKing(mine):
        msg = (1 << 28) + (mine.x << 6) + mine.y
        if not Globals.hasSqueaked:
            Globals.rc.squeak(msg)
            Globals.hasSqueaked = True

    @staticmethod
    def checkForNewKings():
        for m in Globals.newestSqueaks:
            if m.getBytes() > 0:
                msg = m.getBytes()
                if (msg & (1 << 28)) > 0:
                    y = msg & 0b111111
                    msg = msg >> 6
                    x = msg & 0b111111
                    return MapLocation(x, y)
        return None

    @staticmethod
    def encodeNewKingPos(mine):
        Globals.rc.writeSharedArray(57, 0)
        Globals.rc.writeSharedArray(58, mine.x + 1)
        Globals.rc.writeSharedArray(59, mine.y + 1)

    @staticmethod
    def clearNewKing():
        Globals.rc.writeSharedArray(58, 0)

    @staticmethod
    def getNumberBots():
        return Globals.rc.readSharedArray(57)

    @staticmethod
    def incNewKingBotCount(cur):
        Globals.rc.writeSharedArray(57, min(cur + 1, 20))

    @staticmethod
    def needNewKing():
        x = Globals.rc.readSharedArray(58)
        y = Globals.rc.readSharedArray(59)
        return MapLocation(x - 1, y - 1) if x > 0 else None

    @staticmethod
    def beingThrown():
        if not Globals.hasSqueaked:
            Globals.rc.squeak(7 + Globals.locationLastRound.directionTo(Globals.rc.getLocation()).getDirectionOrderNum())
        Globals.hasSqueaked = True

    @staticmethod
    def getAlliesThrown():
        sz = 0
        for msg in Globals.newestSqueaks:
            if 8 <= msg.getBytes() < 16:
                sz += 1
        ret = [None] * sz
        sz = 0
        for msg in Globals.newestSqueaks:
            if 8 <= msg.getBytes() < 16:
                # TODO: FINISH THIS ONCE THE STUFF IS ANSWERED IN #BUG REPORTS
                ret[sz] = Thrown(Globals.rc.getLocation(), Globals.rc.getDirection())
                sz += 1
        return ret

    @staticmethod
    def squeakForSacrifices(loc):
        msg = (1 << 24) + (loc.x << 6) + loc.y
        if not Globals.hasSqueaked:
            Globals.rc.squeak(msg)
            Globals.hasSqueaked = True

    @staticmethod
    def squeakForSacrificesToo(loc):
        msg = (1 << 29) + (loc.x << 6) + loc.y
        if not Globals.hasSqueaked:
            Globals.rc.squeak(msg)
            Globals.hasSqueaked = True

    @staticmethod
    def getSacrifices():
        secondary = None
        for m in Globals.newestSqueaks:
            if m.getBytes() > 0:
                msg = m.getBytes()
                if (msg & (1 << 24)) > 0:
                    y = msg & 0b111111
                    msg = msg >> 6
                    x = msg & 0b111111
                    return MapLocation(x, y)
                if (msg & (1 << 29)) > 0:
                    y = msg & 0b111111
                    msg = msg >> 6
                    x = msg & 0b111111
                    secondary = MapLocation(x + 1000, y + 1000)
        return secondary
