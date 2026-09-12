# Port of philip_06/roles/Splasher.java. See py/CONVENTIONS.md.
import math

from api import *
import RobotPlayer
from roles import Mopper
from utils import Utils
from Helper import Comms

# Java: import static philip_06.Helper.Comms.getMsg
getMsg = Comms.Comms.getMsg
# Java: import static philip_06.Helper.Comms.sendMsg
sendMsg = Comms.Comms.sendMsg


class Splasher:
    rng = None
    type = False
    destination = None
    opponentPaintSquares = 0
    paintTowers = set()
    turnsSinceLastAttack = -100

    @staticmethod
    def retreat(rc):
        bestOpt = None
        for curr in Splasher.paintTowers:
            if bestOpt is None or (rc.getLocation().distanceSquaredTo(curr) < rc.getLocation().distanceSquaredTo(bestOpt) and (not rc.canSenseLocation(bestOpt) or rc.senseRobotAtLocation(bestOpt) is not None)):
                bestOpt = curr
        if bestOpt is None:
            bestOpt = Splasher.getNextCorner(rc)
            Mopper.Mopper.moveTowardsMindfully(rc, bestOpt)
            return
        transfer = rc.getType().paintCapacity - rc.getPaint()
        if rc.canSenseLocation(bestOpt) and rc.senseRobotAtLocation(bestOpt) is not None:
            transfer = min(transfer, rc.senseRobotAtLocation(bestOpt).getPaintAmount())
            rc.setIndicatorString(str(transfer))
            if rc.canTransferPaint(bestOpt, -transfer): rc.transferPaint(bestOpt, -transfer)
        Mopper.Mopper.moveTowardsMindfully(rc, bestOpt)

    targetRuinsOnly = False

    @staticmethod
    def bestRuinAttack(rc):
        closestRuin = Utils.Utils.closestRuin(rc)  # Java: assigned but unused in this method
        forced = False
        best = -1000
        target = None
        nearby = rc.senseNearbyMapInfos(4)
        xavg = 0
        yavg = 0

        for loc in rc.senseNearbyMapInfos(-1):
            if loc.getPaint().isEnemy():
                Splasher.opponentPaintSquares += 1
                xavg += loc.getMapLocation().x
                yavg += loc.getMapLocation().y
        if Splasher.opponentPaintSquares != 0:
            # Java Math.round(float) == floor(x + 0.5f)
            xavg = int(math.floor(xavg / Splasher.opponentPaintSquares + 0.5))
            yavg = int(math.floor(yavg / Splasher.opponentPaintSquares + 0.5))
            forced = rc.getLocation().isWithinDistanceSquared(MapLocation(xavg, yavg), 1)
        #
        # int[] temp = new int[nearby.length];
        # for(int i = 0; i<temp.length; i++){
        #     temp[i] = i;
        # }
        # Utils.shuffleArray(temp);
        #
        for loc in nearby:
            damage = 0
            prim = False
            sec = False
            for hit in rc.senseNearbyMapInfos(loc.getMapLocation(), 4):
                # 1 for paint, 3 for enemy
                if hit.isWall(): continue
                if hit.getPaint().isAlly():
                    damage -= 2
                    if hit.getPaint() == PaintType.ALLY_PRIMARY:
                        prim = True
                        if sec:
                            break
                    if hit.getPaint() == PaintType.ALLY_SECONDARY:
                        sec = True
                        if prim:
                            break
                elif hit.hasRuin() and (rc.senseRobotAtLocation(hit.getMapLocation()) is None or rc.senseRobotAtLocation(hit.getMapLocation()).getTeam() != rc.getTeam()):
                    damage += 10000
                else:
                    damage += 1

            if damage >= best:
                best = damage
                target = loc.getMapLocation()
                if sec:
                    Splasher.type = True
                if prim:
                    Splasher.type = False
        if Splasher.opponentPaintSquares == 0:
            Splasher.turnsSinceLastAttack = 0
        if best > 10000 or forced:
            if rc.canAttack(target):
                Splasher.turnsSinceLastAttack = 0
                rc.attack(target, Splasher.type)
                Mopper.Mopper.explore(rc)
            else:
                Splasher.turnsSinceLastAttack += 1
                Mopper.Mopper.explore(rc)
        elif Splasher.opponentPaintSquares != 0:
            Splasher.turnsSinceLastAttack += 1
            Mopper.Mopper.explore(rc)
        else:
            Splasher.turnsSinceLastAttack += 1
            Mopper.Mopper.explore(rc)

    @staticmethod
    def bestAttack(rc):
        closestRuin = Utils.Utils.closestRuin(rc)
        forced = False
        best = -1000
        target = None
        nearby = rc.senseNearbyMapInfos(4)
        xavg = 0
        yavg = 0

        for loc in rc.senseNearbyMapInfos(-1):
            if loc.isResourcePatternCenter() and loc.getPaint().isEnemy():
                Splasher.opponentPaintSquares += 10
                xavg += 10 * loc.getMapLocation().x
                yavg += 10 * loc.getMapLocation().y
            elif loc.getPaint().isEnemy():
                Splasher.opponentPaintSquares += 1
                xavg += loc.getMapLocation().x
                yavg += loc.getMapLocation().y
        if Splasher.opponentPaintSquares != 0:
            # Java Math.round(float) == floor(x + 0.5f)
            xavg = int(math.floor(xavg / Splasher.opponentPaintSquares + 0.5))
            yavg = int(math.floor(yavg / Splasher.opponentPaintSquares + 0.5))
            forced = rc.getLocation().isWithinDistanceSquared(MapLocation(xavg, yavg), 1)
        #
        # int[] temp = new int[nearby.length];
        # for(int i = 0; i<temp.length; i++){
        #     temp[i] = i;
        # }
        # Utils.shuffleArray(temp);
        #
        for loc in nearby:
            damage = 0
            prim = False
            sec = False
            for hit in rc.senseNearbyMapInfos(loc.getMapLocation(), 4):
                # 1 for paint, 3 for enemy
                if hit.isWall() or hit.hasRuin(): continue
                if hit.getPaint().isAlly():
                    damage -= 1
                    if hit.getPaint() == PaintType.ALLY_PRIMARY:
                        prim = True
                        if sec:
                            break
                    if hit.getPaint() == PaintType.ALLY_SECONDARY:
                        sec = True
                        if prim:
                            break
                elif hit.getPaint() == PaintType.EMPTY:
                    damage += 1
                elif hit.getMapLocation().distanceSquaredTo(loc.getMapLocation()) <= 2:
                    if hit.isResourcePatternCenter() and hit.getPaint().isEnemy():
                        damage += 30
                    elif closestRuin is not None and closestRuin.isWithinDistanceSquared(hit.getMapLocation(), 8):
                        damage += 5
                    else:
                        damage += 3
            if damage >= best:
                best = damage
                target = loc.getMapLocation()
                if sec:
                    Splasher.type = True
                if prim:
                    Splasher.type = False
        if Splasher.opponentPaintSquares == 0:
            Splasher.turnsSinceLastAttack = 0
        if best > 11 or forced:
            if rc.canAttack(target):
                Splasher.turnsSinceLastAttack = 0
                rc.attack(target, Splasher.type)
                if Splasher.opponentPaintSquares != 0 and rc.canMove(rc.getLocation().directionTo(MapLocation(xavg, yavg)).opposite()):
                    rc.move(rc.getLocation().directionTo(MapLocation(xavg, yavg)).opposite())
            else:
                Splasher.turnsSinceLastAttack += 1
                #Mopper.explore(rc);
        elif Splasher.opponentPaintSquares != 0:
            Splasher.turnsSinceLastAttack += 1
            Mopper.Mopper.moveTowardsMindfully(rc, MapLocation(xavg, yavg))
        else:
            Splasher.turnsSinceLastAttack += 1
            #Mopper.explore(rc);

    @staticmethod
    def shouldMove(rc, dir):
        if not rc.canMove(dir): return None
        nearby = rc.senseNearbyRuins(16)
        for loc in nearby:
            if not rc.canSenseRobotAtLocation(loc): continue
            tower = rc.senseRobotAtLocation(loc)
            if tower.getTeam() == rc.getTeam(): continue
            dir = rc.getLocation().directionTo(loc).opposite()
        if rc.canSenseLocation(rc.getLocation().add(dir)) and not rc.senseMapInfo(rc.getLocation().add(dir)).getPaint().isEnemy():
            return dir
        dir = dir.rotateRight()
        if rc.canSenseLocation(rc.getLocation().add(dir)) and not rc.senseMapInfo(rc.getLocation().add(dir)).getPaint().isEnemy():
            return dir
        dir = dir.rotateLeft()
        dir = dir.rotateLeft()
        if rc.canSenseLocation(rc.getLocation().add(dir)) and not rc.senseMapInfo(rc.getLocation().add(dir)).getPaint().isEnemy():
            return dir
        return None

    oppSpawn = None

    @staticmethod
    def getNextCorner(rc):
        if Splasher.rng is None: Splasher.rng = RobotPlayer.RobotPlayer.rng
        x = Splasher.rng.nextInt(3) * (rc.getMapWidth() // 2)
        y = Splasher.rng.nextInt(3) * (rc.getMapHeight() // 2)
        x = max(0, min(rc.getMapWidth() - 1, x + Splasher.rng.nextInt() % 3))
        y = max(0, min(rc.getMapHeight() - 1, y + Splasher.rng.nextInt() % 3))
        return MapLocation(x, y)

    @staticmethod
    def run(rc):
        if rc.getRoundNum() < 4 or rc.getID() % 20 == 0:
            Splasher.targetRuinsOnly = True
        if Splasher.targetRuinsOnly:
            Splasher.bestRuinAttack(rc)
            return
        if Splasher.rng is None: Splasher.rng = RobotPlayer.RobotPlayer.rng
        for loc in rc.senseNearbyRuins(-1):
            tower = rc.senseRobotAtLocation(loc)
            if tower is None or tower.getTeam() == opponent(rc.getTeam()):
                if tower is not None:
                    RobotPlayer.RobotPlayer.lastEnemyTower = tower.getLocation()
                Splasher.paintTowers.discard(loc)
                continue
            if tower.getPaintAmount() >= 150 or tower.getType().paintPerTurn > 0:
                Splasher.paintTowers.add(loc)
            else:
                Splasher.paintTowers.discard(loc)

        sendMsg(rc)
        getMsg(rc)
        if rc.getPaint() < 10:
            for robot in rc.senseNearbyRobots(2):
                if robot.getTeam() == rc.getTeam() and robot.getType().isRobotType() and robot.getType() != UnitType.MOPPER and robot.getPaintAmount() > 50:
                    print("goodbye")
                    rc.disintegrate()
        if rc.getPaint() < 50:
            Splasher.retreat(rc)
            rc.setIndicatorString("retreat")
            return
        Splasher.opponentPaintSquares = 0
        #if (oppSpawn == null) destination = oppSpawn = new MapLocation(rc.getMapWidth()-rc.getLocation().x,rc.getMapHeight()-rc.getLocation().y);
        #
        # int pri = -1;
        # for (Message mess : rc.readMessages(-1)) {
        #     int[] action = Comms.decode(mess.getBytes());
        #
        #     // Only care about recent messages
        #     if (rc.getRoundNum() - action[4] > 50) continue;
        #
        #     // action[5] = 0 => attack location
        #     if (action[5] == 0) {
        #         if (action[1] > pri) {
        #             pri = action[1];
        #             destination = new MapLocation(action[2], action[3]);
        #         }
        #     }
        # }

        if Splasher.destination is None or rc.getLocation().distanceSquaredTo(Splasher.destination) < 9 or rc.getRoundNum() % 69 == 0:
            Splasher.destination = Splasher.getNextCorner(rc)
        Splasher.bestAttack(rc)
        if Splasher.opponentPaintSquares == 0:
            Mopper.Mopper.moveTowardsMindfully(rc, Splasher.destination)
        if rc.isMovementReady():
            best = None
            for loc in rc.senseNearbyMapInfos(-1):
                if loc.getPaint().isAlly() and (best is None or rc.getLocation().distanceSquaredTo(loc.getMapLocation()) < rc.getLocation().distanceSquaredTo(best)):
                    best = loc.getMapLocation()
            if best is not None:
                Mopper.Mopper.moveTowardsMindfully(rc, best)
