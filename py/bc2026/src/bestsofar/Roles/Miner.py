# Port of bestsofar/Roles/Miner.java. See py/CONVENTIONS.md.
from api import *

# Java: Multiking is in the same package (bestsofar.Roles), so the Java file
# needs no import; bound as a module here (not `from Roles.Multiking import
# Multiking`) because Multiking imports Baby which imports this file - module
# binding defers the class lookup and avoids the circular-import failure.
from Roles import Multiking
from Utils import Attack
from Utils.Comms import Comms
from Utils.FastSet import FastSet
from Utils.Globals import Globals
from Utils.Navigator import Navigator
from Utils.Vision import Vision


class Miner(Globals):

    mineDirections = [
        Direction.CENTER,
        Direction.NORTH,
        Direction.NORTHEAST,
        Direction.EAST,
        Direction.SOUTHEAST,
        Direction.SOUTH,
        Direction.SOUTHWEST,
        Direction.WEST,
        Direction.NORTHWEST
    ]

    mineBlacklist = FastSet()

    mine = None
    cheese = None
    returningToKing = False
    newKing = None

    @staticmethod
    def needNewKing():
        hasMine = None
        totalCheese = 0
        cheeseSquares = 0
        for mi in Globals.surroundings:
            if mi.hasCheeseMine():
                hasMine = mi.getMapLocation()
            totalCheese += mi.getCheeseAmount()
            cheeseSquares += 1 if mi.getCheeseAmount() > 0 else 0
        if totalCheese >= Globals.newKingCheeseThreshold and cheeseSquares >= Globals.newKingSquaresThreshold:
            return hasMine
        return None

    @staticmethod
    def amOccupyingMine(loc):
        return Globals.rc.getLocation().isAdjacentTo(loc)

    @staticmethod
    def mineIsOccupied(loc):
        rc = Globals.rc
        for dir in Miner.mineDirections:
            # tile in the 3x3 around the cheese mine

            # if its your current location, then you own the mine :)
            if loc.add(dir) == rc.getLocation():
                return False

            if not rc.canSenseRobotAtLocation(loc.add(dir)):
                continue
            return True
        return False

    # returns true if a vacant cheese mine is found
    @staticmethod
    def findMine():
        for info in Globals.surroundings:
            if info.hasCheeseMine():
                loc = info.getMapLocation()
                if Miner.mineIsOccupied(loc):
                    continue

                Miner.mine = loc
                return True
        return False

    # finds a cheese to go and pickup
    @staticmethod
    def findCheese():
        for info in Globals.surroundings:
            if info.getCheeseAmount() > 0:
                Miner.cheese = info.getMapLocation()
                return True
        return False

    @staticmethod
    def checkMineVacancy():
        rc = Globals.rc
        if Miner.mineIsOccupied(Miner.mine):
            # return to king if i have a respectable amount of cheese
            if rc.getRawCheese() >= Globals.minerSecondaryReturnThreshold or rc.getRawCheese() >= rc.getGlobalCheese():
                Miner.returningToKing = True
                Miner.returnToKing(False)
            # otherwise ditch mine and become soldier
            else:
                Miner.mine = None
                Miner.cheese = None
                Miner.returningToKing = False
            return False
        return True

    @staticmethod
    def returnToKing(urgent):
        rc = Globals.rc
        if rc.getRawCheese() == 0 and (rc.readSharedArray(60) == 0 or Comms.getNumKings() > 1):
            Miner.returningToKing = False
            return
        rc.setIndicatorString("miner: returning to king")
        dir = rc.getLocation().directionTo(Globals.closestKing)
        location = Globals.closestKing.add(Globals.closestKing.directionTo(rc.getLocation()))
        if rc.canTransferCheese(location, rc.getRawCheese()):
            rc.transferCheese(location, rc.getRawCheese())
            if Miner.newKing is not None:
                Comms.squeakNewKing(Miner.newKing)
                Miner.newKing = None
            if rc.canTurn():
                Vision.turn(dir.opposite())
            return

        if rc.getLocation().distanceSquaredTo(location) <= 25:

            if rc.canTurn():
                Vision.turn(dir)
            if rc.canTransferCheese(location, rc.getRawCheese()):
                rc.transferCheese(location, rc.getRawCheese())
                if Miner.newKing is not None:
                    Comms.squeakNewKing(Miner.newKing)
                    Miner.newKing = None
                return

        else:

            if not urgent and rc.getRawCheese() < 80:
                for mi in Globals.surroundings:
                    if mi.getCheeseAmount() > 5 and rc.getLocation().distanceSquaredTo(mi.getMapLocation()) <= 8:
                        if rc.getLocation().distanceSquaredTo(mi.getMapLocation()) < 4:
                            Globals.pickUpCheese(mi.getMapLocation())
                            break
                        d = rc.getLocation().directionTo(mi.getMapLocation())
                        if rc.getLocation().add(d).isAdjacentTo(mi.getMapLocation()) and rc.canMove(d):
                            rc.move(d)
                            Globals.pickUpCheese(mi.getMapLocation())
                            break
                        d = d.rotateLeft()
                        if rc.getLocation().add(d).isAdjacentTo(mi.getMapLocation()) and rc.canMove(d):
                            rc.move(d)
                            Globals.pickUpCheese(mi.getMapLocation())
                            break
                        d = d.rotateRight().rotateRight()
                        if rc.getLocation().add(d).isAdjacentTo(mi.getMapLocation()) and rc.canMove(d):
                            rc.move(d)
                            Globals.pickUpCheese(mi.getMapLocation())
                            break

        Navigator.moveTo(Globals.closestKing, True)

        location = Globals.closestKing.add(Globals.closestKing.directionTo(rc.getLocation()))

        if not urgent:
            for d in Globals.adjacentDirections:
                if rc.canPickUpCheese(rc.getLocation().add(d)):
                    Globals.pickUpCheese(rc.getLocation().add(d))

        if rc.canTransferCheese(location, rc.getRawCheese()):
            rc.transferCheese(location, rc.getRawCheese())
            if Miner.newKing is not None:
                Comms.squeakNewKing(Miner.newKing)
                Miner.newKing = None
            Miner.cheese = None
            Miner.returningToKing = False

    @staticmethod
    def shouldBeMiner():
        rc = Globals.rc
        if rc.getRawCheese() == 0:
            Miner.returningToKing = False
        if rc.getRawCheese() >= Globals.minerReturnThreshold or (rc.getRawCheese() >= Globals.minerSecondaryReturnThreshold and rc.getLocation().distanceSquaredTo(Globals.closestKing) <= Globals.secondaryReturnDistance):
            Miner.returningToKing = True
        if Miner.mine is not None or Miner.cheese is not None or Miner.returningToKing:
            return True
        if Miner.findMine() or Miner.findCheese():
            return True
        return False

    knownSym = 0

    @staticmethod
    def run():
        rc = Globals.rc
        if Miner.newKing is None:
            mightNeedKing = True
            newMine = Miner.needNewKing()
            if newMine is not None:
                for ml in Globals.kingPos:
                    if ml is not None and ml.distanceSquaredTo(newMine) <= Globals.closeToKing:
                        mightNeedKing = False
                if mightNeedKing:
                    print("NEED NEW KING!!!")
                    Miner.newKing = newMine

        if Miner.cheese is not None:
            rc.setIndicatorLine(rc.getLocation(), Miner.cheese, 0, 255, 0)

        # read the help signals
        if rc.readSharedArray(60) > 0 and Comms.getNumKings() == 1:
            Miner.returnToKing(True)
            return


        needSacrifice = Comms.getSacrifices()
        if needSacrifice is not None:
            squeakToo = True
            if needSacrifice.x >= 1000:
                squeakToo = False
                needSacrifice = MapLocation(needSacrifice.x - 1000, needSacrifice.y - 1000)
            Multiking.Multiking.newKingPos = needSacrifice
            Multiking.Multiking.moveTo()
            if rc.getLocation().distanceSquaredTo(needSacrifice) <= 8 and rc.canBecomeRatKing():
                rc.becomeRatKing()
            if squeakToo:
                Comms.squeakForSacrificesToo(needSacrifice)
            return


        # return to king
        if Miner.returningToKing:
            Miner.returnToKing(False)
            return

        # choose the closest thing to attack
        if len(Globals.enemyRobots) > 0:
            if rc.getGlobalCheese() > Globals.emergencyReserve and rc.getRawCheese() <= 20:
                # attack the enemy
                target = None
                for robot in Globals.enemyRobots:
                    if robot.getType() == UnitType.BABY_RAT:
                        if target is None:
                            target = robot
                        elif rc.getLocation().distanceSquaredTo(target.getLocation()) > rc.getLocation().distanceSquaredTo(robot.getLocation()):
                            target = robot
                if target is not None:
                    Attack.Attack.attackBaby()
                    return
            else:
                # run to safety with the cheese
                Miner.returningToKing = True
                Miner.returnToKing(True)
                if Miner.returningToKing:
                    return


        # pick up cheese
        if Miner.cheese is not None:
            if Miner.mine is not None and not Miner.checkMineVacancy():
                return

            rc.setIndicatorString("miner: picking up cheese")

            # check that the cheese is still there
            if rc.canSenseLocation(Miner.cheese) and rc.senseMapInfo(Miner.cheese).getCheeseAmount() <= 0:
                Miner.cheese = None

            # cheese still there
            else:
                Navigator.moveTo(Miner.cheese, True)

                if rc.canPickUpCheese(Miner.cheese):
                    if rc.getRawCheese() < Globals.maxCheese:
                        Globals.pickUpCheese(Miner.cheese)

                    Miner.cheese = None

                    # check to return if i have a lot of cheese
                    if rc.getRawCheese() >= Globals.minerReturnThreshold or rc.getRawCheese() >= rc.getGlobalCheese():
                        Miner.returningToKing = True
                        Miner.returnToKing(False)

                    # look for next cheese, and turn towards
                    if Miner.findCheese():
                        if rc.canTurn():
                            Vision.turn(rc.getLocation().directionTo(Miner.cheese))
                    # no cheese found, turn towards the mine
                    else:
                        if rc.canTurn():
                            Vision.turn(rc.getLocation().directionTo(Miner.mine))
                return

        # move towards the mine, and then circle on the mine, looking for cheese
        if Miner.mine is not None:
            if not Miner.checkMineVacancy():
                return

            rc.setIndicatorString("miner: occupying mine, looking for cheese")

            # try to place a trap at (+1, +1) and (-1, -1)
            # if (rc.canPlaceRatTrap(mine.add(Direction.NORTHEAST))) rc.placeRatTrap(mine.add(Direction.NORTHEAST));
            # if (rc.canPlaceRatTrap(mine.add(Direction.SOUTHWEST))) rc.placeRatTrap(mine.add(Direction.SOUTHWEST));

            # if im at the mine, scan
            if rc.getLocation() == Miner.mine:
                if rc.canTurn():
                    # Java: Integer.bitCount(getID())
                    if bin(rc.getID()).count('1') % 2 == 0:
                        Vision.turn(rc.getDirection().rotateRight().rotateRight())
                    else:
                        Vision.turn(rc.getDirection().rotateLeft().rotateLeft())
            # otherwise move towards the mine
            else:
                # Java: Math.max / Math.abs
                Navigator.moveTo(Miner.mine, max(abs(Miner.mine.x - rc.getLocation().x), abs(Miner.mine.y - rc.getLocation().y)) > 2)
                if rc.canTurn():
                    Vision.turn(rc.getLocation().directionTo(Miner.mine))
                    Miner.checkMineVacancy()

            # look for cheese
            Miner.findCheese()
