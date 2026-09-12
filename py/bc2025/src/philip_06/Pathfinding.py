# Port of philip_06/Pathfinding.java. See py/CONVENTIONS.md.
from api import *
from utils import Constants
from utils.Settings import Settings
from utils import Utils
from roles import Mopper

# Java: import static philip_06.utils.Constants.rng -> written Constants.rng
# (the field is assigned in Constants.setup, so it cannot be bound at import time)


class Pathfinding:
    exploreDirection = None  # Java: instance field
    dest = None

    @staticmethod
    def setDest(rc, loc):
        if loc is None:
            Pathfinding.dest = MapLocation(Constants.Constants.rng.nextInt() % rc.getMapWidth(), Constants.Constants.rng.nextInt() % rc.getMapHeight())
        else:
            Pathfinding.dest = loc

    @staticmethod
    def makeMove(rc):
        if Pathfinding.dest is None: Pathfinding.dest = MapLocation(rc.getMapWidth() // 2, rc.getMapHeight() // 2)
        rc.setIndicatorLine(rc.getLocation(), Pathfinding.dest, 0, 255, 255)
        Mopper.Mopper.moveTowardsMindlessly(rc, Pathfinding.dest)

    @staticmethod
    def move(rc, loc):
        Pathfinding.setDest(rc, loc)
        Pathfinding.makeMove(rc)

    def explore(self, rc):
        Mopper.Mopper.explore(rc)

    def rush(self, rc):
        target = None
        cur = -100000
        scan = rc.senseNearbyMapInfos()
        #System.out.println(Clock.getBytecodeNum());
        temp = [0] * len(scan)
        for i in range(len(temp)):
            temp[i] = i
        #System.out.println(Clock.getBytecodeNum());
        Utils.Utils.shuffleArray(temp)
        #System.out.println(Clock.getBytecodeNum());
        for i in range(len(scan)):
            loc = scan[temp[i]]
            if loc.isPassable():
                if target is None or Utils.Utils.threatLevel(loc.getMapLocation(), rc) > cur:
                    target = loc.getMapLocation()
                    cur = Utils.Utils.threatLevel(loc.getMapLocation(), rc)
        #System.out.println(Clock.getBytecodeNum());
        if target is not None and rc.canSenseLocation(target) and rc.senseMapInfo(target).getPaint().isAlly():
            target = None
        if target is None:
            self.explore(rc)
        else:
            Pathfinding.setDest(rc, target)
            Pathfinding.makeMove(rc)

    def turtle(self, rc):
        target = None
        scan = rc.senseNearbyMapInfos()
        temp = [0] * len(scan)
        for i in range(len(temp)):
            temp[i] = i
        Utils.Utils.shuffleArray(temp)
        for i in range(len(scan)):
            loc = scan[temp[i]]
            if loc.isPassable():
                if (target is None or loc.getMapLocation().distanceSquaredTo(rc.getLocation()) < target.distanceSquaredTo(rc.getLocation())) and loc.getPaint() == PaintType.EMPTY:
                    target = loc.getMapLocation()
        if target is None:
            self.explore(rc)
        else:
            Pathfinding.setDest(rc, target)
            Pathfinding.makeMove(rc)

    def retreat(self, rc):
        rc.setIndicatorString("retreat")
        if Constants.Constants.closestPaintTowerHasPaint is not None:
            rc.setIndicatorLine(rc.getLocation(), Constants.Constants.closestPaintTowerHasPaint, 0, 0, 255)
        if rc.getPaint() <= Settings.lowPaint and Constants.Constants.closestPaintTowerHasPaint is not None:
            Pathfinding.setDest(rc, Constants.Constants.closestPaintTowerHasPaint)
            rc.setIndicatorString("found paint")
        elif Constants.Constants.closestPaintTower is not None:
            Pathfinding.setDest(rc, Constants.Constants.closestPaintTower)
            rc.setIndicatorString("found paint tower")
        else:
            rc.setIndicatorString("explore")
            self.explore(rc)
            return
        if rc.getPaint() <= Settings.lowPaint:
            if Constants.Constants.closestTower is not None and rc.canSenseLocation(Constants.Constants.closestTower):
                if rc.canTransferPaint(Constants.Constants.closestTower, -min(rc.getType().paintCapacity - rc.getPaint(), rc.senseRobotAtLocation(Constants.Constants.closestTower).paintAmount - Settings.minTowerPaintToTransfer)):
                    rc.transferPaint(Constants.Constants.closestTower, -min(rc.getType().paintCapacity - rc.getPaint(), rc.senseRobotAtLocation(Constants.Constants.closestTower).paintAmount - Settings.minTowerPaintToTransfer))
        Pathfinding.makeMove(rc)

    destination = None
    TurnsWasted = 0

    @staticmethod
    def canMoveFriendly(rc, dir):
        return rc.canMove(dir) and rc.senseMapInfo(rc.getLocation().add(dir)).getPaint().isAlly()

    @staticmethod
    def wander(rc):
        if Pathfinding.destination is None or Pathfinding.destination == rc.getLocation() or rc.getRoundNum() % 69 == 0 or Pathfinding.TurnsWasted >= 3:
            Pathfinding.destination = MapLocation(Constants.Constants.rng.nextInt() % rc.getMapWidth(), Constants.Constants.rng.nextInt() % rc.getMapHeight())
            Pathfinding.TurnsWasted = 0
        dir = rc.getLocation().directionTo(Pathfinding.destination)
        if Pathfinding.canMoveFriendly(rc, dir):
            rc.move(dir)
            return
        dir = dir.rotateLeft()
        if Pathfinding.canMoveFriendly(rc, dir):
            rc.move(dir)
            return
        dir = dir.rotateRight()
        dir = dir.rotateRight()
        if Pathfinding.canMoveFriendly(rc, dir):
            rc.move(dir)
            return
        Pathfinding.TurnsWasted += 1
        dir = dir.rotateRight()
        if Pathfinding.canMoveFriendly(rc, dir):
            rc.move(dir)
            return
        dir = dir.opposite()
        if Pathfinding.canMoveFriendly(rc, dir):
            rc.move(dir)
            return
        dir = dir.rotateLeft()
        if Pathfinding.canMoveFriendly(rc, dir):
            rc.move(dir)
            return
        dir = dir.rotateLeft()
        dir = dir.rotateLeft()
        if Pathfinding.canMoveFriendly(rc, dir):
            rc.move(dir)
            return
        dir = dir.rotateRight()
        if Pathfinding.canMoveFriendly(rc, dir):
            rc.move(dir)
            return

    @staticmethod
    def findClosestAllyCell(rc):
        nearby = rc.senseNearbyMapInfos()
        closest = None
        for mi in nearby:
            if not mi.getPaint().isAlly() or not mi.isPassable():
                continue
            if closest is None or rc.getLocation().distanceSquaredTo(mi.getMapLocation()) < rc.getLocation().distanceSquaredTo(closest.getMapLocation()):
                closest = mi
        return closest

    @staticmethod
    def findFurthestAllyCell(rc):
        nearby = rc.senseNearbyMapInfos()
        furthest = None
        for mi in nearby:
            if not mi.getPaint().isAlly() or not mi.isPassable():
                continue
            if furthest is None or rc.getLocation().distanceSquaredTo(mi.getMapLocation()) > rc.getLocation().distanceSquaredTo(furthest.getMapLocation()):
                furthest = mi
        return furthest

    @staticmethod
    def findClosestEnemyCell(rc):
        nearby = rc.senseNearbyMapInfos()
        closest = None
        for mi in nearby:
            if not mi.getPaint().isEnemy() or not mi.isPassable():
                continue
            if closest is None or rc.getLocation().distanceSquaredTo(mi.getMapLocation()) < rc.getLocation().distanceSquaredTo(closest.getMapLocation()):
                closest = mi
        return closest

    @staticmethod
    def findFurthestEnemyCell(rc):
        nearby = rc.senseNearbyMapInfos()
        furthest = None
        for mi in nearby:
            if not mi.getPaint().isEnemy() or not mi.isPassable():
                continue
            if furthest is None or rc.getLocation().distanceSquaredTo(mi.getMapLocation()) > rc.getLocation().distanceSquaredTo(furthest.getMapLocation()):
                furthest = mi
        return furthest
