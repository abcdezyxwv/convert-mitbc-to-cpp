# Port of philip_06/roles/Tower.java. See py/CONVENTIONS.md.
from collections import deque

from api import *
import RobotPlayer
from utils import Actions
from Helper import Comms


class Tower:

    # list of spawn rates
    class SpawnRateChange:
        def __init__(self, sol, spl, mop):
            self.soldierPrty = sol
            self.splasherPrty = spl
            self.mopperPrty = mop

    # Java: Queue<Map.Entry<UnitType, MapLocation>> -> deque of (key, value) tuples
    toSpawn = deque()
    target = None
    targetRound = 0

    @staticmethod
    def run(rc):
        hasMopper = False
        hasSplasher = False
        noEnemyPaint = 0
        for bot in rc.senseNearbyRobots(-1, rc.getTeam()):
            if bot.getType() == UnitType.MOPPER:
                hasMopper = True
            if bot.getType() == UnitType.SPLASHER:
                hasSplasher = True
        for loc in rc.senseNearbyMapInfos(-1):
            if loc.getPaint().isEnemy():
                noEnemyPaint += 1
        if not hasMopper and not hasSplasher and noEnemyPaint > 0:
            Actions.Actions.spawn(rc, UnitType.MOPPER, MapLocation(61, 61))
        # add new spawn stuff
        if RobotPlayer.RobotPlayer.aliveTurns == 1 and rc.getRoundNum() < 50:
#           if(rc.getMapHeight()*rc.getMapWidth()<=1500 && rc.getType()==UnitType.LEVEL_TWO_MONEY_TOWER)
  #             toSpawn.add(Map.entry(UnitType.SPLASHER, new MapLocation(61, 61)));
   #       else
            Tower.toSpawn.append((UnitType.SOLDIER, MapLocation(61, 61)))  # Java: Map.entry
            Tower.toSpawn.append((UnitType.SOLDIER, MapLocation(61, 61)))
        if rc.getRoundNum() - Tower.targetRound > 100:
            Tower.target = None
        Comms.Comms.getMsg(rc)
        Comms.Comms.sendMsg(rc)
        if Tower.target is not None: rc.setIndicatorLine(rc.getLocation(), Tower.target, 0, 0, 0)

        if Tower.target is not None:
            for loc in rc.senseNearbyRobots(-1, rc.getTeam()):
                if rc.canSendMessage(loc.location):
                    rc.sendMessage(loc.location, Comms.Comms.encodeLocation(Tower.target))
        # get spawn rates of current round
        if rc.getRoundNum() < 30:
            s = Tower.SpawnRateChange(1, 0, 0)
        elif rc.getRoundNum() < 60:
            s = Tower.SpawnRateChange(1, 0, 1)
        elif rc.getRoundNum() < (rc.getMapWidth() + rc.getMapWidth()):
            s = Tower.SpawnRateChange(3, 0, 2)
        elif rc.getRoundNum() < 3 * (rc.getMapWidth() + rc.getMapWidth()):
            s = Tower.SpawnRateChange(3, 0, 1)
        else:
            s = Tower.SpawnRateChange(2, 3, 2)
        rc.setIndicatorString("Spawning with priorities: " + str(s.soldierPrty) + ", " + str(s.splasherPrty) + ", " + str(s.mopperPrty))
        if rc.getMoney() > 1100 and rc.getPaint() > 300 and not Tower.toSpawn:  # extra spawn
            r = RobotPlayer.RobotPlayer.rng.nextInt(s.soldierPrty + s.splasherPrty + s.mopperPrty)
            if r < s.soldierPrty: Tower.toSpawn.append((UnitType.SOLDIER, MapLocation(61, 61)))
            elif r < s.splasherPrty + s.soldierPrty: Tower.toSpawn.append((UnitType.SPLASHER, MapLocation(61, 61)))
            else: Tower.toSpawn.append((UnitType.MOPPER, MapLocation(61, 61)))
        # spawn stuff
        while Tower.toSpawn and Actions.Actions.spawn(rc, Tower.toSpawn[0][0], Tower.toSpawn[0][1]):
            Tower.toSpawn.popleft()
        # upgrade self
        if ((rc.getType() == UnitType.LEVEL_ONE_PAINT_TOWER) or (rc.getMoney() > 6000 and rc.getType() == UnitType.LEVEL_TWO_PAINT_TOWER)) and rc.canUpgradeTower(rc.getLocation()) and (rc.getMoney() > 4000 or len(rc.senseNearbyRobots(-1, rc.getTeam())) >= 4):
            rc.upgradeTower(rc.getLocation())
        if len(rc.senseNearbyRobots(-1, opponent(rc.getTeam()))) > 3:
            if rc.getType().getBaseType() == UnitType.LEVEL_ONE_DEFENSE_TOWER and rc.canUpgradeTower(rc.getLocation()) and rc.getMoney() > 2000:
                rc.upgradeTower(rc.getLocation())
        if rc.getMoney() > 6000 and rc.canUpgradeTower(rc.getLocation()):
            rc.upgradeTower(rc.getLocation())
        # Attack enemies
        damage = 0  # Java: accumulated but unused
        snipe = 0
        todo = None
        locs = rc.senseNearbyRobots(9)
        for loc in locs:
            if loc.getTeam() != rc.getTeam() and rc.canAttack(loc.getLocation()):
                # Single shot
                damage += min(loc.getHealth(), rc.getType().aoeAttackStrength)
                if min(loc.getHealth(), rc.getType().attackStrength) > snipe:
                    snipe = min(loc.getHealth(), rc.getType().attackStrength)
                    todo = loc.getLocation()
        if todo is not None and rc.canAttack(todo): rc.attack(todo)
        if rc.canAttack(None): rc.attack(None)  # Java: canAttack(null) / attack(null)
