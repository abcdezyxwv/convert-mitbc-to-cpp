# Port of philip_06/utils/Constants.java. See py/CONVENTIONS.md.
# Bot-internal imports use the module form (`import X` / `from pkg import X`)
# and sit below the class because this bot's import graph is cyclic - names
# resolve at call time, like the reechee port's `import RobotPlayer` +
# `RobotPlayer.RobotPlayer.*`.
from api import *


class Constants:
    @staticmethod
    def setup(rc):
        # Java: file-level `import philip_06.Pathfinding` - deferred into this
        # method because Pathfinding.py imports utils.Constants/utils.Utils
        # back with class-form imports (circular); call-time is safe.
        import Pathfinding
        Constants.rc = rc
        Constants.rng = Random(rc.getID())
        Constants.spawn = rc.getLocation()
        Constants.pathfind = Pathfinding.Pathfinding()

    rc = None  # RobotController
    directions = [
        Direction.NORTH,
        Direction.NORTHEAST,
        Direction.EAST,
        Direction.SOUTHEAST,
        Direction.SOUTH,
        Direction.SOUTHWEST,
        Direction.WEST,
        Direction.NORTHWEST,
    ]
    cardinalDirections = [
        Direction.NORTH,
        Direction.EAST,
        Direction.SOUTH,
        Direction.WEST,
    ]
    ordinalDirections = [
        Direction.NORTHEAST,
        Direction.SOUTHEAST,
        Direction.SOUTHWEST,
        Direction.NORTHWEST,
    ]
    rng = None  # Java: null until setup() runs
    pathfind = None  # Java: null until setup() runs
    spawn = None  # Java: null until setup() runs
    destination = None
    closestTower = None
    closestPaintTower = None
    closestPaintTowerHasPaint = None
    closestEnemyTower = None
    noEnemyTowers = 0
    noEnemyRobots = 0
    noAlliedRobots = 0
    turnsAlive = 0

    @staticmethod
    def update(rc):
        Constants.turnsAlive += 1
        Constants.noEnemyTowers = 0
        Constants.noEnemyRobots = 0
        Constants.noAlliedRobots = 0
        Constants.destination = None
        fakeRuins = rc.senseNearbyRuins(-1)
        for loc in fakeRuins:
            if rc.senseRobotAtLocation(loc) is None and (Constants.destination is None or rc.getLocation().distanceSquaredTo(loc) < rc.getLocation().distanceSquaredTo(Constants.destination)):
                Constants.destination = loc
        if Constants.closestTower is not None and rc.canSenseLocation(Constants.closestTower) and rc.senseRobotAtLocation(Constants.closestTower) is None:
            Constants.closestTower = None
        if Constants.closestPaintTower is not None and rc.canSenseLocation(Constants.closestPaintTower) and rc.senseRobotAtLocation(Constants.closestPaintTower) is None:
            Constants.closestPaintTower = None
        if Constants.closestPaintTowerHasPaint is not None and rc.canSenseLocation(Constants.closestPaintTowerHasPaint) and (rc.senseRobotAtLocation(Constants.closestPaintTowerHasPaint) is None or rc.senseRobotAtLocation(Constants.closestPaintTowerHasPaint).getPaintAmount() <= Settings.minTowerPaintToTransfer * 2):
            Constants.closestPaintTowerHasPaint = None
        Constants.closestEnemyTower = None
        robots = rc.senseNearbyRobots(-1)
        for robot in robots:
            if robot.getTeam() == rc.getTeam():
                if robot.getType().isRobotType():
                    Constants.noAlliedRobots += 1
                    rc.setIndicatorDot(robot.getLocation(), 0, 255, 0)
                if robot.getType().isTowerType() and (Constants.closestTower is None or Utils.Utils.distance(rc.getLocation(), robot.getLocation()) < Utils.Utils.distance(rc.getLocation(), Constants.closestTower)):
                    Constants.closestTower = robot.getLocation()
                if robot.getType().isTowerType() and rc.getType().paintPerTurn > 0 and (Constants.closestPaintTower is None or Utils.Utils.distance(rc.getLocation(), robot.getLocation()) < Utils.Utils.distance(rc.getLocation(), Constants.closestPaintTower)) and robot.getTeam() == rc.getTeam():
                    Constants.closestPaintTower = robot.getLocation()
                if (robot.getType().isTowerType() and robot.getPaintAmount() > Settings.minTowerPaintToTransfer * 2) and (Constants.closestPaintTowerHasPaint is None or Utils.Utils.distance(rc.getLocation(), robot.getLocation()) < Utils.Utils.distance(rc.getLocation(), Constants.closestPaintTowerHasPaint)):
                    Constants.closestPaintTowerHasPaint = robot.getLocation()
            else:
                if robot.getType().isRobotType():
                    Constants.noEnemyRobots += 1
                elif robot.getType().isTowerType():
                    Constants.noEnemyTowers += 1
                    if Constants.closestEnemyTower is None or Utils.Utils.distance(rc.getLocation(), robot.getLocation()) < Utils.Utils.distance(rc.getLocation(), Constants.closestEnemyTower):
                        Constants.closestEnemyTower = robot.getLocation()


# Java's file-level imports, deferred below the class: Pathfinding.py and
# Splasher.py do `from utils.Constants import Constants`, which only resolves
# once the class object already exists in the partially-initialised module.
# Utils/Settings/Random are same-package (`philip_06.utils`) - Java needs no
# import statement for them; utils.Random is NOT java.util.Random.
from utils import Utils
from utils.Settings import Settings
from utils.Random import Random
