# Port of philip_06/RobotPlayer.java. See py/CONVENTIONS.md.
# Bot-internal imports use the module form (`import X` / `from pkg import X`)
# because this bot's import graph is cyclic - names resolve at call time, like
# the reechee port's `import RobotPlayer` + `RobotPlayer.RobotPlayer.*`.
import traceback

from api import *


class RobotPlayer:
    # @SuppressWarnings("unused")
    rng = None  # Java: java.util.Random rng = null -> api.Random
    rush = False
    fill = False
    retreat = False
    build = False
    built = False
    aliveTurns = 0
    lastSeenEnemy = 0
    lastEnemyTower = None  # Java: declared without initializer -> null

    @staticmethod
    def run(rc):
        if rc.getType() != UnitType.SOLDIER and rc.getType() != UnitType.MOPPER:
            Constants.Constants.setup(rc)
        if RobotPlayer.rng is None:
            RobotPlayer.rng = Random(rc.getID() ^ 6969)
        RobotPlayer.rng = Random(rc.getID() ^ 6969)
        Mopper.Mopper.pastLocs = []  # Java: new ArrayList<>()
        RobotPlayer.lastSeenEnemy = rc.getRoundNum()
        while True:
            # Java: rc.getTeam().opponent() -> api opponent(rc.getTeam())
            if len(rc.senseNearbyRobots(-1, opponent(rc.getTeam()))) > 0:
                RobotPlayer.lastSeenEnemy = rc.getRoundNum()
            RobotPlayer.aliveTurns += 1
            valid = 0
            for ruin in rc.senseNearbyRuins(-1):
                if rc.senseRobotAtLocation(ruin) is None:
                    valid += 1
                    break
                elif rc.senseRobotAtLocation(ruin).getTeam() == rc.getTeam():
                    if rc.canSenseLocation(ruin.add(Direction.SOUTH)) and rc.canRemoveMark(ruin.add(Direction.SOUTH)):
                        rc.removeMark(ruin.add(Direction.SOUTH))
            if valid == 0:
                for loc in rc.senseNearbyMapInfos(8):
                    if loc.hasRuin() or loc.isWall():
                        valid += 1
                # Now consider conflict between other SRPs
                for loc in rc.senseNearbyMapInfos():
                    if loc.getMark().isSecondary():
                        if not rc.canSenseLocation(loc.getMapLocation().add(Direction.NORTH)) or (rc.canSenseLocation(loc.getMapLocation().add(Direction.NORTH)) and not rc.senseMapInfo(loc.getMapLocation().add(Direction.NORTH)).hasRuin()):
                            if loc.getMapLocation().distanceSquaredTo(rc.getLocation()) != 16:
                                valid += 1
            # Check that there is actually enough space
            if valid == 0 and rc.canMark(rc.getLocation()):
                if rc.getLocation().x > 1 and rc.getLocation().x < rc.getMapWidth() - 2:
                    if rc.getLocation().y > 1 and rc.getLocation().y < rc.getMapHeight() - 2:
                        rc.mark(rc.getLocation(), True)
            for loc in rc.senseNearbyMapInfos():
                if loc.hasRuin():
                    if rc.canCompleteTowerPattern(UnitType.LEVEL_ONE_PAINT_TOWER, loc.getMapLocation()):
                        # Java: Build.toFinish.getLast() == loc... is a MapLocation
                        # reference comparison -> `is`
                        if rc.getType() == UnitType.SOLDIER and Build.Build.movingTowardsToFinish and Build.Build.toFinish[-1] is loc.getMapLocation():
                            Build.Build.toFinish.pop()
                            Build.Build.movingTowardsToFinish = False
                        rc.completeTowerPattern(UnitType.LEVEL_ONE_PAINT_TOWER, loc.getMapLocation())
                        RobotPlayer.built = True
                    if rc.canCompleteTowerPattern(UnitType.LEVEL_ONE_MONEY_TOWER, loc.getMapLocation()):
                        if rc.getType() == UnitType.SOLDIER and Build.Build.movingTowardsToFinish and Build.Build.toFinish[-1] is loc.getMapLocation():
                            Build.Build.toFinish.pop()
                            Build.Build.movingTowardsToFinish = False
                        rc.completeTowerPattern(UnitType.LEVEL_ONE_MONEY_TOWER, loc.getMapLocation())
                        RobotPlayer.built = True
                    if rc.canCompleteTowerPattern(UnitType.LEVEL_ONE_DEFENSE_TOWER, loc.getMapLocation()):
                        if rc.getType() == UnitType.SOLDIER and Build.Build.movingTowardsToFinish and Build.Build.toFinish[-1] is loc.getMapLocation():
                            Build.Build.toFinish.pop()
                            Build.Build.movingTowardsToFinish = False
                        rc.completeTowerPattern(UnitType.LEVEL_ONE_DEFENSE_TOWER, loc.getMapLocation())
                        RobotPlayer.built = True
                if loc.getMark().isAlly() and loc.getMark().isSecondary():
                    if rc.canCompleteResourcePattern(loc.getMapLocation()):
                        rc.completeResourcePattern(loc.getMapLocation())
            try:
                t = rc.getType()
                if t == UnitType.SOLDIER:
                    Soldier.Soldier.run(rc)
                elif t == UnitType.MOPPER:
                    Mopper.Mopper.run(rc)
                elif t == UnitType.SPLASHER:
                    Splasher.Splasher.run(rc)
                else:
                    Tower.Tower.run(rc)
                Clock.doYield()
            except GameActionException:
                print("GameActionException")
                traceback.print_exc()

            except Exception:
                print("Exception")
                traceback.print_exc()


# Java's file-level imports are placed below the class: the cyclic bot modules
# (roles/*.py) do `from RobotPlayer import RobotPlayer`, which only resolves
# once the RobotPlayer class object already exists in the partial module.
import Soldier  # Java: same package philip_06, no import statement needed
from SoldierState import Build
from roles import Mopper
from roles import Splasher
from roles import Tower
from utils import Constants
