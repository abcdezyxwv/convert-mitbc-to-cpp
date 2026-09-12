# Port of bestsofar/King.java. See py/CONVENTIONS.md.
from api import *
from Utils.Globals import Globals
from Utils import Attack
from Utils.BugNavigator import BugNavigator
from Utils.Comms import Comms
from Utils.Symmetry import Symmetry
from Roles import Rush

# Java: import static bestsofar.Utils.BugNavigator.distance1d
distance1d = BugNavigator.distance1d


class King(Globals):

    lastCatTrap = -5
    lastRatTrap = -5

    # SPAWNING ------------------------------------------------------------ //

    @staticmethod
    def spawn():
        kingLoc = Globals.rc.getLocation()
        spawnPositionCandidates = [None] * 28
        spdSize = 0

        # possible spawning locs
        for cand in Globals.rc.getAllLocationsWithinRadiusSquared(Globals.rc.getLocation(), 10):
            if Globals.rc.onTheMap(cand) and Globals.rc.canBuildRat(cand):
                Globals.rc.setIndicatorDot(cand, 255, 255, 255)
                spawnPositionCandidates[spdSize] = cand
                spdSize += 1

        if spdSize > 0:
            # build facing centre
            if Rush.Rush.spawnLoc is None:
                Rush.Rush.spawnLoc = Globals.rc.getLocation()
            target = Rush.Rush.getNewRushLocation()
            todo = None
            bestDist = 1000000

            for i in range(spdSize):
                # value of building here
                if spawnPositionCandidates[i].distanceSquaredTo(target) < bestDist:
                    bestDist = spawnPositionCandidates[i].distanceSquaredTo(target)
                    todo = spawnPositionCandidates[i]
            if Globals.rc.canTurn():
                Globals.rc.turn(Globals.rc.getLocation().directionTo(todo))
            Globals.rc.buildRat(todo)

    @staticmethod
    def spawnAmountThreshold():
        # return safeCheeseReserve;

        res = Globals.rc.getCurrentRatCost() * (20 - (15 * Globals.rc.getRoundNum()) // 2000)

        # should it be dependent on map size?
        # maybe smaller map = lower threshold -> rush

        return res

    @staticmethod
    def insaneSpawnAmountThreshold():
        res = Globals.rc.getCurrentRatCost() * (40 - (15 * Globals.rc.getRoundNum()) // 2000)
        return min(res, (1200 if Globals.rc.getRoundNum() > Globals.midgame else 2000))

    @staticmethod
    def spawnIf():
        if (Globals.rc.getGlobalCheese() - Globals.rc.getCurrentRatCost() > King.spawnAmountThreshold() or (Globals.rc.getGlobalCheese() >= Globals.minCheese and Globals.rc.getCurrentRatCost() < (Globals.minNumberRats // 4) * 10 + 10)):
            if Globals.rc.getCurrentRatCost() < (Globals.maxNumberRats // 4) * 10 + 10 or Globals.rc.getGlobalCheese() - Globals.rc.getCurrentRatCost() > King.insaneSpawnAmountThreshold() or Globals.rc.getRoundNum() > Globals.endgame:
                King.spawn()

    # SURVIVAL ------------------------------------------------------------ //

    lastDir = None
    unsafe = [None] * 20
    unsafeTime = [0] * 20

    @staticmethod
    def moveSafety():
        if Globals.rc.getRoundNum() == Globals.spawnRound:
            return
        # find the place with the minimum penalty

        score = [0, 0, 0, 0, 0, 0, 0, 0, 0]

        mines = []

        disabled = [False, False, False, False, False, False, False, False, False]

        for mi in Globals.surroundings:

            if mi.isWall() and distance1d(Globals.rc.getLocation(), mi.getMapLocation()) == 3:
                #
                # for (int i = 0; i < 9; i++) if (!disabled[i] && BugNavigator.distance1d(rc.getLocation().add(Direction.DIRECTION_ORDER[i]), mi.getMapLocation()) == 2)
                #     disabled[i] = true;
                #
                continue

            dir = Globals.rc.getLocation().directionTo(mi.getMapLocation())
            penalty = 30 - (Globals.rc.getLocation().add(dir).distanceSquaredTo(mi.getMapLocation()))
            score[Globals.rc.getLocation().directionTo(mi.getMapLocation()).getDirectionOrderNum()] -= 0 if penalty < 0 else penalty * mi.getCheeseAmount()

            if mi.hasCheeseMine():
                mines.append(mi.getMapLocation())

        hasCheese = []

        for ri in Globals.allyRobots:
            if ri.getRawCheeseAmount() > 0:
                hasCheese.append(ri)

        for dir in Direction.DIRECTION_ORDER:
            num = dir.getDirectionOrderNum()
            # cat wapoint
            # for (int i = 0; i < 20; i ++) if (unsafe[i] != null && rc.getRoundNum() - unsafeTime[i] < 30) {
            #     int penalty = 30 - (rc.getLocation().add(dir).distanceSquaredTo(unsafe[i]));
            #     score[num] += 100 * penalty;
            # }
            # robot
            loc = Globals.rc.getLocation().add(dir)
            for robot in hasCheese:
                penalty = 50 - (loc.distanceSquaredTo(robot.getLocation()))
                score[num] -= (robot.getRawCheeseAmount()) * penalty * 2  # Java: /*20 +*/ inside the parens
            for robot in Globals.enemyRobots:
                penalty = 50 - (loc.distanceSquaredTo(robot.getLocation()))
                score[num] += 200000 * penalty
            for robot in Globals.catRobots:
                penalty = 50 - (loc.distanceSquaredTo(robot.getLocation()))
                score[num] += 2000000 * penalty  # cat super scary
            for ml in mines:
                penalty = 50 - (loc.distanceSquaredTo(ml))
                penalty = 50 if penalty > 40 else penalty
                score[num] -= 2000 * penalty

        scores = ""
        for i in range(9):
            scores += " " + str(score[i])
        Globals.rc.setIndicatorString(scores)

        best = 1000000000
        dir = None
        if Globals.rc.canMove(Direction.DIRECTION_ORDER[0]) and score[0] < best and not disabled[0]:
            best = score[0]
            dir = Direction.DIRECTION_ORDER[0]
        if Globals.rc.canMove(Direction.DIRECTION_ORDER[1]) and score[1] < best and not disabled[1]:
            best = score[1]
            dir = Direction.DIRECTION_ORDER[1]
        if Globals.rc.canMove(Direction.DIRECTION_ORDER[2]) and score[2] < best and not disabled[2]:
            best = score[2]
            dir = Direction.DIRECTION_ORDER[2]
        if Globals.rc.canMove(Direction.DIRECTION_ORDER[3]) and score[3] < best and not disabled[3]:
            best = score[3]
            dir = Direction.DIRECTION_ORDER[3]
        if Globals.rc.canMove(Direction.DIRECTION_ORDER[4]) and score[4] < best and not disabled[4]:
            best = score[4]
            dir = Direction.DIRECTION_ORDER[4]
        if Globals.rc.canMove(Direction.DIRECTION_ORDER[5]) and score[5] < best and not disabled[5]:
            best = score[5]
            dir = Direction.DIRECTION_ORDER[5]
        if Globals.rc.canMove(Direction.DIRECTION_ORDER[6]) and score[6] < best and not disabled[6]:
            best = score[6]
            dir = Direction.DIRECTION_ORDER[6]
        if Globals.rc.canMove(Direction.DIRECTION_ORDER[7]) and score[7] < best and not disabled[7]:
            best = score[7]
            dir = Direction.DIRECTION_ORDER[7]
        if Globals.rc.canMove(Direction.DIRECTION_ORDER[8]) and score[8] < best and not disabled[8]:
            best = score[8]
            dir = Direction.DIRECTION_ORDER[8]
        if dir is not None and not Direction.CENTER == dir:
            if Globals.rc.canMove(dir):
                Globals.rc.move(dir)
            if len(Globals.enemyRobots) == 0 and Globals.catLoc is None:
                King.lastDir = dir
            else:
                King.lastDir = None
        else:
            doMove = True
            mi = Globals.rc.senseNearbyMapInfos()
            for i in range(len(mi)):
                if mi[i].hasCheeseMine():
                    doMove = False
            if doMove and King.lastDir is not None and Globals.rc.canMove(King.lastDir) and not disabled[King.lastDir.getDirectionOrderNum()]:
                Globals.rc.move(King.lastDir)
        if Globals.rc.isMovementReady() and len(Globals.enemyRobots) == 0 and len(Globals.catRobots) == 0 and King.lastSeenEnemy > 8:
            random = Globals.adjacentDirections[Globals.rng.nextInt(8)]
            if Globals.rc.canMove(random):
                Globals.rc.move(random)

    catID = [0] * 15
    catRound = [0] * 15
    pointer = 0

    @staticmethod
    def defendCats():
        # List of the last 15 seen cats with (id, num)
        for cat in Globals.catRobots:
            King.catID[King.pointer] = cat.getID()
            King.catRound[King.pointer] = Globals.rc.getRoundNum()
            King.pointer += 1
            King.pointer %= 15
        # Check if the current map location is already documented
        # boolean canSkip = false;
        # for (int j = 0; j < 20; j ++) if (unsafe[j] != null) {
        #     if (rc.getLocation().isWithinDistanceSquared(unsafe[j], 8)) {
        #         canSkip = true;
        #         break;
        #     }
        # }
        # // Check if any cats constantly bother us
        # for (int i = 0; !canSkip && i < pointer; i ++) if (catID[i] > 0) {
        #     int ID = catID[i], annoying = 0;
        #     // check how many times we've seen it in past 30 rounds
        #     for (int j = 0; j < pointer; j ++) if (catID[j] == ID && rc.getRoundNum() - catRound[j] <= 20) {
        #         annoying ++;
        #     }
        #     if (annoying >= 4) {
        #         // current map location is dangerous
        #         MapLocation furthest = unsafe[0];
        #         int id = 0;
        #         for (int j = 1; j < 20; j ++) {
        #             if (unsafe[j] == null || furthest == null || rc.getRoundNum() - unsafeTime[j] > 30) {
        #                 furthest = unsafe[j];
        #                 id = j;
        #             } else {
        #                 if (rc.getLocation().distanceSquaredTo(unsafe[j]) > rc.getLocation().distanceSquaredTo(furthest)) {
        #                     furthest = unsafe[j];
        #                     id = j;
        #                 }
        #             }
        #         }
        #         unsafe[id] = rc.getLocation();
        #     }
        # }

        # Cat defence
        catAttack = None
        distCat = 1000000

        if Globals.catLoc is not None:
            if Globals.rc.isActionReady():
                #
                # MapLocation attempt = rc.getLocation().add(rc.getLocation().directionTo(catLoc));
                # attempt = attempt.add(attempt.directionTo(catLoc));
                # if (rc.canPlaceDirt(attempt)) {
                #     rc.placeDirt(attempt);
                # } else {
                #     attempt = rc.getLocation().add(rc.getLocation().directionTo(catLoc)).add(rc.getLocation().directionTo(catLoc));
                #     if (rc.canPlaceDirt(attempt)) {
                #         rc.placeDirt(attempt);
                #     }
                # }
                #
                # only place cat traps if cat is too close AHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH
                for cand in Globals.rc.getAllLocationsWithinRadiusSquared(Globals.rc.getLocation(), 8):
                    if Globals.catLoc is not None and Globals.rc.canPlaceCatTrap(cand):
                        dist = cand.distanceSquaredTo(Globals.catLoc)
                        if dist < distCat:
                            distCat = dist
                            catAttack = cand
        if Globals.rc.getRoundNum() - King.lastCatTrap >= Globals.catSpacing and catAttack is not None and Globals.rc.canPlaceCatTrap(catAttack):
            Globals.rc.placeCatTrap(catAttack)
            King.lastCatTrap = Globals.rc.getRoundNum()

    @staticmethod
    def tryAttack():
        if not Globals.rc.isActionReady():
            return
        close = Globals.rc.getAllLocationsWithinRadiusSquared(Globals.rc.getLocation(), 8)
        for i in range(len(close)):
            if Globals.rc.canAttack(close[i]):
                Globals.rc.attack(close[i])
                return

    @staticmethod
    def defendRats():
        # Only place traps underneath rats
        minHealth = 120
        weak = None
        for bot in Globals.enemyRobots:
            if Globals.rc.getLocation().distanceSquaredTo(bot.getLocation()) <= 8:
                if bot.getHealth() < minHealth:
                    minHealth = bot.getHealth()
                    weak = bot
        if weak is not None and Globals.rc.isActionReady():
            if minHealth < 15:
                # snipe
                cheeseBoost = 0
                if minHealth == 11:
                    cheeseBoost = 1
                elif minHealth == 12:
                    cheeseBoost = 2
                elif minHealth == 13:
                    cheeseBoost = 5
                elif minHealth == 14:
                    cheeseBoost = 10
                cheeseBoost = min(cheeseBoost, Globals.rc.getGlobalCheese())
                if Globals.rc.canAttack(weak.getLocation(), cheeseBoost):
                    Globals.rc.attack(weak.getLocation(), cheeseBoost)
            else:
                # trap them
                if Globals.rc.canPlaceRatTrap(weak.getLocation()):
                    Globals.rc.placeRatTrap(weak.getLocation())

        if len(Globals.allyRobots) <= len(Globals.enemyRobots) and len(Globals.enemyRobots) > 0:
            sumX = 0
            sumY = 0
            for i in range(len(Globals.enemyRobots)):
                sumX += Globals.enemyRobots[i].location.x
                sumY += Globals.enemyRobots[i].location.y

            sumX = (sumX + (len(Globals.newestSqueaks) + 1) // 2) // (len(Globals.newestSqueaks) + 1)
            sumY = (sumY + (len(Globals.newestSqueaks) + 1) // 2) // (len(Globals.newestSqueaks) + 1)

            bestScore = 10000000
            bestLocation = None

            nearbyLocations = Globals.rc.getAllLocationsWithinRadiusSquared(Globals.rc.getLocation(), 8)

            centroid = MapLocation(sumX, sumY)

            for i in range(len(nearbyLocations)):
                if Globals.rc.canBuildRat(nearbyLocations[i]):
                    score = nearbyLocations[i].distanceSquaredTo(centroid)
                    for j in range(len(Globals.enemyRobots)):
                        if nearbyLocations[i].distanceSquaredTo(Globals.enemyRobots[j].location) <= 8:
                            score += 100000
                    if score < bestScore:
                        bestScore = score
                        bestLocation = nearbyLocations[i]

            if bestLocation is not None:
                if Globals.rc.canTurn():
                    Globals.rc.turn(Globals.rc.getLocation().directionTo(bestLocation))
                Globals.rc.buildRat(bestLocation)

    @staticmethod
    def tryDigDirt():
        if Globals.catLoc is not None:
            return
        mls = Globals.rc.getAllLocationsWithinRadiusSquared(Globals.rc.getLocation(), 8)
        for i in range(len(mls)):
            if Globals.rc.canRemoveDirt(mls[i]):
                Globals.rc.removeDirt(mls[i])
                break

    newKingPos = None

    lastSeenEnemy = 0

    @staticmethod
    def needNewKing():
        King.newKingPos = Comms.needNewKing()
        if King.newKingPos is not None:
            for ml in Globals.kingPos:
                if ml is not None and ml.distanceSquaredTo(King.newKingPos) <= Globals.closeToKing:
                    King.newKingPos = None
                    Comms.clearNewKing()
                    break
        if King.newKingPos is not None:
            return
        ml = Comms.checkForNewKings()
        if ml is None:
            return
        if King.newKingPos is None:
            King.newKingPos = ml
        print("RECIEVED!!!")
        for loc in Globals.kingPos:
            if loc is not None and loc.distanceSquaredTo(King.newKingPos) <= Globals.closeToKing:
                King.newKingPos = None
                return
        Comms.encodeNewKingPos(King.newKingPos)

    @staticmethod
    def spawnNewKing():
        if King.newKingPos is None:
            return
        num = Comms.getNumberBots()
        if num < Globals.botsForNewKing:
            if Globals.rc.getGlobalCheese() - Globals.rc.getCurrentRatCost() > Globals.newKingSpawnThreshold:
                best = 1000000
                ml = None
                for loc in Globals.rc.getAllLocationsWithinRadiusSquared(Globals.rc.getLocation(), 8):
                    dist = loc.distanceSquaredTo(King.newKingPos)
                    if Globals.rc.canBuildRat(loc) and dist < best:
                        best = dist
                        ml = loc
                if ml is not None:
                    print("SPWANED!")
                    if Globals.rc.canTurn():
                        Globals.rc.turn(Globals.rc.getLocation().directionTo(ml))
                    Globals.rc.buildRat(ml)
                    Comms.incNewKingBotCount(num)
        else:
            Comms.incNewKingBotCount(num)
            King.newKingPos = None
            Comms.clearNewKing()

    @staticmethod
    def run():

        if Globals.rc.getRoundNum() == Globals.spawnRound:
            Comms.clearNewKing()
            King.lastDir = Globals.rc.getLocation().directionTo(MapLocation(Globals.mapWidth // 2, Globals.mapHeight // 2))

        # symmetry
        Symmetry.updateSymmetryFromGlobal()
        # if (rc.getRoundNum() != 1) Symmetry.updateNearbySymmetry(); // it's bytecode exceeding really bad :(
        Symmetry.hearNearbySymmetrySqueaks()

        # write to global
        if Comms.getSymmetry() != Symmetry.symm:
            Comms.updateSymmetry(Symmetry.symm)

        if len(Globals.enemyRobots) > 0 or len(Globals.catRobots) > 0:
            King.lastSeenEnemy = 0
        else:
            King.lastSeenEnemy += 1

        King.moveSafety()

        # if (Clock.getBytecodeNum() > 12000) return;

        # collect cheese
        for loc in Globals.rc.getAllLocationsWithinRadiusSquared(Globals.rc.getLocation(), 8):
            if Globals.rc.canPickUpCheese(loc) and Globals.rc.getRawCheese() < Globals.maxCheese:
                Globals.pickUpCheese(loc)

        King.defendCats()
        King.defendRats()

        if Globals.rc.getRoundNum() <= 1200:
            King.needNewKing()
            King.spawnNewKing()
        else:
            Comms.clearNewKing()

        King.spawnIf()

        # try to attack baby -> cat -> king
        if not Attack.Attack.attackBaby():
            if not Attack.Attack.attackCat():
                Attack.Attack.attackKing()

        King.tryDigDirt()

        King.tryAttack()

        # send emergency signal
        if Globals.rc.getRoundNum() >= Globals.endgame or (Globals.rc.getHealth() <= Globals.help2Health and len(Globals.enemyRobots) >= Globals.help2Enemies):
            Globals.rc.writeSharedArray(60, 2)
        elif Globals.rc.getHealth() <= Globals.help1Health and len(Globals.enemyRobots) >= Globals.help1Enemies:
            Globals.rc.writeSharedArray(60, 1)
        else:
            Globals.rc.writeSharedArray(60, 0)

        Comms.squeakEnemies()

        if King.newKingPos is not None:
            Globals.rc.setIndicatorString(str(King.newKingPos))
