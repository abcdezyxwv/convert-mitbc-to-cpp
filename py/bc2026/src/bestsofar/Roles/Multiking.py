# Port of bestsofar/Roles/Multiking.java. See py/CONVENTIONS.md.
from api import *

# Java: import bestsofar.Baby / bestsofar.King -- bound as modules (accessed as
# Baby.Baby / King.King) because Baby imports this file back; module binding
# defers the class lookup to call time and avoids the circular-import failure.
import Baby
import King
from Utils.BugNavigator import BugNavigator
from Utils.Comms import Comms
from Utils.Globals import Globals
from Utils.Navigator import Navigator
from Utils.Vision import Vision


class Multiking(Globals):
    newKingPos = None
    roundsCircled = 0

    @staticmethod
    def isMultiking():
        Multiking.newKingPos = Comms.needNewKing()
        return Comms.getNumberBots() <= Globals.botsForNewKing and Multiking.newKingPos is not None

    targetPos = None

    @staticmethod
    def moveTo():
        rc = Globals.rc
        if rc.getLocation() == Multiking.newKingPos:
            return
        if rc.getLocation().distanceSquaredTo(Multiking.newKingPos) <= 2:
            dir = rc.getLocation().directionTo(Multiking.newKingPos)
            if rc.canMove(dir):
                Vision.turn(dir)
                rc.move(dir)
            return
        if Multiking.targetPos is not None and rc.canSenseRobotAtLocation(Multiking.targetPos):
            Multiking.targetPos = None
        if Multiking.targetPos is None and rc.getLocation().distanceSquaredTo(Multiking.newKingPos) <= 8:
            Vision.turn(rc.getLocation().directionTo(Multiking.newKingPos))
            pos = Multiking.newKingPos
            if not rc.canSenseRobotAtLocation(pos):
                Multiking.targetPos = pos
                BugNavigator.moveTo(Multiking.targetPos, True)
                return
            pos = Multiking.newKingPos.add(Multiking.newKingPos.directionTo(rc.getLocation()))
            if not rc.canSenseRobotAtLocation(pos):
                Multiking.targetPos = pos
                BugNavigator.moveTo(Multiking.targetPos, True)
                return
            pos = Multiking.newKingPos.add(Multiking.newKingPos.directionTo(rc.getLocation()).rotateLeft())
            if not rc.canSenseRobotAtLocation(pos):
                Multiking.targetPos = pos
                BugNavigator.moveTo(Multiking.targetPos, True)
                return
            pos = Multiking.newKingPos.add(Multiking.newKingPos.directionTo(rc.getLocation()).rotateRight())
            if not rc.canSenseRobotAtLocation(pos):
                Multiking.targetPos = pos
                BugNavigator.moveTo(Multiking.targetPos, True)
                return
            pos = Multiking.newKingPos.add(Multiking.newKingPos.directionTo(rc.getLocation()).rotateLeft().rotateLeft())
            if not rc.canSenseRobotAtLocation(pos):
                Multiking.targetPos = pos
                BugNavigator.moveTo(Multiking.targetPos, True)
                return
            pos = Multiking.newKingPos.add(Multiking.newKingPos.directionTo(rc.getLocation()).rotateRight().rotateRight())
            if not rc.canSenseRobotAtLocation(pos):
                Multiking.targetPos = pos
                BugNavigator.moveTo(Multiking.targetPos, True)
                return
            pos = Multiking.newKingPos.add(Multiking.newKingPos.directionTo(rc.getLocation()).opposite().rotateRight())
            if not rc.canSenseRobotAtLocation(pos):
                Multiking.targetPos = pos
                BugNavigator.moveTo(Multiking.targetPos, True)
                return
            pos = Multiking.newKingPos.add(Multiking.newKingPos.directionTo(rc.getLocation()).opposite().rotateLeft())
            if not rc.canSenseRobotAtLocation(pos):
                Multiking.targetPos = pos
                BugNavigator.moveTo(Multiking.targetPos, True)
                return
            pos = Multiking.newKingPos.add(Multiking.newKingPos.directionTo(rc.getLocation()).opposite())
            if not rc.canSenseRobotAtLocation(pos):
                Multiking.targetPos = pos
                BugNavigator.moveTo(Multiking.targetPos, True)
                return
            return
        if Multiking.targetPos is None:
            Navigator.moveTo(Multiking.newKingPos, True)
            return
        BugNavigator.moveTo(Multiking.targetPos, True)


    @staticmethod
    def run():
        rc = Globals.rc
        for ml in Globals.kingPos:
            if ml is None:
                break
            if ml.distanceSquaredTo(Multiking.newKingPos) <= Globals.closeToKing:
                Baby.Baby.isNewKing = False
                return
        rc.setIndicatorString(str(Multiking.newKingPos))
        Multiking.moveTo()
        if rc.getLocation().distanceSquaredTo(Multiking.newKingPos) <= 8:
            Multiking.roundsCircled += 1
            Comms.squeakForSacrifices(Multiking.newKingPos)
        if rc.getLocation().distanceSquaredTo(Multiking.newKingPos) <= 8 and rc.canBecomeRatKing():
            rc.becomeRatKing()
            King.King.run()
            return
        if Multiking.roundsCircled >= Globals.giveUpNewKing:
            Baby.Baby.isNewKing = False
