# Port of philip_06/SoldierState/Retreat.java. See py/CONVENTIONS.md.
# Module-form imports for bot-internal deps (cyclic import graph) - names
# resolve at call time.
from api import *
import RobotPlayer
import Soldier
from roles import Mopper


class Retreat:
    @staticmethod
    def run(rc):
        bestOpt = None
        for curr in Soldier.Soldier.paintTowers:
            if rc.canSenseLocation(curr) and rc.senseRobotAtLocation(curr) is None:
                Soldier.Soldier.paintTowers.discard(curr)
                break
        for curr in Soldier.Soldier.paintTowers:
            if bestOpt is None or (rc.getLocation().distanceSquaredTo(curr) < rc.getLocation().distanceSquaredTo(bestOpt) and (not rc.canSenseLocation(bestOpt) or rc.senseRobotAtLocation(bestOpt) is not None)):
                bestOpt = curr
        if bestOpt is None:
            bestOpt = MapLocation(RobotPlayer.RobotPlayer.rng.nextInt(rc.getMapWidth()), RobotPlayer.RobotPlayer.rng.nextInt(rc.getMapHeight()))
            Mopper.Mopper.moveTowardsMindfully(rc, bestOpt)
            return
        transfer = 100 - rc.getPaint()
        if rc.canSenseLocation(bestOpt) and rc.senseRobotAtLocation(bestOpt) is not None:
            transfer = min(transfer, rc.senseRobotAtLocation(bestOpt).getPaintAmount())
            rc.setIndicatorString(str(transfer))
            if rc.canTransferPaint(bestOpt, -transfer):
                rc.transferPaint(bestOpt, -transfer)
        Mopper.Mopper.moveTowardsMindfully(rc, bestOpt)
