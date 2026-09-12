# Port of philip_06/utils/Actions.java. See py/CONVENTIONS.md.
# Bot-internal imports use the module form (`import X` / `from pkg import X`)
# and sit below the class because this bot's import graph is cyclic - names
# resolve at call time, like the reechee port's `import RobotPlayer` +
# `RobotPlayer.RobotPlayer.*`.
from api import *

# Java: import java.util.HashMap -> dict


class Actions:
    @staticmethod
    def spawn(rc, type, dest):
        # Java: RobotPlayer.rng.nextBoolean() - api.Random (the java.util.Random
        # stand-in) has no nextBoolean(); Java's is a fair coin (next(1) != 0),
        # so nextInt(2) != 0 is the faithful stand-in (same as the C++ port).
        if dest == MapLocation(61, 61) and Tower.Tower.target is not None and RobotPlayer.RobotPlayer.rng.nextInt(2) != 0:
            dest = Tower.Tower.target
        for dir in Direction.allDirections():
            if rc.canBuildRobot(type, rc.getLocation().add(dir)):
                rc.buildRobot(type, rc.getLocation().add(dir))
                if rc.canSendMessage(rc.getLocation().add(dir)):
                    rc.sendMessage(rc.getLocation().add(dir), Comms.Comms.encodeLocation(dest))
                return True
        return False

    badRuins = {}  # static HashMap<MapLocation,Integer>

    @staticmethod
    def makeTower(rc, ruin):
        if ruin is None:
            return
        if rc.getNumberTowers() == GameConstants.MAX_NUMBER_OF_TOWERS:
            return
        if ruin in Actions.badRuins:
            if rc.getRoundNum() - Actions.badRuins[ruin] < 10:
                return
            else:
                del Actions.badRuins[ruin]
        if rc.getLocation().distanceSquaredTo(ruin) > 9:
            Mopper.Mopper.moveTowardsMindlessly(rc, ruin)
            return
        type = None
        if rc.senseMapInfo(ruin.add(Direction.NORTH)).getMark().isAlly():
            type = UnitType.LEVEL_ONE_PAINT_TOWER
        elif rc.senseMapInfo(ruin.add(Direction.EAST)).getMark().isAlly():
            type = UnitType.LEVEL_ONE_MONEY_TOWER
        elif rc.senseMapInfo(ruin.add(Direction.SOUTH)).getMark().isAlly():
            type = UnitType.LEVEL_ONE_DEFENSE_TOWER
        if type is None:
            if RobotPlayer.RobotPlayer.rng.nextInt(3) == 1 or rc.getMoney() > 5000:
                type = UnitType.LEVEL_ONE_PAINT_TOWER
                if rc.canMark(ruin.add(Direction.NORTH)):
                    rc.mark(ruin.add(Direction.NORTH), False)
            else:
                type = UnitType.LEVEL_ONE_MONEY_TOWER
                if rc.canMark(ruin.add(Direction.EAST)):
                    rc.mark(ruin.add(Direction.EAST), False)
        best = None
        _cost = 0
        _colour = False
        arr = rc.getTowerPattern(type)
        for i in range(-2, 3):
            for j in range(-2, 3):
                if i == 0 and j == 0:
                    continue
                if rc.canSenseLocation(ruin.translate(i, j)):
                    cur = rc.senseMapInfo(ruin.translate(i, j)).getPaint()
                    if cur == PaintType.EMPTY or (cur == PaintType.ALLY_PRIMARY and arr[i + 2][j + 2]) or (cur == PaintType.ALLY_SECONDARY and not arr[i + 2][j + 2]):
                        _cost += 1
                        if best is None or rc.getLocation().distanceSquaredTo(best) > rc.getLocation().distanceSquaredTo(ruin.translate(i, j)):
                            best = ruin.translate(i, j)
                            _colour = arr[i + 2][j + 2]
                    elif cur == PaintType.ENEMY_PRIMARY or cur == PaintType.ENEMY_SECONDARY:
                        _cost = 1000000
        if _cost >= 25:
            Actions.badRuins[ruin] = rc.getRoundNum()
        elif best is not None:
            rc.setIndicatorDot(best, 255, 0, 0)
            if rc.canAttack(best):
                rc.attack(best, _colour)
        if len(rc.senseNearbyRobots(ruin, rc.getLocation().distanceSquaredTo(ruin), rc.getTeam())) == 0:
            if best is not None and rc.getLocation().distanceSquaredTo(best) > 9:
                Mopper.Mopper.moveTowardsMindlessly(rc, best)
            else:
                Mopper.Mopper.moveTowardsMindlessly(rc, ruin)
        if rc.canCompleteTowerPattern(type, ruin):
            rc.completeTowerPattern(type, ruin)

    @staticmethod
    def getPaint(rc):
        if rc.getHealth() <= 40:
            return
        for loc in rc.senseNearbyRuins(-1):
            bot = rc.senseRobotAtLocation(loc)
            if bot is None:
                continue
            if rc.canTransferPaint(loc, -min(rc.getType().paintCapacity - rc.getPaint(), bot.paintAmount)):
                rc.transferPaint(loc, -min(rc.getType().paintCapacity - rc.getPaint(), bot.paintAmount))


# Java's file-level imports, deferred below the class: several sibling modules
# do `from utils.Actions import Actions`, which only resolves once the class
# object already exists in the partially-initialised module.
import RobotPlayer
from Helper import Comms
from Helper import Pathfind  # imported by the Java file, unused in this file
from roles import Mopper
from roles import Tower
