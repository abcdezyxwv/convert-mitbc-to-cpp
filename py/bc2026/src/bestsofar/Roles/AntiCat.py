# Port of bestsofar/Roles/AntiCat.java. See py/CONVENTIONS.md.
from api import *

from Utils import Attack
from Utils.Globals import Globals
from Utils.Movement import Movement
from Utils.Navigator import Navigator
from Utils.Vision import Vision


class AntiCat(Globals):
    lastTime = -1
    inARow = 0

    @staticmethod
    def suicide():
        Attack.Attack.attackCat()

    @staticmethod
    def run(catLoc):
        rc = Globals.rc
        if AntiCat.lastTime == rc.getRoundNum() - 1:
            AntiCat.inARow += 1
        else:
            AntiCat.inARow = 1
        kingLoc = Globals.kingPos[0]
        if rc.getLocation().distanceSquaredTo(kingLoc) < 8:
            dir1 = kingLoc.directionTo(catLoc)
            dir2 = kingLoc.add(dir1).directionTo(catLoc)
            attempt = kingLoc.add(dir1).add(dir2)
            attempt = attempt.add(attempt.directionTo(catLoc))
            if rc.canTurn():
                Vision.turn(rc.getLocation().directionTo(catLoc))
            if Vision.isDirt(attempt):
                dir2 = dir2.rotateLeft()
                attempt = kingLoc.add(dir1).add(dir2)
                if Vision.isDirt(attempt):
                    dir2 = dir2.rotateRight().rotateRight()
                    attempt = kingLoc.add(dir1).add(dir2)
            # Java: `getLocation() == attempt` is reference equality on two
            # fresh MapLocations (always false); `is` preserves that.
            if rc.getLocation() is attempt:
                Movement.circle(kingLoc)
            elif not rc.getLocation().isWithinDistanceSquared(attempt, 2):
                Navigator.moveTo(attempt, False)
            if rc.canPlaceDirt(attempt):
                rc.placeDirt(attempt)
                Vision.placeDirt(attempt)
            return True
        if AntiCat.inARow > 10:
            AntiCat.suicide()
            return True
        return False
