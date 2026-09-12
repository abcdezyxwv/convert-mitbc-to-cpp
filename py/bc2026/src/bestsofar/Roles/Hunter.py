# Port of bestsofar/Roles/Hunter.java. See py/CONVENTIONS.md.
from api import *

from Utils.Globals import Globals


class Hunter(Globals):
    # Cat attacking micro
    cat = None
    catDir = Direction.CENTER
    unknownRounds = 0

    @staticmethod
    def run():
        rc = Globals.rc
        if not rc.isCooperation():
            if Globals.catLoc is not None:
                target = rc.getLocation().add(rc.getLocation().directionTo(Globals.catLoc))
                if rc.canAttack(target):
                    rc.attack(target)
            return



        if rc.readSharedArray(62) == 0:
            return
        # Maintain cat position
        Hunter.unknownRounds += 1
        if Globals.catLoc is not None:
            print("Target seen")
            Hunter.cat = Globals.catLoc
            Hunter.catDir = rc.senseRobotAtLocation(Hunter.cat).getDirection()
            Hunter.unknownRounds = 0

        # Get the latest information if possible
#        MapLocation possible = Comms.getPreyLoc();
#        if (unknownRounds > 0 && possible.x > -1 && rc.getLocation().distanceSquaredTo(possible) < 20) {
#            cat = possible;
#            if (unknownRounds > 2) catDir = Direction.CENTER;
#            unknownRounds = 2;
#        }
        if Hunter.cat is None or Hunter.unknownRounds > 3 or (rc.getRawCheese() == 0 and rc.getGlobalCheese() < Globals.safeCheeseReserve):
            return
        # Try place cat trap
        m1 = MapLocation(Hunter.cat.x, Hunter.cat.y)
        m2 = MapLocation(Hunter.cat.x + 1, Hunter.cat.y)
        m3 = MapLocation(Hunter.cat.x, Hunter.cat.y + 1)
        m4 = MapLocation(Hunter.cat.x + 1, Hunter.cat.y + 1)
        if rc.canPlaceCatTrap(m1):
            rc.placeCatTrap(m1)
        if rc.canPlaceCatTrap(m2):
            rc.placeCatTrap(m2)
        if rc.canPlaceCatTrap(m3):
            rc.placeCatTrap(m3)
        if rc.canPlaceCatTrap(m4):
            rc.placeCatTrap(m4)
