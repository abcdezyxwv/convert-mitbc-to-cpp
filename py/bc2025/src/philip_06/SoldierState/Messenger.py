# Port of philip_06/SoldierState/Messenger.java. See py/CONVENTIONS.md.
# Module-form imports for bot-internal deps (cyclic import graph) - names
# resolve at call time.
from api import *
import RobotPlayer
import Soldier
from Helper import Comms
from roles import Mopper


class Messenger:
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
            Mopper.Mopper.moveTowardsMindlessly(rc, bestOpt)
            return
        Mopper.Mopper.moveTowardsMindlessly(rc, bestOpt)
        # Try to send a message
        if rc.canSendMessage(bestOpt):
            message = Comms.Comms.encode(rc, Soldier.Soldier.priority, Soldier.Soldier.messageLoc, Soldier.Soldier.roundNum, Soldier.Soldier.message)
            rc.sendMessage(bestOpt, message)
            Soldier.Soldier.messenger = False
            Soldier.Soldier.messageLoc = None
            Soldier.Soldier.priority = 0
            Soldier.Soldier.roundNum = 0
            Soldier.Soldier.message = 0
