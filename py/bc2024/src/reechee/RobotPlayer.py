# Port of reechee/RobotPlayer.java. See py/CONVENTIONS.md.
import traceback

from api import *
import Pathfind


class RobotPlayer:
    # SHARED ARRAY INFO
    # 0 - 2: Information about team flags - contains x, y, number of booms placed

    # Settings
    numDefence = 3
    flagMove1 = 3
    flagMove2 = 5
    defensiveTrapType = TrapType.EXPLOSIVE

    # Game Variables
    roundNum = 0
    id = -1

    # Code Variables
    rng = None
    teamFlagInfo = -1
    teamFlagLocation = None
    role = -1
    # 0: Defender, 1: Attacker
    flagTargetLocation = None
    oscillationDirections = [
        Direction.NORTH,
        Direction.NORTHEAST,
        Direction.EAST,
        Direction.SOUTHEAST,
        Direction.SOUTH,
        Direction.SOUTHWEST,
        Direction.WEST,
        Direction.NORTHWEST,
    ]
    currentOscillationDirection = 0

    @staticmethod
    def run(rc):
        # Make the rng seed
        if RobotPlayer.rng is None:
            RobotPlayer.rng = Random(rc.getID())

        while True:
            try:
                rc.setIndicatorString(str(RobotPlayer.id))

                # Get global upgrades if available
                RobotPlayer.getGlobalUpgrades(rc)

                # Get info about bot
                RobotPlayer.roundNum = rc.getRoundNum()

                # Get Bot ID on round one (0 indexed)
                if RobotPlayer.roundNum == 1:
                    RobotPlayer.id = rc.readSharedArray(0)
                    rc.writeSharedArray(0, RobotPlayer.id + 1)
                    if RobotPlayer.id < RobotPlayer.numDefence:
                        RobotPlayer.role = 0
                    else:
                        RobotPlayer.role = 1
                    Clock.doYield()
                # Reset shared array after id's are set
                if RobotPlayer.roundNum == 2:
                    rc.writeSharedArray(0, 0)

                # If the bot isn't spawned
                if not rc.isSpawned():
                    if RobotPlayer.id > RobotPlayer.numDefence:
                        # Attempt to spawn the bot (arbitrarily)
                        # REMOVED FOR TESTING
                        # RobotPlayer.spawnBot(rc)
                        pass
                    else:
                        # Spawn the bot in a location with a flag without a defender
                        # Identify possible spawn locations
                        spawnLocs = rc.getAllySpawnLocations()
                        spawnLoc = None
                        # Choose an available location to spawn
                        for i in spawnLocs:
                            isTaken = False
                            for j in range(RobotPlayer.numDefence):
                                if j == RobotPlayer.id:
                                    continue
                                # Java read rc.readSharedArray(j) twice (once per
                                # /60 and %60); hoisted - same call count overall.
                                packed = rc.readSharedArray(j)
                                if abs(i.x - packed // 60) < 4 and abs(i.y - packed % 60) < 4:
                                    isTaken = True
                            if rc.canSpawn(i) and not isTaken:
                                spawnLoc = i
                        # Spawn in that location
                        if spawnLoc is not None:
                            rc.spawn(spawnLoc)

                # If the robot has been spawned
                if rc.isSpawned():
                    # If the bot is a defender
                    if RobotPlayer.role == 0:
                        # Identify nearby flag/s
                        nearbyFlags = rc.senseNearbyFlags(-1, rc.getTeam())
                        # Double check there is a flag to avoid errors
                        if len(nearbyFlags) > 0:
                            # Broadcast flag's x and y
                            if RobotPlayer.teamFlagInfo == -1:
                                RobotPlayer.teamFlagInfo = (nearbyFlags[0].getLocation().x * 60
                                                            + nearbyFlags[0].getLocation().y)
                                rc.writeSharedArray(RobotPlayer.id, RobotPlayer.teamFlagInfo)
                                RobotPlayer.teamFlagLocation = nearbyFlags[0].getLocation()

                            # In the setup phase, move the flag
                            if RobotPlayer.roundNum < 150:
                                # Find target location (2, 1, 0 tiles corner-ward
                                # depending on how far to the side it is)
                                x = 0
                                y = 0
                                sx = 0
                                sy = 0
                                spawnLocs = rc.getAllySpawnLocations()
                                for i in spawnLocs:
                                    sx += i.x
                                    sy += i.y
                                sx //= 27  # sx >= 0: Java int division
                                sy //= 27
                                if sx < rc.getMapWidth() // RobotPlayer.flagMove1:
                                    x = -1
                                if sx < rc.getMapWidth() // RobotPlayer.flagMove2:
                                    x = -2
                                if sx > rc.getMapWidth() - (rc.getMapWidth() // RobotPlayer.flagMove1):
                                    x = 1
                                if sx > rc.getMapWidth() - (rc.getMapWidth() // RobotPlayer.flagMove2):
                                    x = 2

                                if sy < rc.getMapHeight() // RobotPlayer.flagMove1:
                                    y = -1
                                if sy < rc.getMapHeight() // RobotPlayer.flagMove2:
                                    y = -2
                                if sy > rc.getMapHeight() - (rc.getMapHeight() // RobotPlayer.flagMove1):
                                    y = 1
                                if sy > rc.getMapHeight() - (rc.getMapHeight() // RobotPlayer.flagMove2):
                                    y = 2

                                RobotPlayer.flagTargetLocation = MapLocation(
                                    RobotPlayer.teamFlagLocation.x + x,
                                    RobotPlayer.teamFlagLocation.y + y)

                                rc.setIndicatorString(str(RobotPlayer.id) + ": " + str(sx) + " " + str(sy))

                                # Move the flag if it is not in the target position
                                if nearbyFlags[0].getLocation() != RobotPlayer.flagTargetLocation:
                                    if rc.canPickupFlag(nearbyFlags[0].getLocation()):
                                        rc.pickupFlag(nearbyFlags[0].getLocation())
                                    if rc.hasFlag():
                                        if rc.canDropFlag(RobotPlayer.flagTargetLocation):
                                            rc.dropFlag(RobotPlayer.flagTargetLocation)
                                        Pathfind.Pathfind.moveTowards(rc, RobotPlayer.flagTargetLocation)
                                        if rc.canDropFlag(RobotPlayer.flagTargetLocation):
                                            rc.dropFlag(RobotPlayer.flagTargetLocation)
                            # In the main phase, build traps around the spawn zone
                            else:
                                # Drop the flag if it's still holding the flag
                                if rc.hasFlag():
                                    if rc.canDropFlag(RobotPlayer.flagTargetLocation):
                                        rc.dropFlag(RobotPlayer.flagTargetLocation)
                                # Oscillate around the spawn zone
                                if rc.getLocation() == RobotPlayer.teamFlagLocation.add(
                                        RobotPlayer.oscillationDirections[RobotPlayer.currentOscillationDirection]):
                                    RobotPlayer.currentOscillationDirection += 1
                                    if RobotPlayer.currentOscillationDirection == 8:
                                        RobotPlayer.currentOscillationDirection = 0
                                Pathfind.Pathfind.moveTowardsV1(rc, RobotPlayer.teamFlagLocation.add(
                                    RobotPlayer.oscillationDirections[RobotPlayer.currentOscillationDirection]))
                                # Place traps on rounds where _  for even traps
                                if RobotPlayer.roundNum % RobotPlayer.numDefence == RobotPlayer.id:
                                    RobotPlayer.placeTrapsNearFlag(rc)

                    # If the bot is an attacker
                    if RobotPlayer.role == 1:
                        # In the setup phase, explore to gather crumbs
                        if RobotPlayer.roundNum < 150:
                            Pathfind.Pathfind.explore(rc)
                            Clock.doYield()

            except GameActionException:
                # Bad things happen
                print("GameActionException")
                traceback.print_exc()

            except Exception:
                # Bad things happen
                print("Exception")
                traceback.print_exc()

            finally:
                # End the turn
                Clock.doYield()

    @staticmethod
    def getGlobalUpgrades(rc):
        # Check for global upgrades
        if rc.canBuyGlobal(GlobalUpgrade.HEALING):
            rc.buyGlobal(GlobalUpgrade.HEALING)
        # First get HEALING and then action
        if rc.canBuyGlobal(GlobalUpgrade.ACTION):
            rc.buyGlobal(GlobalUpgrade.ACTION)

    @staticmethod
    def spawnBot(rc):
        # Identify possible spawn locations
        spawnLocs = rc.getAllySpawnLocations()
        spawnLoc = None
        # Choose an available location to spawn
        for i in spawnLocs:
            if rc.canSpawn(i):
                spawnLoc = i
        # Spawn in that location
        if spawnLoc is not None:
            rc.spawn(spawnLoc)

    @staticmethod
    def xDefense(rc):
        # Get all possible building locations
        buildLocs = rc.senseNearbyMapInfos(2)
        buildLoc = None
        distanceToFlag = 1000000
        isTrap = False  # if false, water
        # Find build location closest to flag
        for i in buildLocs:
            if abs(i.getMapLocation().x - RobotPlayer.flagTargetLocation.x) == \
                    abs(i.getMapLocation().y - RobotPlayer.flagTargetLocation.y):
                if rc.canBuild(RobotPlayer.defensiveTrapType, i.getMapLocation()):
                    if RobotPlayer.flagTargetLocation.distanceSquaredTo(i.getMapLocation()) < distanceToFlag:
                        distanceToFlag = RobotPlayer.flagTargetLocation.distanceSquaredTo(i.getMapLocation())
                        buildLoc = i.getMapLocation()
                        isTrap = True
            else:
                if rc.canDig(i.getMapLocation()):
                    if RobotPlayer.flagTargetLocation.distanceSquaredTo(i.getMapLocation()) < distanceToFlag:
                        distanceToFlag = RobotPlayer.flagTargetLocation.distanceSquaredTo(i.getMapLocation())
                        buildLoc = i.getMapLocation()
                        isTrap = False
        # If a location is found, build there
        if buildLoc is not None:
            if isTrap:
                rc.build(RobotPlayer.defensiveTrapType, buildLoc)
            else:
                rc.dig(buildLoc)

    @staticmethod
    def placeTrapsNearFlag(rc):
        # Get all possible building locations
        buildLocs = rc.senseNearbyMapInfos(2)
        buildLoc = None
        distanceToFlag = 1000000
        # Find build location closest to flag
        for i in buildLocs:
            if rc.canBuild(RobotPlayer.defensiveTrapType, i.getMapLocation()):
                if RobotPlayer.flagTargetLocation.distanceSquaredTo(i.getMapLocation()) < distanceToFlag:
                    distanceToFlag = RobotPlayer.flagTargetLocation.distanceSquaredTo(i.getMapLocation())
                    buildLoc = i.getMapLocation()
        # If a location is found, build there
        if buildLoc is not None:
            rc.build(RobotPlayer.defensiveTrapType, buildLoc)

    @staticmethod
    def healNearby(rc):
        # Relevant robots to interact with
        nearbyRobots = rc.senseNearbyRobots(-1)
        # Choose the best robots to attack
        toHeal = None
        lowestHeal = 99999
        toAttack = None
        lowestAttack = 99999
        for currRobot in nearbyRobots:
            # Checks for which team it's on
            if currRobot.team == rc.getTeam():
                # Friendly team, try to heal it
                if currRobot.health < lowestHeal and rc.canHeal(currRobot.location):
                    lowestHeal = currRobot.health
                    toHeal = currRobot.location
            else:
                # Enemy team, try attack it
                if currRobot.hasFlag and rc.canAttack(currRobot.location):
                    toAttack = currRobot.location
                    break
                if currRobot.health < lowestAttack and rc.canAttack(currRobot.location):
                    lowestAttack = currRobot.health
                    toAttack = currRobot.location
        if toHeal is not None and rc.canHeal(toHeal):
            rc.heal(toHeal)
        # Java bug preserved: checks canHeal but calls attack
        if toAttack is not None and rc.canHeal(toAttack):
            rc.attack(toAttack)

    @staticmethod
    def attackNearby(rc):
        # Relevant robots to interact with
        nearbyRobots = rc.senseNearbyRobots(-1)
        # Choose the best robots to attack
        toHeal = None
        lowestHeal = 99999
        toAttack = None
        lowestAttack = 99999
        for currRobot in nearbyRobots:
            # Checks for which team it's on
            if currRobot.team == rc.getTeam():
                # Friendly team, try to heal it
                if currRobot.health < lowestHeal and rc.canHeal(currRobot.location):
                    lowestHeal = currRobot.health
                    toHeal = currRobot.location
            else:
                # Enemy team, try attack it
                if currRobot.hasFlag and rc.canAttack(currRobot.location):
                    toAttack = currRobot.location
                    break
                if currRobot.health < lowestAttack and rc.canAttack(currRobot.location):
                    lowestAttack = currRobot.health
                    toAttack = currRobot.location
        # Java bug preserved: checks canHeal but calls attack
        if toAttack is not None and rc.canHeal(toAttack):
            rc.attack(toAttack)
        if toHeal is not None and rc.canHeal(toHeal):
            rc.heal(toHeal)
