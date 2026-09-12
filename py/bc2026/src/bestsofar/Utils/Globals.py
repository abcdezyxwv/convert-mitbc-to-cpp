# Port of bestsofar/Utils/Globals.java. See py/CONVENTIONS.md.
from api import *
from Utils.AdditionalClasses.Threat import Threat
from Utils.AdditionalClasses.Thrown import Thrown
from Utils.FastSet import FastSet

# Java imports bestsofar.Baby, bestsofar.Roles.Multiking and
# bestsofar.Utils.{Comms,Movement,Reachability,Vision}. All of those classes
# extend Globals and import this module at class-definition time, so they are
# imported lazily inside the methods that use them (circular import).


class Globals:
    rc = None  # RobotController

    trapGlobalCheeseThreshold = 250
    safeCheeseReserve = 600
    emergencyReserve = 250
    catSpacing = 4
    ratSpacing = 2
    pacifistRounds = 200
    help1Health = 250
    help1Enemies = 3
    help2Health = 100
    help2Enemies = 2
    endgame = 1960
    midgame = 300
    cheeseThreshold = 50
    minNumberRats = 12
    maxNumberRats = 16
    minCheese = 110
    doSpawnThreshold = 2500
    attackerNumber = 2
    useTrapCheeseThreshold = 500
    globalCheeseTrapSubstitute = 40
    secondBestMoveChance = 0.2
    disintegrationHP = 10
    minerReturnThreshold = 40
    maxCheese = 200
    minerSecondaryReturnThreshold = 20
    secondaryReturnDistance = 200
    newKingCheeseThreshold = 200
    newKingSquaresThreshold = 5
    newKingSpawnThreshold = 1200
    botsForNewKing = 9
    giveUpNewKing = 25
    closeToKing = 100

    rng = None  # Random
    directions = [
        Direction.NORTH,
        Direction.NORTHEAST,
        Direction.EAST,
        Direction.SOUTHEAST,
        Direction.SOUTH,
        Direction.SOUTHWEST,
        Direction.WEST,
        Direction.NORTHWEST,
        Direction.CENTER
    ]

    surroundings = None  # MapInfo[]
    allyRobots = None  # RobotInfo[]
    enemyRobots = None  # RobotInfo[]
    catRobots = None  # RobotInfo[]
    catsLastTurn = []
    kingPos = None  # MapLocation[]
    catLoc = None
    newestSqueaks = None  # Message[]
    alliesThrown = None  # Thrown[]
    closestKing = None
    closestEnemy = None  # RobotInfo
    closestEnemyKing = None
    squeaksReadLastRound = 0
    locationLastRound = None
    moreAllies = None  # ArrayList<RobotInfo>

    symmetry = 0
    hasSqueaked = False
    enemiesLastRound = False
    cantTurn = False
    cantMove = False

    mapWidth = 0
    mapHeight = 0
    spawnRound = 0

    internalRoundNum = 0
    myId = 0
    myTeam = None
    opponentTeam = None
    threats = None  # Threat[]
    allDirections = Direction.allDirections()  # Java: Direction.values()
    adjacentDirections = [
        Direction.NORTH,
        Direction.EAST,
        Direction.SOUTH,
        Direction.WEST,
        Direction.NORTHEAST,
        Direction.SOUTHEAST,
        Direction.SOUTHWEST,
        Direction.NORTHWEST
    ]

    @staticmethod
    def init(robotController):
        from Baby import Baby
        from Roles.Multiking import Multiking
        from Utils.Comms import Comms
        from Utils.Movement import Movement
        from Utils.Vision import Vision

        Globals.rc = robotController

        Globals.mapWidth = Globals.rc.getMapWidth()
        Globals.mapHeight = Globals.rc.getMapHeight()

        Globals.spawnRound = Globals.rc.getRoundNum()

        Globals.internalRoundNum = Globals.rc.getRoundNum() - 1
        Globals.myId = Globals.rc.getID()
        Globals.myTeam = Globals.rc.getTeam()
        Globals.opponentTeam = opponent(Globals.myTeam)  # Java: myTeam.opponent()

        Globals.kingPos = [None] * 5

        Globals.newestSqueaks = []
        Globals.alliesThrown = []

        Globals.cantMove = False
        Globals.cantTurn = False

        Globals.rng = Random(Globals.rc.getID())

        Globals.symmetry = Comms.getSymmetry()

        if Globals.rc.getType() == UnitType.BABY_RAT:
            Baby.isNewKing = Multiking.isMultiking()

        Vision.init()
        Comms.init()
        Movement.init()

    lastRound = None  # Message[]
    thisRound = None  # Message[]

    @staticmethod
    def startTurn():
        from Utils.Comms import Comms
        from Utils.Reachability import Reachability
        from Utils.Vision import Vision

        Comms.startTurn()

        Globals.surroundings = Globals.rc.senseNearbyMapInfos()
        Globals.allyRobots = Globals.rc.senseNearbyRobots(-1, Globals.myTeam)

        knownAllies = FastSet()
        for r in Globals.allyRobots:
            knownAllies.add(MapLocation(r.getID() % 64, (r.getID() >> 6) % 64))

        Globals.enemyRobots = Globals.rc.senseNearbyRobots(-1, Globals.opponentTeam)
        Globals.catRobots = Globals.rc.senseNearbyRobots(-1, Team.NEUTRAL)

        Globals.lastRound = Globals.rc.readSqueaks(Globals.rc.getRoundNum() - 1)
        Globals.thisRound = Globals.rc.readSqueaks(Globals.rc.getRoundNum())

        Globals.internalRoundNum += 1

        if Globals.rc.getRoundNum() != Globals.internalRoundNum:
            # oh no
            Globals.newestSqueaks = [None] * len(Globals.thisRound)
            for i in range(len(Globals.thisRound)):
                Globals.newestSqueaks[i] = Globals.thisRound[i]
            Globals.internalRoundNum = Globals.rc.getRoundNum()
            if Globals.rc.getRoundNum() > Globals.spawnRound + 5:
                print("bytecode limit exceeeeeeeeded :(")
        elif len(Globals.lastRound) >= Globals.squeaksReadLastRound:
            Globals.newestSqueaks = [None] * (len(Globals.lastRound) - Globals.squeaksReadLastRound + len(Globals.thisRound))

            for i in range(Globals.squeaksReadLastRound, len(Globals.lastRound)):
                Globals.newestSqueaks[i - Globals.squeaksReadLastRound] = Globals.lastRound[i]
            for i in range(len(Globals.thisRound)):
                Globals.newestSqueaks[i + len(Globals.lastRound) - Globals.squeaksReadLastRound] = Globals.thisRound[i]

        enemyKingHeard = None

        sz = 0
        sza = 0
        for msg in Globals.newestSqueaks:
            m = msg.getBytes()
            if msg.getBytes() < 0:
                sz += 1
            elif 8 <= msg.getBytes() < 16:
                sza += 1
            elif enemyKingHeard is None and (m & (1 << 25)) > 0:
                y = m & 0b111111
                m = m >> 6
                x = m & 0b111111
                enemyKingHeard = MapLocation(x, y)

        threats = [None] * sz
        Globals.alliesThrown = [None] * sza

        Globals.moreAllies = []

        ptr = 0
        sz = 0
        for m in Globals.newestSqueaks:
            if m.getBytes() <= -1:
                msg = -m.getBytes()
                # strongest first

                hp = msg % 1024
                msg >>= 12
                dir = Direction.DIRECTION_ORDER[1 + msg % 8]
                if not knownAllies.contains(MapLocation(m.getSenderID() % 64, (m.getSenderID() >> 6) % 64)):
                    # Java: new RobotInfo(m.getSenderID(), myTeam,
                    #   UnitType.BABY_RAT, hp, m.getSource(), dir, 0, 0, null)
                    # api.py field order differs; the trailing null
                    # carryingRobot argument has no api.py field.
                    Globals.moreAllies.append(RobotInfo(ID=m.getSenderID(), team=Globals.myTeam,
                                                        health=hp, location=m.getSource(),
                                                        direction=dir, chirality=0,
                                                        type=UnitType.BABY_RAT, rawCheeseAmount=0))
                msg >>= 3

                # weakest second
                dir = Comms.decodeDir(msg & 0b111)
                msg = msg >> 3
                y = (msg & 0b111111)
                msg = msg >> 6
                x = (msg & 0b111111)
                threats[ptr] = Threat(MapLocation(x, y), dir, False)
                ptr += 1
            elif 8 <= m.getBytes() < 16:
                Globals.alliesThrown[sz] = Thrown(m.getSource(), Direction.DIRECTION_ORDER[m.getBytes() - 7])
                sz += 1

        Globals.hasSqueaked = False
        closest = 0
        for i in range(1, 5):
            if Globals.kingPos[i] is None:
                break
            if Globals.rc.getLocation().distanceSquaredTo(Globals.kingPos[closest]) > Globals.rc.getLocation().distanceSquaredTo(Globals.kingPos[i]):
                closest = i
        Globals.closestKing = Globals.kingPos[closest]

        if Globals.rc.isBeingThrown():
            Comms.beingThrown()

        Vision.startTurn()
        if Globals.rc.getRoundNum() != Globals.spawnRound and Globals.rc.getType() == UnitType.BABY_RAT and len(Globals.enemyRobots) > 0:

            for ri in Globals.allyRobots:
                if ri.getType() == UnitType.BABY_RAT:
                    Vision.isWall[ri.location.x] |= 1 << ri.location.y
                else:
                    for ml in Globals.rc.getAllLocationsWithinRadiusSquared(ri.location, 2):
                        if Vision.hasSeenLocation(ml):
                            Vision.isWall[ri.location.x] |= 1 << ri.location.y

            Reachability.checkReachability(Globals.rc.getDirection())
            #for (MapLocation ml : rc.getAllLocationsWithinRadiusSquared(rc.getLocation(), -1))
            #    if (Vision.hasSeenLocation(ml) && Vision.canReach(ml))
            #        rc.setIndicatorDot(ml, 125, 125, 125);

            for ri in Globals.allyRobots:
                if ri.getType() == UnitType.BABY_RAT:
                    Vision.isWall[ri.location.x] &= ~(1 << ri.location.y)
                else:
                    for ml in Globals.rc.getAllLocationsWithinRadiusSquared(ri.location, 2):
                        if Vision.hasSeenLocation(ml):
                            Vision.isWall[ri.location.x] &= ~(1 << ri.location.y)

        Globals.closestEnemy = None
        Globals.closestEnemyKing = None
        reachableEnemies = []
        for info in Globals.enemyRobots:
            if Vision.hasSeenLocation(info.location) and not Vision.canReach(info.location):
                continue
            if info.type == UnitType.RAT_KING:
                if Globals.closestEnemyKing is None or Globals.rc.getLocation().distanceSquaredTo(info.location) < Globals.rc.getLocation().distanceSquaredTo(Globals.closestEnemyKing):
                    Globals.closestEnemyKing = info.location
            elif Globals.closestEnemy is None or Globals.rc.getLocation().distanceSquaredTo(info.location) < Globals.rc.getLocation().distanceSquaredTo(Globals.closestEnemy.location) or (info.health < Globals.closestEnemy.health and Globals.rc.getLocation().distanceSquaredTo(info.location) <= Globals.rc.getLocation().distanceSquaredTo(Globals.closestEnemy.location)):
                Globals.closestEnemy = info
            reachableEnemies.append(info)
        if Globals.closestEnemyKing is None:
            Globals.closestEnemyKing = enemyKingHeard

        Globals.enemyRobots = list(reachableEnemies)  # Java: reachableEnemies.toArray(new RobotInfo[0])

        for t in threats:
            Globals.rc.setIndicatorDot(t.loc, 255, 0, 0)
            if Vision.hasSeenLocation(t.loc) and not Vision.canReach(t.loc):
                continue
            if Globals.closestEnemy is None or Globals.rc.getLocation().distanceSquaredTo(t.loc) < Globals.rc.getLocation().distanceSquaredTo(Globals.closestEnemy.location):
                # Java: new RobotInfo(-1, opponentTeam, UnitType.BABY_RAT, 100,
                #   t.loc, t.dir, 0, 0, null) - see note above.
                Globals.closestEnemy = RobotInfo(ID=-1, team=Globals.opponentTeam,
                                                 health=100, location=t.loc,
                                                 direction=t.dir, chirality=0,
                                                 type=UnitType.BABY_RAT, rawCheeseAmount=0)

        Globals.catLoc = None
        for ri in Globals.catRobots:
            if Vision.hasSeenLocation(ri.location) and not Vision.canReach(ri.location):
                continue
            Globals.catLoc = ri.location

    @staticmethod
    def endTurn():
        from Utils.Comms import Comms
        from Utils.Vision import Vision

        # TODO: OPTIMISE THIS
        Globals.squeaksReadLastRound = len(Globals.rc.readSqueaks(Globals.rc.getRoundNum()))
        Globals.locationLastRound = Globals.rc.getLocation()
        Vision.endTurn()
        if Globals.closestEnemyKing is not None:
            Comms.squeakEnemyKing(Globals.closestEnemyKing)
        Globals.catsLastTurn = Globals.catRobots
        Globals.enemiesLastRound = len(Globals.enemyRobots) > 0

    @staticmethod
    def debugBytecode(tag, interval):
        if Globals.rc.getRoundNum() % interval != 0:
            return
        print("Bytecode used: " + str(Clock.getBytecodeNum()) + " - " + tag)

    @staticmethod
    def debug(string, interval):
        if Globals.rc.getRoundNum() % interval != 0:
            return
        print(string)

    @staticmethod
    def approxNumberBabies():
        return 4 * ((Globals.rc.getCurrentRatCost() // 10) - 1)  # cost >= 0: Java int division

    @staticmethod
    def getRobotLocations(loc, type):
        if type == UnitType.RAT_KING:
            return [
                loc.add(Globals.directions[0]),
                loc.add(Globals.directions[1]),
                loc.add(Globals.directions[2]),
                loc.add(Globals.directions[3]),
                loc.add(Globals.directions[4]),
                loc.add(Globals.directions[5]),
                loc.add(Globals.directions[6]),
                loc.add(Globals.directions[7]),
                loc.add(Globals.directions[8])
            ]
        if type == UnitType.CAT:
            return [
                loc.add(Direction.NORTH),
                loc.add(Direction.NORTHEAST),
                loc.add(Direction.EAST),
                loc.add(Direction.CENTER)
            ]
        return [loc]

    @staticmethod
    def closestOnMap(ml):
        return MapLocation((ml.x if ml.x >= 0 else 0) if ml.x < Globals.mapWidth else Globals.mapWidth - 1,
                           (ml.y if ml.y >= 0 else 0) if ml.y < Globals.mapHeight else Globals.mapHeight - 1)

    @staticmethod
    def isWithinVision(robotLocation, robotDirection, location, visionRadiusSquared):
        if visionRadiusSquared != -1 and visionRadiusSquared < robotLocation.distanceSquaredTo(location):
            return False
        location = MapLocation(location.x - robotLocation.x, location.y - robotLocation.y)
        if robotDirection.getDirectionOrderNum() <= 4:
            if robotDirection.getDirectionOrderNum() <= 2:
                if robotDirection.getDirectionOrderNum() == 1:
                    # WEST
                    return location.x <= location.y and location.y <= -location.x
                # NORTHWEST
                return location.x <= 0 and location.y >= 0
            if robotDirection.getDirectionOrderNum() == 3:
                # NORTH
                return -location.y <= location.x and location.x <= location.y
            # NORTHEAST
            return location.x >= 0 and location.y >= 0
        if robotDirection.getDirectionOrderNum() <= 6:
            if robotDirection.getDirectionOrderNum() == 5:
                # EAST
                return -location.x <= location.y and location.y <= location.x
            # SOUTHEAST
            return location.x >= 0 and location.y <= 0
        if robotDirection.getDirectionOrderNum() == 7:
            # SOUTH
            return location.y <= location.x and location.x <= -location.y
        # SOUTHWEST
        return location.x <= 0 and location.y <= 0

    @staticmethod
    def mapLocationAddNoise(ml, maxDist):
        ml = ml.translate(Globals.rng.nextInt() % maxDist, Globals.rng.nextInt() % maxDist)
        return Globals.closestOnMap(ml)

    @staticmethod
    def dontTurn():
        Globals.cantTurn = False

    @staticmethod
    def dontMove():
        Globals.cantMove = False

    @staticmethod
    def pickUpCheese(ml):
        if not Globals.rc.canPickUpCheese(ml):
            return
        x = Globals.rc.senseMapInfo(ml).getCheeseAmount()
        if x + Globals.rc.getRawCheese() > Globals.maxCheese:
            Globals.rc.pickUpCheese(ml, Globals.maxCheese - Globals.rc.getRawCheese())
        else:
            Globals.rc.pickUpCheese(ml)
