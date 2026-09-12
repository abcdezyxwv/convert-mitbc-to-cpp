# Port of bestsofar/Baby.java. See py/CONVENTIONS.md.
from api import *

from Utils import Attack
from Utils.CatsAreWalls import CatsAreWalls
from Utils.Comms import Comms
from Utils.FastSet import FastSet
from Utils.Globals import Globals
from Utils.Movement import Movement
from Utils.Symmetry import Symmetry
from Utils.Vision import Vision

# Java: import bestsofar.Roles.*; -- bound as modules, not `from Roles.X import
# X`, because Rush/Multiking (via Baby) form an import cycle with this file;
# module binding defers the class lookup to call time. Use as Miner.Miner etc.
from Roles import Hunter, Miner, Multiking, Rush


class Baby(Globals):

    spawn = None

    isNewKing = False
    explorer = False

    roundsBeingHeld = 0

    @staticmethod
    def evadeCats():
        # evade cats
        fst = FastSet()
        for cat in Globals.catRobots:
            fakeID = MapLocation(cat.getID() % 64, (cat.getID() % 4096) >> 6)
            if not fst.contains(fakeID):
                fst.add(fakeID)
                CatsAreWalls.pretend(cat.location, cat.direction)
        for cat in Globals.catsLastTurn:
            fakeID = MapLocation(cat.getID() % 64, (cat.getID() % 4096) >> 6)
            if not fst.contains(fakeID):
                fst.add(fakeID)
                CatsAreWalls.pretend(cat.location, cat.direction)
                CatsAreWalls.pretend(cat.location.add(cat.direction), cat.direction)

    @staticmethod
    def unevadeCats():
        # unevade cats
        fst = FastSet()
        for cat in Globals.catRobots:
            fakeID = MapLocation(cat.getID() % 64, (cat.getID() % 4096) >> 6)
            if not fst.contains(fakeID):
                fst.add(fakeID)
                CatsAreWalls.unpretend(cat.location, cat.direction)
        for cat in Globals.catsLastTurn:
            fakeID = MapLocation(cat.getID() % 64, (cat.getID() % 4096) >> 6)
            if not fst.contains(fakeID):
                fst.add(fakeID)
                CatsAreWalls.unpretend(cat.location, cat.direction)
                CatsAreWalls.unpretend(cat.location.add(cat.direction), cat.direction)

    @staticmethod
    def burnCooldown():
        rc = Globals.rc
        if Globals.closestEnemy is None or rc.getLocation().distanceSquaredTo(Globals.closestEnemy.location) > 8:
            if rc.getRawCheese() < Globals.maxCheese:
                for i in range(9):
                    if rc.canPickUpCheese(rc.getLocation().add(Direction.DIRECTION_ORDER[i])):
                        Globals.pickUpCheese(rc.getLocation().add(Direction.DIRECTION_ORDER[i]))
                        break

        if len(Globals.enemyRobots) == 0 and Globals.closestEnemy is None:
            for direction in Direction.DIRECTION_ORDER:
                if rc.canAttack(rc.getLocation().add(direction)):
                    rc.attack(rc.getLocation().add(direction))
                    break

        transferLoc = Globals.closestKing.add(Globals.closestKing.directionTo(rc.getLocation()))
        if rc.canTransferCheese(transferLoc, rc.getRawCheese()):
            rc.transferCheese(transferLoc, rc.getRawCheese())

    @staticmethod
    def run():
        rc = Globals.rc
        # newborn
        if Baby.spawn is None:
            Baby.spawn = rc.getLocation()

            Baby.explorer = True

        # disintegration to disarm opponent
        if rc.isBeingCarried():
            Baby.roundsBeingHeld += 1
            if Baby.roundsBeingHeld >= 2 and Globals.squeaksReadLastRound >= 2 and rc.getHealth() < 50:
                rc.disintegrate()
        else:
            Baby.roundsBeingHeld = 0

        # check for emergency mode
        if rc.readSharedArray(60) > 0 and rc.canBecomeRatKing():
            rc.becomeRatKing()
            return

        if not rc.isBeingThrown() and not rc.isBeingCarried():
            # return to king unless can SEE enemies
            if Miner.Miner.returningToKing and len(Globals.enemyRobots) == 0:
                Miner.Miner.run()
                Baby.burnCooldown()
                return
            # attack micro
            didAttack = Attack.Attack.attack()

            if not didAttack:
                Baby.evadeCats()

                if Baby.isNewKing:
                    Multiking.Multiking.run()
                else:
                    if len(Globals.enemyRobots) == 0 and Globals.closestEnemy is None:
                        Hunter.Hunter.run()

                    # miner
                    if Miner.Miner.shouldBeMiner() and len(Globals.enemyRobots) == 0:
                        rc.setIndicatorDot(MapLocation(0, 0), 255, 255, 0)
                        Miner.Miner.run()
                        if Miner.Miner.returningToKing:
                            Globals.hasSqueaked = True
                        Vision.turnJustBecause()
                    # explorer
                    elif Baby.explorer:
                        rc.setIndicatorDot(MapLocation(0, 0), 0, 255, 0)
                        Movement.explore()
                        Vision.turnJustBecause()
                    else:
                        Rush.Rush.run(Baby.spawn)
                        Vision.turnJustBecause()
                Baby.unevadeCats()
            Baby.burnCooldown()

        # Inform nearby allies of enemy information
        Comms.squeakEnemies()

        # symmetry stuff
        Symmetry.updateSymmetryFromGlobal()
        Symmetry.updateNearbySymmetry()
        Symmetry.hearNearbySymmetrySqueaks()
        Symmetry.commSymmetryToNearby()
