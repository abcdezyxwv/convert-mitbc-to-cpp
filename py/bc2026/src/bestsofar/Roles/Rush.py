# Port of bestsofar/Roles/Rush.java. See py/CONVENTIONS.md.
from api import *

# Java: import bestsofar.Baby -- bound as a module (accessed as Baby.Baby)
# because Baby imports this file back; module binding defers the class lookup
# to call time and avoids the circular-import failure.
import Baby
from Utils import Attack
from Utils.Globals import Globals
from Utils.Navigator import Navigator
from Utils.Symmetry import Symmetry
from Utils.Vision import Vision


class Rush(Globals):

    spawnLoc = None
    rush = None
    approx = None
    remainingSym = 0
    guessedSym = 0
    susFactor = [0] * 5
    turnsStuck = 0
    bestDist = 0
    approxRound = 0
    kingFound = False

    @staticmethod
    def getNewRushLocation():

#        // If all the symmetries have been tried
#        if (remainingSym == 7) {
#            Baby.explorer = true;
#            guessedSym = 0;
#            return new MapLocation(rng.nextInt(mapWidth), rng.nextInt(mapHeight));
#        }

        possibleSymmetries = Symmetry.getPossibleSymmetries()
        possibleRushLocations = [None] * 6
        guesses = [0] * 6
        prlSize = 0

        for s in possibleSymmetries:
            guesses[prlSize] = s
            possibleRushLocations[prlSize] = Symmetry.symmetricallyOpposite(Rush.spawnLoc, s)
            prlSize += 1

            if s == 4:
                guesses[prlSize] = s
                possibleRushLocations[prlSize] = Symmetry.symmetricallyOpposite(Rush.spawnLoc, s)
                prlSize += 1
                guesses[prlSize] = s
                possibleRushLocations[prlSize] = Symmetry.symmetricallyOpposite(Rush.spawnLoc, s)
                prlSize += 1
                guesses[prlSize] = s
                possibleRushLocations[prlSize] = Symmetry.symmetricallyOpposite(Rush.spawnLoc, s)
                prlSize += 1

        pray = Globals.rng.nextInt(prlSize)
        Rush.guessedSym = guesses[pray]

        return Globals.mapLocationAddNoise(possibleRushLocations[pray], 3)

    @staticmethod
    def run(spawn):
        rc = Globals.rc
        if Rush.spawnLoc is None:
            Rush.spawnLoc = spawn
        Rush.spawnLoc = spawn

        if rc.canTurn():
            for i in range(len(Globals.enemyRobots)):
                ri = Globals.enemyRobots[i]
                if ri.getType() == UnitType.RAT_KING:
                    Rush.kingFound = True
                    dir = rc.getLocation().directionTo(ri.location)
                    Vision.turn(dir)
                    break

        # return to save the king
        mode = rc.readSharedArray(60)
        if mode == 2:
            # very urgent
            if not Rush.kingFound:
                Navigator.moveTo(Globals.kingPos[0], True)
        elif mode == 1:
            # see which one is closer
            if rc.getLocation().distanceSquaredTo(Rush.rush) > rc.getLocation().distanceSquaredTo(Globals.kingPos[0]):
                Navigator.moveTo(Globals.kingPos[0], True)

        # guess symmetry
#        remainingSym |= Symmetry.symm;
        if Rush.kingFound:
            Rush.guessedSym = 0
        if Rush.guessedSym > 0:
            if (Symmetry.symm & Rush.guessedSym) > 0:
                Rush.guessedSym = 0
                Rush.rush = None
        if Rush.rush is None:
            Rush.rush = Rush.getNewRushLocation()
            Rush.bestDist = rc.getLocation().distanceSquaredTo(Rush.rush)
        if not Rush.kingFound and rc.getLocation().isWithinDistanceSquared(Rush.rush, 4):
            Rush.turnsStuck = 0
#            susFactor[guessedSym] += 1;
#            if (susFactor[guessedSym] > 3) remainingSym |= guessedSym;
            # Java: Integer.bitCount(Symmetry.symm)
            if bin(Symmetry.symm).count('1') == 2:
                Baby.Baby.explorer = True
                return
            Rush.rush = Rush.getNewRushLocation()
            Rush.bestDist = rc.getLocation().distanceSquaredTo(Rush.rush)
        if not Rush.kingFound and Rush.approx is not None and rc.getLocation().isWithinDistanceSquared(Rush.approx, 2):
            # Java: rng.nextInt() % 3 -- the api Random.nextInt() yields
            # non-negative values, so Python % matches Java's truncating %.
            Rush.approx = MapLocation(Rush.approx.x + Globals.rng.nextInt() % 3, Rush.approx.y + Globals.rng.nextInt() % 3)
        if not Rush.kingFound and (rc.getLocation().isWithinDistanceSquared(Rush.rush, 2) or Rush.turnsStuck > 19):
            Rush.turnsStuck = 0
#            susFactor[guessedSym] += 1;
#            if (susFactor[guessedSym] > 3) remainingSym |= guessedSym;
            Rush.rush = Rush.getNewRushLocation()
            Rush.bestDist = rc.getLocation().distanceSquaredTo(Rush.rush)
        # if it can see the enemy king, direct it towards it
        for robot in Globals.enemyRobots:
            if robot.getType() == UnitType.RAT_KING:
                Rush.rush = robot.getLocation()
                Rush.kingFound = True
                break
        # read the squeaks
        for message in rc.readSqueaks(-1):
            m = message.getBytes()
            if (m & (1 << 30)) == 0:
                continue
            m ^= (1 << 30)
            # Java: int division and % truncate toward zero (m may be negative)
            r = int(m / 10000)
            x = int((m - int(m / 10000) * 10000) / 100)
            y = m - int(m / 100) * 100
            if r > Rush.approxRound:
                Rush.approxRound = r
                Rush.approx = MapLocation(x, y)
        if Rush.kingFound:
            msg = 10000 * (rc.getRoundNum() + 20) + 100 * Rush.rush.x + Rush.rush.y
            msg |= (1 << 30)
            rc.squeak(msg)
            Globals.hasSqueaked = True
        elif Rush.approx is not None:
            msg = 10000 * Rush.approxRound + 100 * Rush.approx.x + Rush.approx.y
            msg |= (1 << 30)
            rc.squeak(msg)
            Globals.hasSqueaked = True
        # no need to return, should be suicidal
        if Rush.rush is not None:
            if Rush.kingFound:
                Navigator.moveTo(Rush.rush, True)
            elif Rush.approx is not None:
                Navigator.moveTo(Globals.closestOnMap(Rush.approx), True)
            else:
                Navigator.moveTo(Rush.rush, True)
                newDist = rc.getLocation().distanceSquaredTo(Rush.rush)
                if newDist < Rush.bestDist:
                    Rush.bestDist = newDist
                    Rush.turnsStuck = 0
                else:
                    Rush.turnsStuck += 1

        Attack.Attack.attackKing()
        Attack.Attack.attackBaby()
