# Port of philip_06/Soldier.java. See py/CONVENTIONS.md.
# Bot-internal imports use the module form (`import X` / `from pkg import X`)
# because this bot's import graph is cyclic (Soldier <-> SoldierState.*,
# Helper.Comms, roles.*) - names resolve at call time, like the reechee port's
# `import RobotPlayer` + `RobotPlayer.RobotPlayer.*`.
import math

from api import *
import RobotPlayer
from Helper import Comms
from SoldierState import Attack
from SoldierState import Build
from SoldierState import Fill
from SoldierState import Retreat
from roles import Mopper


class Soldier:
    builder = False
    turnsAlive = 0
    spawn = None
    paintTowers = set()
    ruins = None
    messenger = False
    messageLoc = None
    priority = 0
    roundNum = 0
    message = 0
    moneyLastTurn = 0
    defaultFill = False
    attack = None

    @staticmethod
    def onMap(rc, curr):
        return curr.x >= 0 and curr.x < rc.getMapWidth() and curr.y >= 0 and curr.y < rc.getMapHeight()

    @staticmethod
    def scale(value, originalMin, originalMax, targetMin, targetMax):
        # Java: Math.round(x) is floor(x + 0.5); Python round() is banker's.
        return int(math.floor(targetMin + (value - originalMin) * (targetMax - targetMin) / (originalMax - originalMin) + 0.5))

    @staticmethod
    def retreat(rc):
        bestOpt = None
        for curr in Soldier.paintTowers:
            if bestOpt is None or (rc.getLocation().distanceSquaredTo(curr) < rc.getLocation().distanceSquaredTo(bestOpt) and (not rc.canSenseLocation(bestOpt) or rc.senseRobotAtLocation(bestOpt) is not None)):
                bestOpt = curr
        if bestOpt is None:
            bestOpt = MapLocation(RobotPlayer.RobotPlayer.rng.nextInt(rc.getMapWidth()), RobotPlayer.RobotPlayer.rng.nextInt(rc.getMapHeight()))
            Mopper.Mopper.moveTowardsMindfully(rc, bestOpt)
            return
        transfer = rc.getType().paintCapacity - rc.getPaint()
        if rc.canSenseLocation(bestOpt) and rc.senseRobotAtLocation(bestOpt) is not None:
            transfer = min(transfer, rc.senseRobotAtLocation(bestOpt).getPaintAmount())
            #rc.setIndicatorString(Integer.toString(transfer));
            if rc.canTransferPaint(bestOpt, -transfer):
                rc.transferPaint(bestOpt, -transfer)
        Mopper.Mopper.moveTowardsMindfully(rc, bestOpt)

    @staticmethod
    def stealPaint(rc):
        if rc.getPaint() >= 180 or not rc.isActionReady():
            return
        for ri in rc.senseNearbyRobots(2, rc.getTeam()):
            if ri.type != UnitType.MOPPER and ri.type != UnitType.SPLASHER and ri.type != UnitType.SOLDIER:
                if ri.getPaintAmount() > 150:
                    amt = min(ri.getPaintAmount() - 150, 200 - rc.getPaint())
                    if rc.canTransferPaint(ri.getLocation(), -amt):
                        rc.transferPaint(ri.getLocation(), -amt)
                        return
                    ret = Mopper.Mopper.moveTowardsMindfully(rc, ri.getLocation())
                    if not ret:
                        return
                    if rc.canTransferPaint(ri.getLocation(), -amt):
                        rc.transferPaint(ri.getLocation(), -amt)
                        return
                return

    @staticmethod
    def donatePaint(rc):
        if rc.getPaint() <= 60:
            return
        lowest = None
        for ri in rc.senseNearbyRobots(8, rc.getTeam()):
            if lowest is None or ri.getPaintAmount() < lowest.getPaintAmount():
                lowest = ri
        for ml in Soldier.ruins:
            ri = rc.senseRobotAtLocation(ml)
            if ri is None:
                continue
            if ri.type == UnitType.LEVEL_ONE_PAINT_TOWER or ri.type == UnitType.LEVEL_TWO_PAINT_TOWER or ri.type == UnitType.LEVEL_THREE_PAINT_TOWER:
                if ri.getPaintAmount() <= 600:
                    if lowest is None or lowest.getType().isRobotType():
                        lowest = ri
        if lowest is None:
            return
        if lowest.type == UnitType.SPLASHER and lowest.getPaintAmount() >= 240:
            return
        if lowest.type == UnitType.MOPPER and lowest.getPaintAmount() >= 45:
            return
        if lowest.type == UnitType.SOLDIER and lowest.getPaintAmount() >= 120:
            return
        if lowest.type == UnitType.SPLASHER:
            amt = min(300 - lowest.getPaintAmount(), rc.getPaint() - 40)
        elif lowest.type == UnitType.MOPPER:
            amt = min(100 - lowest.getPaintAmount(), rc.getPaint() - 50)
        elif lowest.type == UnitType.SOLDIER:
            amt = min(200 - lowest.getPaintAmount(), rc.getPaint() - 40)
        else:
            amt = min(1000 - lowest.getPaintAmount(), rc.getPaint() - 50)
        if not rc.canTransferPaint(lowest.getLocation(), amt):
            Mopper.Mopper.moveTowardsMindlessly(rc, lowest.getLocation())
        if rc.canTransferPaint(lowest.getLocation(), amt):
            rc.transferPaint(lowest.getLocation(), amt)

    @staticmethod
    def run(rc):
        Soldier.turnsAlive += 1
        Soldier.ruins = rc.senseNearbyRuins(-1)

        # Get messages
        if rc.getHealth() <= 40:
            Soldier.donatePaint(rc)
        else:
            Soldier.stealPaint(rc)
        Comms.Comms.getMsg(rc)
        Comms.Comms.sendMsg(rc)

        # Maintain list of paint towers
        for loc in rc.senseNearbyRuins(-1):
            tower = rc.senseRobotAtLocation(loc)
            # Java: getTeam() == getTeam().opponent() - always false
            if tower is None or rc.getTeam() == opponent(rc.getTeam()):
                if tower is not None:
                    RobotPlayer.RobotPlayer.lastEnemyTower = loc
                Soldier.paintTowers.discard(loc)
                continue
            if tower.getPaintAmount() >= 150 or tower.getType().paintPerTurn > 0:
                Soldier.paintTowers.add(loc)
            else:
                Soldier.paintTowers.discard(loc)
        # Precompute stuff when it just spawned
        if Soldier.turnsAlive == 1:
            Soldier.builder = RobotPlayer.RobotPlayer.rng.nextInt(6) == 0
            Build.Build.toFinish = []
            Build.Build.turnAdded = []
            for robot in rc.senseNearbyRobots(4):
                if robot.getTeam() == rc.getTeam() and robot.getType().isTowerType():
                    Soldier.spawn = robot.getLocation()
            Attack.Attack.target = Attack.Attack.rotational(rc, Soldier.spawn)
            a = Attack.Attack.vertical(rc, Soldier.spawn)
            b = Attack.Attack.horizontal(rc, Soldier.spawn)
            if Attack.Attack.target.distanceSquaredTo(a) < Attack.Attack.target.distanceSquaredTo(b):
                Attack.Attack.next = a
            else:
                Attack.Attack.next = b
            Attack.Attack.found = True
            # See which mode it toggles to
            if rc.getRoundNum() < max(100, rc.getMapWidth() + rc.getMapHeight()):
                # Paint towers: two builders
                # Money towers: one filler one builder
                if rc.senseRobotAtLocation(Soldier.spawn).getType() == UnitType.LEVEL_ONE_MONEY_TOWER:
                    if rc.senseRobotAtLocation(Soldier.spawn).getPaintAmount() > 200:
                        RobotPlayer.RobotPlayer.fill = True
            else:
                # 4 fillers : 1 builder
                if RobotPlayer.RobotPlayer.rng.nextInt(5) != 3:
                    RobotPlayer.RobotPlayer.fill = True
            if rc.getRoundNum() <= 2 and not Soldier.paintTowers:
                Soldier.defaultFill = True

        if Soldier.attack is not None and not Soldier.builder:
            Attack.Attack.next = Attack.Attack.target
            Attack.Attack.target = Soldier.attack
            RobotPlayer.RobotPlayer.rush = True
            Soldier.messenger = False

        if not RobotPlayer.RobotPlayer.rush:
            # See if it needs to coordinate attack
            for ruin in Soldier.ruins:
                if rc.canSenseRobotAtLocation(ruin):
                    ri = rc.senseRobotAtLocation(ruin)
                    if ri.getTeam() != rc.getTeam():
                        RobotPlayer.RobotPlayer.rush = True
                        Attack.Attack.next = Attack.Attack.target
                        Attack.Attack.target = ruin
                        # See if it needs to be a messenger instead
                        # Calculate how many turns it can live
                        power = rc.getPaint() // 10  # getPaint() >= 0: Java int division
                        power = min(power, rc.getHealth() // (ri.getType().aoeAttackStrength + ri.getType().attackStrength))  # >= 0: Java int division
                        if power < 3:
                            # meaningless attack
                            Soldier.messenger = True
                            Soldier.messageLoc = ruin
                            Soldier.priority = 7 - Soldier.scale(ruin.distanceSquaredTo(Soldier.spawn), 0,
                                    rc.getMapHeight() * rc.getMapHeight() + rc.getMapWidth() * rc.getMapWidth(),
                                    3, 7)
                            Soldier.roundNum = rc.getRoundNum()
                            Soldier.message = 0
                            break
                else:
                    RobotPlayer.RobotPlayer.build = True
            # See if it needs to coordinate a splasher attack
            # Prereq: > 40% sensed is enemy + > 4 enemies sensed
            # Only required when lowest hp soldier and senses less than 3 splashers
            # More important => overrides attack
            if len(rc.senseNearbyRobots(-1, opponent(rc.getTeam()))) > 4:
                splashers = 0
                req = True
                for splash in rc.senseNearbyRobots(-1, rc.getTeam()):
                    if splash.getType() == UnitType.SPLASHER:
                        splashers += 1
                    elif splash.getType() == UnitType.SOLDIER and splash.getLocation().isAdjacentTo(rc.getLocation()):
                        if splash.getPaintAmount() < rc.getPaint():
                            req = False
                enemy = 0
                if splashers < 3 and req:
                    for mi in rc.senseNearbyMapInfos():
                        if mi.getPaint().isEnemy():
                            enemy += 1
                    if enemy > 20:
                        Soldier.messenger = True
                        Soldier.messageLoc = rc.getLocation()
                        Soldier.priority = 7 - Soldier.scale(rc.getLocation().distanceSquaredTo(Soldier.spawn), 0,
                                rc.getMapHeight() * rc.getMapHeight() + rc.getMapWidth() * rc.getMapWidth(),
                                1, 5)
                        Soldier.roundNum = rc.getRoundNum()
                        Soldier.message = 1
        if Build.Build.toFinish:
            RobotPlayer.RobotPlayer.rush = False
            RobotPlayer.RobotPlayer.build = True
        # Check if all towers are done lol
        if rc.getNumberTowers() == 25:
            RobotPlayer.RobotPlayer.fill = True
            RobotPlayer.RobotPlayer.build = False

        RobotPlayer.RobotPlayer.retreat = not RobotPlayer.RobotPlayer.rush and rc.getPaint() < 20

        # State machine
        if Build.Build.movingTowardsToFinish or Build.Build.askForMopper:
            Build.Build.run(rc)
        elif RobotPlayer.RobotPlayer.retreat:
            #System.out.println("Retreat");
            #System.out.println(Clock.getBytecodeNum());
            Retreat.Retreat.run(rc)
            rc.setIndicatorString("Retreating")
            #System.out.println(Clock.getBytecodeNum());
        elif RobotPlayer.RobotPlayer.rush:
            #System.out.println("Rush");
            #System.out.println(Clock.getBytecodeNum());
            Attack.Attack.run(rc)
            rc.setIndicatorString("Rushing")
            #System.out.println(Clock.getBytecodeNum());
        elif (RobotPlayer.RobotPlayer.fill or Soldier.defaultFill) and not RobotPlayer.RobotPlayer.build:
            #System.out.println("Fill");
            #System.out.println(Clock.getBytecodeNum());
            Fill.Fill.run(rc)
            rc.setIndicatorString("Filling")
            #System.out.println(Clock.getBytecodeNum());
        else:
            #System.out.println("Build");
            #System.out.println(Clock.getBytecodeNum());
            Build.Build.run(rc)
            #rc.setIndicatorString("Building");

            #System.out.println(Clock.getBytecodeNum());
        Soldier.moneyLastTurn = rc.getMoney()
#        Utils.attackTowers(rc);
