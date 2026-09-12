# Port of philip_06/utils/Utils.java. See py/CONVENTIONS.md.
import math

from api import *


class Utils:
    @staticmethod
    def distance(a, b):
        return max(abs(a.x - b.x), abs(a.y - b.y))

    @staticmethod
    def closest(loc, locs):
        closest = None
        minDist = 1000000
        for l in locs:
            dist = Utils.distance(loc, l)
            if dist < minDist:
                minDist = dist
                closest = l
        return closest

    @staticmethod
    def closestInfo(loc, locs):
        closest = None
        minDist = 1000000
        for l in locs:
            dist = Utils.distance(loc, l.getMapLocation())
            if dist < minDist:
                minDist = dist
                closest = l
        return closest

    @staticmethod
    def threatLevel(loc, rc):
        oppSpawn = MapLocation(rc.getMapWidth() - Constants.Constants.spawn.x, rc.getMapHeight() - Constants.Constants.spawn.y)
        return -math.sqrt(loc.distanceSquaredTo(oppSpawn)) + math.sqrt(loc.distanceSquaredTo(Constants.Constants.spawn))

    @staticmethod
    def spawn(rc, type):
        for dir in Constants.Constants.directions:
            if rc.canBuildRobot(type, rc.getLocation().add(dir)):
                rc.buildRobot(type, rc.getLocation().add(dir))
                return True
        return False

    @staticmethod
    def getColour(loc):
        if loc.y % 3 != 2:
            return (loc.x + loc.y) % 2 == 0
        if abs(loc.x - loc.y) % 4 == 0:
            return False
        return (loc.x + loc.y) % 2 == 0
        #center is loc.y%3==2 && Math.abs(loc.x-loc.y)%4==0

    @staticmethod
    def getPaint(loc):
        if Utils.getColour(loc):
            return PaintType.ALLY_SECONDARY
        return PaintType.ALLY_PRIMARY

    @staticmethod
    def checkResources(rc):
        for loc in rc.getAllLocationsWithinRadiusSquared(rc.getLocation(), -1):
            if loc.y % 3 == 2 and abs(loc.x - loc.y) % 4 == 0 and rc.canCompleteResourcePattern(loc):
                rc.completeResourcePattern(loc)

    @staticmethod
    def attackTowers(rc):
        if Constants.Constants.closestEnemyTower is None:
            return
        if rc.canAttack(Constants.Constants.closestEnemyTower):
            rc.attack(Constants.Constants.closestEnemyTower, Utils.getColour(Constants.Constants.closestEnemyTower))
        if rc.canMove(rc.getLocation().directionTo(Constants.Constants.closestEnemyTower).opposite()):
            rc.move(rc.getLocation().directionTo(Constants.Constants.closestEnemyTower).opposite())

    @staticmethod
    def closestEnemyTower(rc):
        ans = None
        for loc in rc.senseNearbyRuins(-1):
            info = rc.senseRobotAtLocation(loc)
            if info is None or info.getTeam() == rc.getTeam():
                continue
            if ans is None or info.location.distanceSquaredTo(rc.getLocation()) < ans.location.distanceSquaredTo(rc.getLocation()):
                ans = info
        return ans

    @staticmethod
    def shuffleArray(array):
        for i in range(len(array) - 1, 0, -1):
            # Constants.rng is philip_06.utils.Random: nextInt() is always
            # non-negative, so % matches Java here.
            index = Constants.Constants.rng.nextInt() % (i + 1)
            if index != i:
                temp = array[index]
                array[index] = array[i]
                array[i] = temp

    @staticmethod
    def closestRuin(rc):
        best = None
        for loc in rc.senseNearbyRuins(-1):
            if rc.senseRobotAtLocation(loc) is None and (best is None or best.distanceSquaredTo(rc.getLocation()) > loc.distanceSquaredTo(rc.getLocation())):
                best = loc
        return best


# Java's file-level imports, deferred below the class: Pathfinding.py and
# Splasher.py do `from utils.Utils import Utils`, which only resolves once
# the class object already exists in the partially-initialised module.
# Java `import static philip_06.utils.Constants.rng` -> Constants.Constants.rng.
from utils import Constants
