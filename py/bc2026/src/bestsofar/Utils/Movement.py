# Port of bestsofar/Utils/Movement.java. See py/CONVENTIONS.md.
from api import *
from Utils.Globals import Globals
from Utils.Navigator import Navigator
from Utils.Vision import Vision


class Movement(Globals):

    targetLoc = None
    explorePoints = None  # MapLocation[]
    epSize = 0
    turnsStuck = 0
    bestDist = 0

    @staticmethod
    def indicateAllExplorePoints():
        for loc in Movement.explorePoints:
            Globals.rc.setIndicatorDot(loc, 100, 255, 255)

    @staticmethod
    def setNextExplorePoint():
        Movement.targetLoc = Movement.explorePoints[Globals.rng.nextInt(Movement.epSize)]
        Movement.turnsStuck = 0
        Movement.bestDist = Globals.rc.getLocation().distanceSquaredTo(Movement.targetLoc)

    @staticmethod
    def explore():
        # if theres no target, or reached target, or see target but unreachable
        if Movement.targetLoc is None or Globals.rc.getLocation() == Movement.targetLoc or Movement.turnsStuck > 14 or (Vision.hasSeenLocation(Movement.targetLoc) and not Vision.sensePassability(Movement.targetLoc)):
            Movement.setNextExplorePoint()

        Navigator.moveTo(Movement.targetLoc, True)

        newDist = Globals.rc.getLocation().distanceSquaredTo(Movement.targetLoc)
        if newDist < Movement.bestDist:
            Movement.bestDist = newDist
            Movement.turnsStuck = 0
        else:
            Movement.turnsStuck += 1

    @staticmethod
    def init():
        Movement.explorePoints = [None] * 144

        # Java: for (int i = mapWidth/15; i < mapWidth/2; i += (i+6)/2)
        # (non-constant step -> while; all operands non-negative so // is exact)
        i = Globals.mapWidth // 15
        while i < Globals.mapWidth // 2:
            j = Globals.mapHeight // 15
            while j < Globals.mapHeight // 2:
                Movement.explorePoints[Movement.epSize] = MapLocation(i, j)  # Java: explorePoints[epSize++]
                Movement.epSize += 1
                Movement.explorePoints[Movement.epSize] = MapLocation(Globals.mapWidth - i - 1, j)
                Movement.epSize += 1
                Movement.explorePoints[Movement.epSize] = MapLocation(i, Globals.mapHeight - j - 1)
                Movement.epSize += 1
                Movement.explorePoints[Movement.epSize] = MapLocation(Globals.mapWidth - i - 1, Globals.mapHeight - j - 1)
                Movement.epSize += 1
                j += (j + 6) // 2
            i += (i + 6) // 2

    @staticmethod
    def exploreSafe():
        pass

    @staticmethod
    def circle(loc):
        if not Globals.rc.isMovementReady():
            return
        target = loc.add(Globals.rc.getLocation().directionTo(loc).rotateLeft())
        if not Globals.rc.onTheMap(target):
            target = loc
        Navigator.moveTo(target, False)
