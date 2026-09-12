# Port of bestsofar/Utils/Attack.java. See py/CONVENTIONS.md.
from api import *
from Roles import Rush
from Utils.AdditionalClasses.Thrown import Thrown
from Utils.BugNavigator import BugNavigator
from Utils.Globals import Globals
from Utils.Vision import Vision

# Java: import static java.lang.Math.min -> builtin min


# api.py's UnitType is a plain int enum without the Java per-type
# `visionConeRadiusSquared` field; mirrors battlecode.common.UnitType's
# per-type constants (same table the C++ port uses in Vision::visionConeRadiusSquared).
def visionConeRadiusSquared(t):
    if t == UnitType.BABY_RAT:
        return 20
    if t == UnitType.RAT_KING:
        return 25
    if t == UnitType.CAT:
        return 17
    return 0


# api.py's RobotInfo shim lacks `carryingRobot`/`getCarryingRobot()`
# (engine-provided in Java); free helper mirrors the C++ port's shim fn.
def getCarryingRobot(r):
    return getattr(r, 'carryingRobot', None)


class Attack(Globals):
    holdingRounds = 0
    cheeseToUse = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 1, 2, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 2, 2, 0, 0,
        0, 0, 0, 0, 1, 2, 2, 2, 2, 2, 0, 0, 0, 0, 1, 2,
        2, 2, 2, 2, 2, 2, 0, 0, 1, 2, 2, 2, 2, 2, 2, 2, 2,
        2, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
        2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
        2, 2, 2, 2, 2, 2, 2, 2]

    @staticmethod
    def getSafeDirections():
        safeDirections = []
        for attempt in Direction.DIRECTION_ORDER:
            safe = True
            loc = Globals.rc.getLocation().add(attempt)
            if (not Globals.rc.canMove(attempt) and not Globals.rc.canRemoveDirt(loc)) and attempt != Direction.CENTER:
                continue
            multiple = False
            for uhoh in Globals.alliesThrown:
                if not uhoh.isSafe(loc):
                    safe = False
                    break
            if not safe:
                continue

            gangb = None

            for enemy in Globals.enemyRobots:
                dist = loc.distanceSquaredTo(enemy.location)
                if dist > 8 or enemy.getType() == UnitType.RAT_KING or getCarryingRobot(enemy) is not None:
                    continue
                if not Vision.isWithinVision(enemy.location, enemy.direction, loc, visionConeRadiusSquared(enemy.getType())):
                    continue

                if Globals.rc.canCarryRat(enemy.location):
                    if multiple:
                        safe = False
                        break
                    multiple = True
                else:
                    if dist <= 2:
                        if getCarryingRobot(enemy) is not None:  # Java: enemy.carryingRobot != null
                            if Globals.rc.isActionReady() and (Globals.rc.getHealth() > enemy.health or not Globals.isWithinVision(enemy.location, enemy.direction, loc, visionConeRadiusSquared(enemy.type))):
                                if multiple:
                                    safe = False
                                    break
                                multiple = True
                                continue
                            safe = False
                            break
                        if enemy.health <= 12:
                            if multiple:
                                safe = False
                                break
                            multiple = True
                            continue
                        if dist == 2:
                            if multiple:
                                safe = False
                                break
                            multiple = True
                        elif dist == 1:
                            left = loc.add(loc.directionTo(enemy.location).rotateLeft().rotateLeft())
                            right = loc.add(loc.directionTo(enemy.location).rotateRight().rotateRight())
                            if (Vision.hasSeenLocation(left) and not Vision.isPassableWithDig(left)) and (Vision.hasSeenLocation(right) and not Vision.isPassableWithDig(right)):
                                if multiple:
                                    safe = False
                                    break
                                multiple = True
                            else:
                                gangb = enemy
                                if multiple:
                                    safe = False
                                    break
                                multiple = True
                    else:
                        if dist != 5 and getCarryingRobot(enemy) is not None:
                            safe = False
                            break
                        if enemy.health - (12 if Globals.rc.getLocation().isAdjacentTo(enemy.location) and Globals.rc.isActionReady() else 0) > Globals.rc.getHealth():
                            safe = False
                            break
                        if multiple:
                            safe = False
                            break
                        else:
                            multiple = True

            if safe:

                #check gb

                #
                # if (gangb != null) {
                #     for (RobotInfo ally: allyRobots) {
                #         if (ally.location.distanceSquaredTo(gangb.location) <= 2 && ally.type.equals(UnitType.BABY_RAT) && gangb.location.isWithinDistanceSquared(ally.location, 20, ally.direction, ally.type.visionConeAngle)) {
                #             if (gangb.health - 12 < ally.health || !ally.location.isWithinDistanceSquared(gangb.location, 20, gangb.direction, gangb.type.visionConeAngle)) {
                #                 gangb = null;
                #                 break;
                #             }
                #         }
                #     }
                #     if (gangb != null) {
                #         for (RobotInfo ally: moreAllies) {
                #             if (ally.location.distanceSquaredTo(gangb.location) <= 2 && ally.type.equals(UnitType.BABY_RAT) && gangb.location.isWithinDistanceSquared(ally.location, 20, ally.direction, ally.type.visionConeAngle)) {
                #                 if (gangb.health - 12 < ally.health || !ally.location.isWithinDistanceSquared(gangb.location, 20, gangb.direction, gangb.type.visionConeAngle)) {
                #                     gangb = null;
                #                     break;
                #                 }
                #             }
                #         }
                #     }
                # }
                #
                #  */

                if gangb is None:
                    safeDirections.append(attempt)
                    Globals.rc.setIndicatorDot(loc, 0, 0, 0)
        return safeDirections

    @staticmethod
    def canUseTrap():
        return (Globals.rc.getRawCheese() >= 20 or (Globals.rc.getGlobalCheese() >= Globals.useTrapCheeseThreshold - Globals.rc.getRawCheese() * Globals.globalCheeseTrapSubstitute and Globals.rc.getCurrentRatCost() > 50)) and len(Globals.enemyRobots) >= 2

    enemy = None
    unknown = 0

    @staticmethod
    def blindSpot(bad):
        m = bad.getLocation()
        m1 = MapLocation(m.x-1, m.y+1)
        m2 = MapLocation(m.x, m.y+1)
        m3 = MapLocation(m.x+1, m.y+1)
        m4 = MapLocation(m.x-1, m.y)
        m5 = MapLocation(m.x+1, m.y)
        m6 = MapLocation(m.x-1, m.y-1)
        m7 = MapLocation(m.x, m.y-1)
        m8 = MapLocation(m.x+1, m.y-1)
        # Java: switch expression on bad.getDirection()
        d = bad.getDirection()
        if d == Direction.NORTH:
            return [m4, m5, m6, m7, m8]
        if d == Direction.NORTHEAST:
            return [m1, m4, m6, m7, m8]
        if d == Direction.EAST:
            return [m1, m2, m4, m6, m7]
        if d == Direction.SOUTHEAST:
            return [m1, m2, m3, m4, m6]
        if d == Direction.SOUTH:
            return [m1, m2, m3, m4, m5]
        if d == Direction.SOUTHWEST:
            return [m1, m2, m3, m5, m8]
        if d == Direction.WEST:
            return [m2, m3, m5, m7, m8]
        if d == Direction.NORTHWEST:
            return [m3, m5, m6, m7, m8]
        return []

    lastKnown = None
    lastRound = 0

    @staticmethod
    def onevone():
        if Globals.rc.getCarrying() is not None:
            Attack.gunner()
        if Attack.enemy is None or Attack.unknown > 1:
            # 1v1 the closest bot
            closest = None
            for bot in Globals.enemyRobots:
                # Java: != on MapLocation references (always true - fresh objects)
                if bot.getLocation() is not Globals.rc.getLocation():
                    if closest is None or Globals.rc.getLocation().distanceSquaredTo(closest.getLocation()) > Globals.rc.getLocation().distanceSquaredTo(bot.getLocation()):
                        closest = bot
            if closest is not None or Attack.unknown > 1:
                Attack.enemy = closest
        if Attack.enemy is None:
            return False

        # Fun part: try to 1v1 someone now
        if not Globals.rc.canSenseRobot(Attack.enemy.ID):
            # cannot sense (NOT GOOD)
            # turn towards it's last known direction
            dir = Globals.rc.getLocation().directionTo(Attack.enemy.getLocation())
            if dir != Globals.rc.getDirection():
                if Globals.rc.canTurn(dir):
                    Vision.turn(dir)
            else:
                # either turn left or right
                d = Globals.rc.getDirection()
                if Globals.rc.canTurn():
                    if Globals.rng.nextInt(2) == 0:
                        Vision.turn(d.rotateRight().rotateRight())
                    else:
                        Vision.turn(d.rotateLeft().rotateLeft())
        if not Globals.rc.canSenseRobot(Attack.enemy.ID):
            Attack.unknown += 1
            if Globals.rc.canMoveForward():
                Globals.rc.moveForward()
            if Attack.unknown >= 3:
                Attack.enemy = None
            return True
        Attack.enemy = Globals.rc.senseRobot(Attack.enemy.ID)
        enemyLoc = Attack.enemy.getLocation()

        # Try the dumb pickup sequence
        if Globals.rc.canCarryRat(enemyLoc):
            Globals.rc.carryRat(enemyLoc)
            if len(Globals.enemyRobots) == 1 and Globals.rc.canMove(Globals.rc.getDirection().opposite()):
                Globals.rc.move(Globals.rc.getDirection().opposite())
            return True

        # If we have more HP, pick it up
        if Globals.rc.getHealth() > Attack.enemy.getHealth() and Globals.rc.isActionReady() and Globals.rc.isMovementReady() and Globals.rc.getCarrying() is None:
            dir = Globals.rc.getLocation().directionTo(Attack.enemy.getLocation())
            dest = Globals.rc.getLocation().add(dir)
            # Java: dest != enemyLoc is a reference compare (always true - fresh objects)
            if dest.isAdjacentTo(enemyLoc) and Globals.rc.canMove(dir) and dest is not enemyLoc and Globals.rc.canSenseRobotAtLocation(enemyLoc):
                Globals.rc.move(dir)
                Globals.rc.carryRat(enemyLoc)
                return True

        # Try move into blind spot + pick up combo
        if Globals.rc.isMovementReady() and Globals.rc.isTurningReady() and Globals.rc.isActionReady() and Globals.rc.getCarrying() is None:
            for m in Attack.blindSpot(Attack.enemy):
                if Globals.rc.getLocation().isAdjacentTo(m):
                    # ez combo ggs
                    if not Globals.rc.canMove(Globals.rc.getLocation().directionTo(m)):
                        continue
                    Globals.rc.move(Globals.rc.getLocation().directionTo(m))
                    if not Globals.rc.canSenseRobot(Attack.enemy.ID):
                        Vision.turn(Globals.rc.getLocation().directionTo(Attack.enemy.getLocation()))
                    if Globals.rc.canSenseRobot(Attack.enemy.ID) and Globals.rc.canCarryRat(Attack.enemy.getLocation()):
                        Globals.rc.carryRat(Attack.enemy.getLocation())
                        return True

        # Move into their blind spot haha if they are strafing
        if Globals.rc.getRoundNum() - Attack.lastRound == 1 and Globals.rc.getCarrying() is None:
            # check for strafing conditions
            # Java: enemyLoc != lastKnown.getLocation() is a reference compare (always true)
            if enemyLoc is not Attack.lastKnown.getLocation() and Attack.enemy.getID() == Attack.lastKnown.getID() and Globals.rc.isMovementReady() and Globals.rc.isTurningReady():
                # direction of movement
                dir = Attack.lastKnown.getLocation().directionTo(enemyLoc)
                if dir != Attack.enemy.getDirection() and dir != Attack.lastKnown.getDirection():
                    Globals.rc.setIndicatorString("THEY STRAFED!!")
                    # they strafed ggs ez W
                    # if we face them front on we just win
                    m1 = MapLocation(enemyLoc.x, enemyLoc.y+1)
                    m2 = MapLocation(enemyLoc.x, enemyLoc.y-1)
                    m3 = MapLocation(enemyLoc.x+1, enemyLoc.y)
                    m4 = MapLocation(enemyLoc.x-1, enemyLoc.y)
                    for attempt in [m1, m2, m3, m4]:
                        if Globals.rc.getLocation().isAdjacentTo(attempt):
                            dirr = Globals.rc.getLocation().directionTo(attempt)
                            if not Globals.isWithinVision(attempt, dirr, enemyLoc, 2):
                                continue
                            if not Globals.rc.canMove(Globals.rc.getLocation().directionTo(attempt)):
                                continue
                            if dirr != Globals.rc.getDirection():
                                Vision.turn(dirr)
                            Globals.rc.move(Globals.rc.getLocation().directionTo(attempt))
                            if Globals.rc.canCarryRat(enemyLoc):
                                Globals.rc.carryRat(enemyLoc)
                            else:
                                print("did not work?!?! why did i not pick up")


        if Globals.rc.canAttack(enemyLoc):
            # check how much to attack with
            if Globals.rc.getHealth() > Attack.enemy.getHealth():
                print("WHY DID I NOT PICK UP??")
            diff = Attack.enemy.getHealth() - Globals.rc.getHealth()
            if diff <= 11:
                Globals.rc.attack(Attack.enemy.getLocation(), 2)
            elif diff == 12 or diff == 13:
                # we need a lot to come back
                Globals.rc.attack(Attack.enemy.getLocation(), 5)
            elif diff > 30 and Globals.rc.isActionReady() and Globals.rc.isMovementReady():
                # place a trap and move backwards
                if Globals.rc.canMove(Globals.rc.getDirection().opposite()):
                    Globals.rc.move(Globals.rc.getDirection().opposite())
                    Globals.rc.placeRatTrap(Globals.rc.getLocation().add(Globals.rc.getDirection()))
            else:
                Globals.rc.attack(enemyLoc)
            # NEVER BACK DOWN (strafing is nearly a guaranteed loss)
            # step back once in a while
            if Globals.rc.isMovementReady() and Globals.rng.nextInt(3) == 0 and Globals.rc.getLocation().distanceSquaredTo(enemyLoc) == 2:
                if Globals.rc.canMove(Globals.rc.getDirection().opposite()):
                    Globals.rc.move(Globals.rc.getDirection().opposite())
        # never move towards them if you need to strafe
        next = Globals.rc.getLocation().add(Globals.rc.getDirection())
        if next.distanceSquaredTo(enemyLoc) >= 2 and Globals.rc.getLocation().distanceSquaredTo(enemyLoc) > next.distanceSquaredTo(enemyLoc):
            # moves us closer
            if Globals.rc.canMoveForward():
                Globals.rc.moveForward()
        elif Globals.rc.getLocation().distanceSquaredTo(enemyLoc) >= 9 and Globals.rc.isMovementReady():
            # turn and move closer
            dir = Globals.rc.getLocation().directionTo(enemyLoc)
            if Globals.rc.canTurn():
                Vision.turn(dir)
            if Globals.rc.canMoveForward():
                Globals.rc.moveForward()

        # Turn to face the enemy
        if Globals.rc.canTurn():
            dir = Globals.rc.getLocation().directionTo(enemyLoc)
            if dir != Globals.rc.getDirection() and dir != Direction.CENTER:
                Vision.turn(dir)
        if Globals.rc.canAttack(enemyLoc):
            # check how much to attack with
            if Globals.rc.getHealth() > Attack.enemy.getHealth():
                print("WHY DID I NOT PICK UP??")
            diff = Attack.enemy.getHealth() - Globals.rc.getHealth()
            if diff <= 12:
                Globals.rc.attack(Attack.enemy.getLocation(), 2)
            elif diff == 13:
                # we need a lot to come back
                Globals.rc.attack(Attack.enemy.getLocation(), 5)
            elif diff > 30 and Globals.rc.isActionReady() and Globals.rc.isMovementReady() and Globals.rc.canMove(Globals.rc.getDirection().opposite()):
                # place a trap and move backwards
                Globals.rc.move(Globals.rc.getDirection().opposite())
                Globals.rc.placeRatTrap(Globals.rc.getLocation().add(Globals.rc.getDirection()))
            else:
                Globals.rc.attack(enemyLoc)
            # NEVER BACK DOWN (strafing is nearly a guaranteed loss)
            # step back once in a while
            if Globals.rc.isMovementReady() and Globals.rng.nextInt(3) == 0 and Globals.rc.getLocation().distanceSquaredTo(enemyLoc) == 2:
                if Globals.rc.canMove(Globals.rc.getDirection().opposite()):
                    Globals.rc.move(Globals.rc.getDirection().opposite())

        # ggs we won
        if Globals.rc.getCarrying() is not None and Globals.rc.getCarrying().ID == Attack.enemy.ID:
            Attack.enemy = None

        # Java: both branches assign lastKnown = enemy (dead if/else)
        if Attack.enemy is not None and Globals.rc.canSenseRobot(Attack.enemy.getID()):
            Attack.lastKnown = Attack.enemy
        else:
            Attack.lastKnown = Attack.enemy
        if Attack.lastKnown is not None:
            Attack.lastRound = Globals.rc.getRoundNum()

        return True

    @staticmethod
    def getInvisDirections():
        safeDirections = []
        for attempt in Direction.DIRECTION_ORDER:
            invis = True
            loc = Globals.rc.getLocation().add(attempt)
            if not Globals.rc.canMove(attempt) and not Globals.rc.canRemoveDirt(loc):
                continue
            for enemy in Globals.enemyRobots:
                if enemy.getType() == UnitType.RAT_KING or getCarryingRobot(enemy) is not None:
                    continue
                if not Vision.isWithinVision(enemy.location, enemy.direction, loc, visionConeRadiusSquared(enemy.getType())):
                    continue
                invis = False
                break
            if invis:
                safeDirections.append(attempt)
                Globals.rc.setIndicatorDot(loc, 0, 0, 0)
        return safeDirections

    @staticmethod
    def trapType(type):
        if not Globals.rc.isActionReady():
            return False
        if Globals.rc.getRawCheese() < 5:
            return False
        if Globals.rc.getGlobalCheese() - 5 < Globals.trapGlobalCheeseThreshold:
            return False

        # TS UNFINISHED /////////////////////////////////

        # find attackable robot of type
        for nearbyRobot in Globals.enemyRobots:
            if nearbyRobot.getType() == type:
                # build a trap next to them if I can: CAT
                if type == UnitType.CAT:
                    # loop through directions starting from a random one
                    st = Globals.rng.nextInt(8)
                    for i in range(8):
                        adjLoc = nearbyRobot.getLocation().add(Globals.directions[(st + i) % 8])
                        if Globals.rc.canPlaceCatTrap(adjLoc):
                            Globals.rc.placeCatTrap(adjLoc)
                            return True
                # build a trap next to them if I can: RAT
                else:
                    if Globals.rc.canPlaceRatTrap(nearbyRobot.getLocation()):
                        Globals.rc.placeRatTrap(nearbyRobot.getLocation())
                        return True
        return False

    @staticmethod
    def trapKing():
        return Attack.trapType(UnitType.RAT_KING)

    @staticmethod
    def trapBaby():
        return Attack.trapType(UnitType.BABY_RAT)

    @staticmethod
    def trapCat():
        return Attack.trapType(UnitType.CAT)

    @staticmethod
    def canPickUp(pos, enemy):
        if not Globals.rc.isActionReady():
            return False
        if Globals.rc.getCarrying() is not None:
            return False
        d = pos.distanceSquaredTo(enemy.location)
        if d > 2:
            return False
        if Globals.rc.getHealth() > enemy.health:
            return True
        d1 = enemy.location.directionTo(pos)
        d2 = enemy.direction
        return d1.dx*d2.dx+d1.dy*d2.dy <= 0

    @staticmethod
    def bestThrowingDirection():
        best = None
        bestDis = 2**31 - 1  # Java: Integer.MAX_VALUE
        for info in Globals.rc.senseNearbyRobots(-1):
            if info.type == UnitType.RAT_KING and info.getTeam() == opponent(Globals.rc.getTeam()):
                best = Globals.rc.getLocation().directionTo(info.location)
                break
            if info.getTeam() == Globals.rc.getTeam():
                continue
            dx = info.location.x-Globals.rc.getLocation().x
            dy = info.location.y-Globals.rc.getLocation().y
            if dx == 0 and bestDis > abs(dy):
                bestDis = abs(dy)
                best = Globals.rc.getLocation().directionTo(info.location)
            elif dy == 0 and bestDis > abs(dx):
                bestDis = abs(dx)
                best = Globals.rc.getLocation().directionTo(info.location)
            elif abs(dx) == abs(dy) and bestDis > abs(dx):
                bestDis = abs(dx)
                best = Globals.rc.getLocation().directionTo(info.location)
        if best is not None:
            return best
        for info in Globals.rc.senseNearbyRobots(-1, Team.NEUTRAL):
            dx = info.location.x-Globals.rc.getLocation().x
            dy = info.location.y-Globals.rc.getLocation().y
            if dx == 0 and bestDis > abs(dy):
                bestDis = abs(dy)
                best = Globals.rc.getLocation().directionTo(info.location)
            elif dy == 0 and bestDis > abs(dx):
                bestDis = abs(dx)
                best = Globals.rc.getLocation().directionTo(info.location)
            elif abs(dx) == abs(dy) and bestDis > abs(dx):
                bestDis = abs(dx)
                best = Globals.rc.getLocation().directionTo(info.location)
        if best is not None:
            return best

        return Globals.rc.getLocation().directionTo(Rush.Rush.rush)

    @staticmethod
    def newBestThrowingDirection(enemy):
        best = None
        score = 0
        for dir in Direction.allDirections():
            if dir == Direction.CENTER:
                continue
            x = Globals.rc.getLocation()
            for i in range(8):
                x = x.add(dir)
                if not Globals.rc.onTheMap(x):
                    if score <= 28-i*4:
                        score = 28-i*4
                        best = dir
                    break
                if not Globals.rc.canSenseLocation(x):
                    break
                info = Globals.rc.senseMapInfo(x)
                if not info.isPassable():
                    if info.isWall():
                        if score <= min(enemy.health, 28-i*4):
                            score = min(enemy.health, 28-i*4)
                            best = dir
                    elif info.isDirt():
                        if score <= min(enemy.health, 28-i*4):
                            score = min(enemy.health, 28-i*4)
                            best = dir
                    break
                elif Globals.rc.isLocationOccupied(x):
                    bot = Globals.rc.senseRobotAtLocation(x)
                    if bot.team == Globals.rc.getTeam() and score <= min(enemy.health, 28-i*4) - min(bot.health, 28-i*4):
                        score = min(enemy.health, 28-i*4) - min(bot.health, 28-i*4)
                        best = dir
                    elif bot.team == opponent(Globals.rc.getTeam()) and score <= min(enemy.health, 28-i*4) + min(bot.health, 28-i*4):
                        score = min(enemy.health, 28-i*4) + min(bot.health, 28-i*4)
                        best = dir
                    elif bot.team == Team.NEUTRAL and score <= enemy.health:
                        score = enemy.health
                        best = dir

        return best

    @staticmethod
    def damageToCheese(dam):
        if dam <= 10:
            return 0
        return (dam-11)*(dam-11)+1

    @staticmethod
    def catMicro():
        for cat in Globals.catRobots:
            Vision.turn(Globals.rc.getLocation().directionTo(cat.location))
            if Globals.rc.canPlaceCatTrap(cat.location.add(cat.location.directionTo(Globals.rc.getLocation()))):
                Globals.rc.placeCatTrap(cat.location.add(cat.location.directionTo(Globals.rc.getLocation())))
                if Globals.rc.canMove(cat.location.directionTo(Globals.rc.getLocation())) and cat.location.distanceSquaredTo(Globals.rc.getLocation()) <= 8:
                    Globals.rc.move(cat.location.directionTo(Globals.rc.getLocation()))
            if Globals.rc.canAttack(cat.location):
                Globals.rc.attack(cat.location)

    @staticmethod
    def scratch():
        if not Globals.rc.isActionReady():
            return False
        target = None
        for i in range(len(Globals.enemyRobots)):
            if Globals.rc.canAttack(Globals.enemyRobots[i].location) and (target is None or target.health < Globals.enemyRobots[i].health):
                target = Globals.enemyRobots[i]
        if target is None:
            return False
        if target.health <= 13:
            #TODO: ANSON CHECK THIS (TRY TO 1 SHOT THEM)
            if Globals.rc.canAttack(target.location, Attack.cheeseToUse[target.health]):
                Globals.rc.attack(target.location, Attack.cheeseToUse[target.health])
                Globals.enemyRobots = Globals.rc.senseNearbyRobots(-1, Globals.opponentTeam)
                target = None
                for info in Globals.enemyRobots:
                    if Vision.hasSeenLocation(info.location) and not Vision.canReach(info.location):
                        continue
                    elif target is None or Globals.rc.getLocation().distanceSquaredTo(info.location) < Globals.rc.getLocation().distanceSquaredTo(target.location) or (info.health < target.health and Globals.rc.getLocation().distanceSquaredTo(info.location) <= Globals.rc.getLocation().distanceSquaredTo(target.location)):
                        target = info
            else:
                Globals.rc.attack(target.location)
        elif target.health > Globals.rc.getHealth() and target.health-Globals.rc.getHealth() <= 13:
            if Globals.rc.canAttack(target.location, min(2, Attack.damageToCheese(target.health-Globals.rc.getHealth()))):
                Globals.rc.attack(target.location, min(2, Attack.damageToCheese(target.health-Globals.rc.getHealth())))
            else:
                Globals.rc.attack(target.location)
        else:
            if Globals.rc.canAttack(target.location, 2):
                Globals.rc.attack(target.location, 2)
            else:
                Globals.rc.attack(target.location)
        return True

    @staticmethod
    def steps(start, end):
        return max(abs(start.x - end.x), abs(start.y - end.y))

    # micro for traps
    @staticmethod
    def trapMicro():
        if not Attack.canUseTrap() or len(Globals.newestSqueaks) >= len(Globals.enemyRobots) + 1:
            return
        # ok we are in danger, we want to place traps
        # (don't waste traps) only place adjacent to enemy
        bestTrap = None
        score = 0
        for dir in Globals.directions:
            if Globals.rc.canPlaceRatTrap(Globals.rc.getLocation().add(dir)):
                cand = Globals.rc.getLocation().add(dir)
                sscore = 0
                for dir2 in Globals.directions:
                    if Globals.rc.canSenseRobotAtLocation(cand.add(dir2)):
                        poss = Globals.rc.senseRobotAtLocation(cand.add(dir2))
                        if poss.getTeam() == Globals.opponentTeam:
                            if poss.getHealth() > 50:
                                sscore += 3
                            else:
                                sscore += 2
                if sscore > score:
                    score = sscore
                    bestTrap = cand
        if bestTrap is not None and Globals.rc.canPlaceRatTrap(bestTrap):
            Globals.rc.placeRatTrap(bestTrap)

    @staticmethod
    def retreat():
        if Globals.rc.canCarryRat(Globals.closestEnemy.location):
            Globals.rc.carryRat(Globals.closestEnemy.location)
            Globals.enemyRobots = Globals.rc.senseNearbyRobots(-1, Globals.opponentTeam)
            Globals.closestEnemy = None
            for info in Globals.enemyRobots:
                if Vision.hasSeenLocation(info.location) and not Vision.canReach(info.location):
                    continue
                elif Globals.closestEnemy is None or Globals.rc.getLocation().distanceSquaredTo(info.location) < Globals.rc.getLocation().distanceSquaredTo(Globals.closestEnemy.location) or (info.health < Globals.closestEnemy.health and Globals.rc.getLocation().distanceSquaredTo(info.location) <= Globals.rc.getLocation().distanceSquaredTo(Globals.closestEnemy.location)):
                    Globals.closestEnemy = info
            if Globals.closestEnemy is None:
                return False
        Attack.trapMicro()
        Attack.scratch()
        minDis = 1000
        bestDir = Direction.CENTER
        for i in range(8):
            if not Globals.rc.canMove(Globals.adjacentDirections[i]):
                continue
            minD = 1000
            for enemy in Globals.enemyRobots:
                minD = min(minD, Globals.rc.getLocation().add(Globals.adjacentDirections[i]).distanceSquaredTo(enemy.location))
            if minD < minDis:
                minDis = minD
                bestDir = Globals.adjacentDirections[i]
        if bestDir != Direction.CENTER and Globals.rc.canMove(bestDir):
            Globals.rc.move(bestDir)
        Attack.scratch()
        return True

    # return true if actually attacked
    @staticmethod
    def holdLine():
        safeDirections = Attack.getSafeDirections()
        invisDirections = Attack.getInvisDirections()
        helping = None
        for ally in Globals.rc.senseNearbyRobots(-1, Globals.rc.getTeam()):
            if ally.location.distanceSquaredTo(Globals.closestEnemy.location) <= Globals.rc.getLocation().distanceSquaredTo(Globals.closestEnemy.location) or (helping is not None and ally.location.distanceSquaredTo(Globals.closestEnemy.location) <= helping.location.distanceSquaredTo(Globals.closestEnemy.location)):
                helping = ally
        #attempt kidnap
        if Globals.rc.canCarryRat(Globals.closestEnemy.location):
            Globals.rc.carryRat(Globals.closestEnemy.location)
            Globals.enemyRobots = Globals.rc.senseNearbyRobots(-1, Globals.opponentTeam)
            Globals.closestEnemy = None
            for info in Globals.enemyRobots:
                if Vision.hasSeenLocation(info.location) and not Vision.canReach(info.location):
                    continue
                elif Globals.closestEnemy is None or Globals.rc.getLocation().distanceSquaredTo(info.location) < Globals.rc.getLocation().distanceSquaredTo(Globals.closestEnemy.location) or (info.health < Globals.closestEnemy.health and Globals.rc.getLocation().distanceSquaredTo(info.location) <= Globals.rc.getLocation().distanceSquaredTo(Globals.closestEnemy.location)):
                    Globals.closestEnemy = info
            if Globals.closestEnemy is None:
                return False
        if Globals.rc.isActionReady() and Globals.rc.getCarrying() is None:
            for enemy in Globals.enemyRobots:
                if enemy.location.distanceSquaredTo(Globals.rc.getLocation()) >= 9:
                    continue
                for dir in invisDirections:
                    if Attack.canPickUp(Globals.rc.getLocation().add(dir), enemy):
                        #rc.setIndicatorDot(rc.getLocation().add(dir),255,255,255);
                        if Globals.isWithinVision(Globals.rc.getLocation().add(dir), Globals.rc.getDirection(), enemy.location, visionConeRadiusSquared(enemy.getType())):
                            pass
                        elif Globals.rc.canTurn() and Globals.isWithinVision(Globals.rc.getLocation().add(dir), dir, enemy.location, visionConeRadiusSquared(enemy.getType())):
                            Vision.turn(dir)
                        if Globals.rc.canMove(dir):
                            if dir != Direction.CENTER:
                                Globals.rc.move(dir)
                            if Globals.rc.canCarryRat(enemy.location):
                                Globals.rc.carryRat(enemy.location)
                                Globals.enemyRobots = Globals.rc.senseNearbyRobots(-1, Globals.opponentTeam)
                                Globals.closestEnemy = None
                                for info in Globals.enemyRobots:
                                    if Vision.hasSeenLocation(info.location) and not Vision.canReach(info.location):
                                        continue
                                    elif Globals.closestEnemy is None or Globals.rc.getLocation().distanceSquaredTo(info.location) < Globals.rc.getLocation().distanceSquaredTo(Globals.closestEnemy.location) or (info.health < Globals.closestEnemy.health and Globals.rc.getLocation().distanceSquaredTo(info.location) <= Globals.rc.getLocation().distanceSquaredTo(Globals.closestEnemy.location)):
                                        Globals.closestEnemy = info
                                if Globals.closestEnemy is None:
                                    return False
                            elif Attack.canPickUp(Globals.rc.getLocation(), enemy) and Globals.rc.canTurn(Globals.rc.getLocation().directionTo(enemy.location)):
                                Vision.turn(Globals.rc.getLocation().directionTo(enemy.location))
                                if Globals.rc.canCarryRat(enemy.location):
                                    Globals.rc.carryRat(enemy.location)
                                    Globals.enemyRobots = Globals.rc.senseNearbyRobots(-1, Globals.opponentTeam)
                                    Globals.closestEnemy = None
                                    for info in Globals.enemyRobots:
                                        if Vision.hasSeenLocation(info.location) and not Vision.canReach(info.location):
                                            continue
                                        elif Globals.closestEnemy is None or Globals.rc.getLocation().distanceSquaredTo(info.location) < Globals.rc.getLocation().distanceSquaredTo(Globals.closestEnemy.location) or (info.health < Globals.closestEnemy.health and Globals.rc.getLocation().distanceSquaredTo(info.location) <= Globals.rc.getLocation().distanceSquaredTo(Globals.closestEnemy.location)):
                                            Globals.closestEnemy = info
                                if Globals.closestEnemy is None:
                                    return False

        if Globals.rc.isActionReady() and Globals.rc.getCarrying() is None:
            for enemy in Globals.enemyRobots:
                if enemy.location.distanceSquaredTo(Globals.rc.getLocation()) >= 9:
                    continue
                for dir in safeDirections:
                    if Attack.canPickUp(Globals.rc.getLocation().add(dir), enemy):
                        #rc.setIndicatorDot(rc.getLocation().add(dir),255,255,255);
                        if Globals.isWithinVision(Globals.rc.getLocation().add(dir), Globals.rc.getDirection(), enemy.location, visionConeRadiusSquared(enemy.getType())):
                            pass
                        elif Globals.rc.canTurn() and Globals.isWithinVision(Globals.rc.getLocation().add(dir), dir, enemy.location, visionConeRadiusSquared(enemy.getType())):
                            Vision.turn(dir)
                        if Globals.rc.canMove(dir):
                            if dir != Direction.CENTER:
                                Globals.rc.move(dir)
                            if Globals.rc.canCarryRat(enemy.location):
                                Globals.rc.carryRat(enemy.location)
                                Globals.enemyRobots = Globals.rc.senseNearbyRobots(-1, Globals.opponentTeam)
                                Globals.closestEnemy = None
                                for info in Globals.enemyRobots:
                                    if Vision.hasSeenLocation(info.location) and not Vision.canReach(info.location):
                                        continue
                                    elif Globals.closestEnemy is None or Globals.rc.getLocation().distanceSquaredTo(info.location) < Globals.rc.getLocation().distanceSquaredTo(Globals.closestEnemy.location) or (info.health < Globals.closestEnemy.health and Globals.rc.getLocation().distanceSquaredTo(info.location) <= Globals.rc.getLocation().distanceSquaredTo(Globals.closestEnemy.location)):
                                        Globals.closestEnemy = info
                                if Globals.closestEnemy is None:
                                    return False
                            elif Attack.canPickUp(Globals.rc.getLocation(), enemy) and Globals.rc.canTurn(Globals.rc.getLocation().directionTo(enemy.location)):
                                Vision.turn(Globals.rc.getLocation().directionTo(enemy.location))
                                if Globals.rc.canCarryRat(enemy.location):
                                    Globals.rc.carryRat(enemy.location)
                                    Globals.enemyRobots = Globals.rc.senseNearbyRobots(-1, Globals.opponentTeam)
                                    Globals.closestEnemy = None
                                    for info in Globals.enemyRobots:
                                        if Vision.hasSeenLocation(info.location) and not Vision.canReach(info.location):
                                            continue
                                        elif Globals.closestEnemy is None or Globals.rc.getLocation().distanceSquaredTo(info.location) < Globals.rc.getLocation().distanceSquaredTo(Globals.closestEnemy.location) or (info.health < Globals.closestEnemy.health and Globals.rc.getLocation().distanceSquaredTo(info.location) <= Globals.rc.getLocation().distanceSquaredTo(Globals.closestEnemy.location)):
                                            Globals.closestEnemy = info
                                        if Globals.closestEnemy is None:
                                            return False

        if Globals.closestEnemy is None:
            return False
        if Globals.rc.canMove(Globals.rc.getLocation().directionTo(Globals.closestEnemy.location)):
            if Globals.rc.getLocation().directionTo(Globals.closestEnemy.location) in invisDirections:
                if Globals.rc.getLocation().add(Globals.rc.getLocation().directionTo(Globals.closestEnemy.location)).directionTo(Globals.closestEnemy.location) == Globals.rc.getLocation().directionTo(Globals.closestEnemy.location) and Globals.rc.canTurn():
                    Vision.turn(Globals.rc.getLocation().directionTo(Globals.closestEnemy.location))
                Globals.rc.move(Globals.rc.getLocation().directionTo(Globals.closestEnemy.location))
            elif Globals.rc.canMove(Globals.rc.getLocation().directionTo(Globals.closestEnemy.location).rotateLeft()) and Globals.rc.getLocation().directionTo(Globals.closestEnemy.location).rotateLeft() in invisDirections:
                if Globals.rc.getLocation().add(Globals.rc.getLocation().directionTo(Globals.closestEnemy.location).rotateLeft()).directionTo(Globals.closestEnemy.location) == Globals.rc.getLocation().directionTo(Globals.closestEnemy.location).rotateLeft() and Globals.rc.canTurn():
                    Vision.turn(Globals.rc.getLocation().directionTo(Globals.closestEnemy.location).rotateLeft())
                Globals.rc.move(Globals.rc.getLocation().directionTo(Globals.closestEnemy.location).rotateLeft())
            elif Globals.rc.canMove(Globals.rc.getLocation().directionTo(Globals.closestEnemy.location).rotateRight()) and Globals.rc.getLocation().directionTo(Globals.closestEnemy.location).rotateRight() in invisDirections:
                if Globals.rc.getLocation().add(Globals.rc.getLocation().directionTo(Globals.closestEnemy.location).rotateRight()).directionTo(Globals.closestEnemy.location) == Globals.rc.getLocation().directionTo(Globals.closestEnemy.location).rotateRight() and Globals.rc.canTurn():
                    Vision.turn(Globals.rc.getLocation().directionTo(Globals.closestEnemy.location).rotateRight())
                Globals.rc.move(Globals.rc.getLocation().directionTo(Globals.closestEnemy.location).rotateRight())
            elif Globals.rc.getLocation().directionTo(Globals.closestEnemy.location) in safeDirections and Attack.steps(Globals.rc.getLocation().add(Globals.rc.getLocation().directionTo(Globals.closestEnemy.location)), Globals.closestEnemy.location) % 2 == 0:
                if Globals.rc.getLocation().add(Globals.rc.getLocation().directionTo(Globals.closestEnemy.location)).directionTo(Globals.closestEnemy.location) == Globals.rc.getLocation().directionTo(Globals.closestEnemy.location) and Globals.rc.canTurn():
                    Vision.turn(Globals.rc.getLocation().directionTo(Globals.closestEnemy.location))
                Globals.rc.move(Globals.rc.getLocation().directionTo(Globals.closestEnemy.location))
            elif Globals.rc.canMove(Globals.rc.getLocation().directionTo(Globals.closestEnemy.location).rotateRight()) and Globals.rc.getLocation().directionTo(Globals.closestEnemy.location).rotateRight() in safeDirections and Attack.steps(Globals.rc.getLocation().add(Globals.rc.getLocation().directionTo(Globals.closestEnemy.location).rotateRight()), Globals.closestEnemy.location) % 2 == 0:
                if Globals.rc.getLocation().add(Globals.rc.getLocation().directionTo(Globals.closestEnemy.location).rotateRight()).directionTo(Globals.closestEnemy.location) == Globals.rc.getLocation().directionTo(Globals.closestEnemy.location).rotateRight() and Globals.rc.canTurn():
                    Vision.turn(Globals.rc.getLocation().directionTo(Globals.closestEnemy.location).rotateRight())
                Globals.rc.move(Globals.rc.getLocation().directionTo(Globals.closestEnemy.location).rotateRight())
            elif Globals.rc.canMove(Globals.rc.getLocation().directionTo(Globals.closestEnemy.location).rotateLeft()) and Globals.rc.getLocation().directionTo(Globals.closestEnemy.location).rotateLeft() in safeDirections and Attack.steps(Globals.rc.getLocation().add(Globals.rc.getLocation().directionTo(Globals.closestEnemy.location).rotateLeft()), Globals.closestEnemy.location) % 2 == 0:
                if Globals.rc.getLocation().add(Globals.rc.getLocation().directionTo(Globals.closestEnemy.location).rotateLeft()).directionTo(Globals.closestEnemy.location) == Globals.rc.getLocation().directionTo(Globals.closestEnemy.location).rotateLeft() and Globals.rc.canTurn():
                    Vision.turn(Globals.rc.getLocation().directionTo(Globals.closestEnemy.location).rotateLeft())
                Globals.rc.move(Globals.rc.getLocation().directionTo(Globals.closestEnemy.location).rotateLeft())
        elif Globals.rc.getLocation().distanceSquaredTo(Globals.closestEnemy.location) > 15:
            BugNavigator.moveTo(Globals.closestEnemy.location, True)

        if Attack.canUseTrap():
            Attack.trapMicro()

        if Globals.rc.isMovementReady():
            for dir in invisDirections:
                if Globals.rc.canMove(dir) and dir != Direction.CENTER and 15 >= Globals.rc.getLocation().add(dir).distanceSquaredTo(Globals.closestEnemy.location):
                    Attack.scratch()
                    Globals.rc.move(dir)
                    Attack.scratch()
                    break
        if Globals.rc.isMovementReady():
            for dir in safeDirections:
                if Globals.rc.canMove(dir):
                    if not Attack.canUseTrap():
                        Attack.scratch()
                    if dir == Direction.CENTER:
                        break
                    Globals.rc.move(dir)
                    Attack.scratch()
                    break
        if Globals.rc.isMovementReady() and Globals.rc.getHealth() < Globals.closestEnemy.health and Globals.rc.getLocation().distanceSquaredTo(Globals.closestEnemy.location) <= 8:
            if Globals.rc.canMove(Globals.closestEnemy.location.directionTo(Globals.rc.getLocation())):
                if not Attack.canUseTrap():
                    Attack.scratch()
                    if Globals.closestEnemy is None:
                        return False
                Globals.rc.move(Globals.closestEnemy.location.directionTo(Globals.rc.getLocation()))
                Attack.scratch()
            elif Globals.rc.canMove(Globals.closestEnemy.location.directionTo(Globals.rc.getLocation()).rotateLeft()):
                if not Attack.canUseTrap():
                    Attack.scratch()
                    if Globals.closestEnemy is None:
                        return False
                Globals.rc.move(Globals.closestEnemy.location.directionTo(Globals.rc.getLocation()).rotateLeft())
                Attack.scratch()
            elif Globals.rc.canMove(Globals.closestEnemy.location.directionTo(Globals.rc.getLocation()).rotateRight()):
                if not Attack.canUseTrap():
                    Attack.scratch()
                    if Globals.closestEnemy is None:
                        return False
                Globals.rc.move(Globals.closestEnemy.location.directionTo(Globals.rc.getLocation()).rotateRight())
                Attack.scratch()
                if Globals.closestEnemy is None:
                    return False
        if Globals.closestEnemy is None:
            return False
        if Globals.rc.canTurn(Globals.rc.getLocation().directionTo(Globals.closestEnemy.location)):
            Vision.turn(Globals.rc.getLocation().directionTo(Globals.closestEnemy.location))
        Attack.scratch()

        return True

    @staticmethod
    def moveIn():
        invisDirections = Attack.getInvisDirections()
        helping = None
        for ally in Globals.rc.senseNearbyRobots(-1, Globals.rc.getTeam()):
            if ally.location.distanceSquaredTo(Globals.closestEnemy.location) <= Globals.rc.getLocation().distanceSquaredTo(Globals.closestEnemy.location) or (helping is not None and ally.location.distanceSquaredTo(Globals.closestEnemy.location) <= helping.location.distanceSquaredTo(Globals.closestEnemy.location)):
                helping = ally
        #attempt kidnap
        if Globals.rc.canCarryRat(Globals.closestEnemy.location):
            Globals.rc.carryRat(Globals.closestEnemy.location)
            Globals.enemyRobots = Globals.rc.senseNearbyRobots(-1, Globals.opponentTeam)
            Globals.closestEnemy = None
            for info in Globals.enemyRobots:
                if Vision.hasSeenLocation(info.location) and not Vision.canReach(info.location):
                    continue
                elif Globals.closestEnemy is None or Globals.rc.getLocation().distanceSquaredTo(info.location) < Globals.rc.getLocation().distanceSquaredTo(Globals.closestEnemy.location) or (info.health < Globals.closestEnemy.health and Globals.rc.getLocation().distanceSquaredTo(info.location) <= Globals.rc.getLocation().distanceSquaredTo(Globals.closestEnemy.location)):
                    Globals.closestEnemy = info
            if Globals.closestEnemy is None:
                return False


        if Globals.rc.isActionReady() and Globals.rc.getCarrying() is None:
            for enemy in Globals.enemyRobots:
                if enemy.location.distanceSquaredTo(Globals.rc.getLocation()) >= 9:
                    continue
                for dir in invisDirections:
                    if Attack.canPickUp(Globals.rc.getLocation().add(dir), enemy):
                        #rc.setIndicatorDot(rc.getLocation().add(dir),255,255,255);
                        if Globals.isWithinVision(Globals.rc.getLocation().add(dir), Globals.rc.getDirection(), enemy.location, visionConeRadiusSquared(enemy.getType())):
                            pass
                        elif Globals.rc.canTurn() and Globals.isWithinVision(Globals.rc.getLocation().add(dir), dir, enemy.location, visionConeRadiusSquared(enemy.getType())):
                            Vision.turn(dir)
                        if Globals.rc.canMove(dir):
                            if dir != Direction.CENTER:
                                Globals.rc.move(dir)
                            if Globals.rc.canCarryRat(enemy.location):
                                Globals.rc.carryRat(enemy.location)
                                Globals.enemyRobots = Globals.rc.senseNearbyRobots(-1, Globals.opponentTeam)
                                Globals.closestEnemy = None
                                for info in Globals.enemyRobots:
                                    if Vision.hasSeenLocation(info.location) and not Vision.canReach(info.location):
                                        continue
                                    elif Globals.closestEnemy is None or Globals.rc.getLocation().distanceSquaredTo(info.location) < Globals.rc.getLocation().distanceSquaredTo(Globals.closestEnemy.location) or (info.health < Globals.closestEnemy.health and Globals.rc.getLocation().distanceSquaredTo(info.location) <= Globals.rc.getLocation().distanceSquaredTo(Globals.closestEnemy.location)):
                                        Globals.closestEnemy = info
                                if Globals.closestEnemy is None:
                                    return False
                            elif Attack.canPickUp(Globals.rc.getLocation(), enemy) and Globals.rc.canTurn(Globals.rc.getLocation().directionTo(enemy.location)):
                                Vision.turn(Globals.rc.getLocation().directionTo(enemy.location))
                                if Globals.rc.canCarryRat(enemy.location):
                                    Globals.rc.carryRat(enemy.location)
                                    Globals.enemyRobots = Globals.rc.senseNearbyRobots(-1, Globals.opponentTeam)
                                    Globals.closestEnemy = None
                                    for info in Globals.enemyRobots:
                                        if Vision.hasSeenLocation(info.location) and not Vision.canReach(info.location):
                                            continue
                                        elif Globals.closestEnemy is None or Globals.rc.getLocation().distanceSquaredTo(info.location) < Globals.rc.getLocation().distanceSquaredTo(Globals.closestEnemy.location) or (info.health < Globals.closestEnemy.health and Globals.rc.getLocation().distanceSquaredTo(info.location) <= Globals.rc.getLocation().distanceSquaredTo(Globals.closestEnemy.location)):
                                            Globals.closestEnemy = info
                                if Globals.closestEnemy is None:
                                    return False


        if Globals.rc.isActionReady() and Globals.rc.getCarrying() is None:
            for enemy in Globals.enemyRobots:
                if enemy.location.distanceSquaredTo(Globals.rc.getLocation()) >= 9:
                    continue
                for dir in Direction.allDirections():
                    if Attack.canPickUp(Globals.rc.getLocation().add(dir), enemy):
                        #rc.setIndicatorDot(rc.getLocation().add(dir),255,255,255);
                        if Globals.isWithinVision(Globals.rc.getLocation().add(dir), Globals.rc.getDirection(), enemy.location, visionConeRadiusSquared(enemy.getType())):
                            pass
                        elif Globals.rc.canTurn() and Globals.isWithinVision(Globals.rc.getLocation().add(dir), dir, enemy.location, visionConeRadiusSquared(enemy.getType())):
                            Vision.turn(dir)
                        if Globals.rc.canMove(dir):
                            if dir != Direction.CENTER:
                                Globals.rc.move(dir)
                            if Globals.rc.canCarryRat(enemy.location):
                                Globals.rc.carryRat(enemy.location)
                                Globals.enemyRobots = Globals.rc.senseNearbyRobots(-1, Globals.opponentTeam)
                                Globals.closestEnemy = None
                                for info in Globals.enemyRobots:
                                    if Vision.hasSeenLocation(info.location) and not Vision.canReach(info.location):
                                        continue
                                    elif Globals.closestEnemy is None or Globals.rc.getLocation().distanceSquaredTo(info.location) < Globals.rc.getLocation().distanceSquaredTo(Globals.closestEnemy.location) or (info.health < Globals.closestEnemy.health and Globals.rc.getLocation().distanceSquaredTo(info.location) <= Globals.rc.getLocation().distanceSquaredTo(Globals.closestEnemy.location)):
                                        Globals.closestEnemy = info
                                if Globals.closestEnemy is None:
                                    return False
                            elif Attack.canPickUp(Globals.rc.getLocation(), enemy) and Globals.rc.canTurn(Globals.rc.getLocation().directionTo(enemy.location)):
                                Vision.turn(Globals.rc.getLocation().directionTo(enemy.location))
                                if Globals.rc.canCarryRat(enemy.location):
                                    Globals.rc.carryRat(enemy.location)
                                    Globals.enemyRobots = Globals.rc.senseNearbyRobots(-1, Globals.opponentTeam)
                                    Globals.closestEnemy = None
                                    for info in Globals.enemyRobots:
                                        if Vision.hasSeenLocation(info.location) and not Vision.canReach(info.location):
                                            continue
                                        elif Globals.closestEnemy is None or Globals.rc.getLocation().distanceSquaredTo(info.location) < Globals.rc.getLocation().distanceSquaredTo(Globals.closestEnemy.location) or (info.health < Globals.closestEnemy.health and Globals.rc.getLocation().distanceSquaredTo(info.location) <= Globals.rc.getLocation().distanceSquaredTo(Globals.closestEnemy.location)):
                                            Globals.closestEnemy = info
                                        if Globals.closestEnemy is None:
                                            return False
        if Globals.closestEnemy is None:
            return False
        Attack.scratch()
        if Globals.rc.canMove(Globals.rc.getLocation().directionTo(Globals.closestEnemy.location)):
            if Globals.rc.getLocation().directionTo(Globals.closestEnemy.location) in invisDirections:
                if Globals.rc.getLocation().add(Globals.rc.getLocation().directionTo(Globals.closestEnemy.location)).directionTo(Globals.closestEnemy.location) == Globals.rc.getLocation().directionTo(Globals.closestEnemy.location) and Globals.rc.canTurn():
                    Vision.turn(Globals.rc.getLocation().directionTo(Globals.closestEnemy.location))
                Globals.rc.move(Globals.rc.getLocation().directionTo(Globals.closestEnemy.location))
            elif Globals.rc.canMove(Globals.rc.getLocation().directionTo(Globals.closestEnemy.location).rotateLeft()) and Globals.rc.getLocation().directionTo(Globals.closestEnemy.location).rotateLeft() in invisDirections:
                if Globals.rc.getLocation().add(Globals.rc.getLocation().directionTo(Globals.closestEnemy.location).rotateLeft()).directionTo(Globals.closestEnemy.location) == Globals.rc.getLocation().directionTo(Globals.closestEnemy.location).rotateLeft() and Globals.rc.canTurn():
                    Vision.turn(Globals.rc.getLocation().directionTo(Globals.closestEnemy.location).rotateLeft())
                Globals.rc.move(Globals.rc.getLocation().directionTo(Globals.closestEnemy.location).rotateLeft())
            elif Globals.rc.canMove(Globals.rc.getLocation().directionTo(Globals.closestEnemy.location).rotateRight()) and Globals.rc.getLocation().directionTo(Globals.closestEnemy.location).rotateRight() in invisDirections:
                if Globals.rc.getLocation().add(Globals.rc.getLocation().directionTo(Globals.closestEnemy.location).rotateRight()).directionTo(Globals.closestEnemy.location) == Globals.rc.getLocation().directionTo(Globals.closestEnemy.location).rotateRight() and Globals.rc.canTurn():
                    Vision.turn(Globals.rc.getLocation().directionTo(Globals.closestEnemy.location).rotateRight())
                Globals.rc.move(Globals.rc.getLocation().directionTo(Globals.closestEnemy.location).rotateRight())
            elif Globals.rc.canMove(Globals.rc.getLocation().directionTo(Globals.closestEnemy.location)):
                if Globals.rc.getLocation().add(Globals.rc.getLocation().directionTo(Globals.closestEnemy.location)).directionTo(Globals.closestEnemy.location) == Globals.rc.getLocation().directionTo(Globals.closestEnemy.location) and Globals.rc.canTurn():
                    Vision.turn(Globals.rc.getLocation().directionTo(Globals.closestEnemy.location))
                Globals.rc.move(Globals.rc.getLocation().directionTo(Globals.closestEnemy.location))
            elif Globals.rc.canMove(Globals.rc.getLocation().directionTo(Globals.closestEnemy.location).rotateRight()):
                if Globals.rc.getLocation().add(Globals.rc.getLocation().directionTo(Globals.closestEnemy.location).rotateRight()).directionTo(Globals.closestEnemy.location) == Globals.rc.getLocation().directionTo(Globals.closestEnemy.location).rotateRight() and Globals.rc.canTurn():
                    Vision.turn(Globals.rc.getLocation().directionTo(Globals.closestEnemy.location).rotateRight())
                Globals.rc.move(Globals.rc.getLocation().directionTo(Globals.closestEnemy.location).rotateRight())
            elif Globals.rc.canMove(Globals.rc.getLocation().directionTo(Globals.closestEnemy.location).rotateLeft()):
                if Globals.rc.getLocation().add(Globals.rc.getLocation().directionTo(Globals.closestEnemy.location).rotateLeft()).directionTo(Globals.closestEnemy.location) == Globals.rc.getLocation().directionTo(Globals.closestEnemy.location).rotateLeft() and Globals.rc.canTurn():
                    Vision.turn(Globals.rc.getLocation().directionTo(Globals.closestEnemy.location).rotateLeft())
                Globals.rc.move(Globals.rc.getLocation().directionTo(Globals.closestEnemy.location).rotateLeft())
        elif Globals.rc.getLocation().distanceSquaredTo(Globals.closestEnemy.location) > 15:
            BugNavigator.moveTo(Globals.closestEnemy.location, True)

        #if (canUseTrap()) trapMicro();
        Attack.scratch()
        if Globals.rc.isMovementReady():
            for dir in invisDirections:
                if Globals.rc.canMove(dir) and dir != Direction.CENTER and 15 >= Globals.rc.getLocation().add(dir).distanceSquaredTo(Globals.closestEnemy.location):
                    Attack.scratch()
                    Globals.rc.move(dir)
                    Attack.scratch()
                    break
        Attack.scratch()
        if Globals.rc.isMovementReady() and Globals.rc.getHealth() < Globals.closestEnemy.health and Globals.rc.getLocation().distanceSquaredTo(Globals.closestEnemy.location) <= 8:
            if Globals.rc.canMove(Globals.closestEnemy.location.directionTo(Globals.rc.getLocation())):
                if not Attack.canUseTrap():
                    Attack.scratch()
                    if Globals.closestEnemy is None:
                        return False
                Globals.rc.move(Globals.closestEnemy.location.directionTo(Globals.rc.getLocation()))
                Attack.scratch()
            elif Globals.rc.canMove(Globals.closestEnemy.location.directionTo(Globals.rc.getLocation()).rotateLeft()):
                if not Attack.canUseTrap():
                    Attack.scratch()
                    if Globals.closestEnemy is None:
                        return False
                Globals.rc.move(Globals.closestEnemy.location.directionTo(Globals.rc.getLocation()).rotateLeft())
                Attack.scratch()
            elif Globals.rc.canMove(Globals.closestEnemy.location.directionTo(Globals.rc.getLocation()).rotateRight()):
                if not Attack.canUseTrap():
                    Attack.scratch()
                    if Globals.closestEnemy is None:
                        return False
                Globals.rc.move(Globals.closestEnemy.location.directionTo(Globals.rc.getLocation()).rotateRight())
                Attack.scratch()
                if Globals.closestEnemy is None:
                    return False
        if Globals.closestEnemy is None:
            return False
        if Globals.rc.canTurn(Globals.rc.getLocation().directionTo(Globals.closestEnemy.location)):
            Vision.turn(Globals.rc.getLocation().directionTo(Globals.closestEnemy.location))
        Attack.scratch()

        return True

    @staticmethod
    def attack():
        if Globals.rc.getCarrying() is not None:
            if Globals.rc.getCarrying().getTeam() == Globals.myTeam:
                return False
            Attack.gunner()

        #if (rc.getRawCheese() >= minerReturnThreshold) return false;

        #if (enemyRobots.length == 1 && enemyRobots[0].getType() != UnitType.RAT_KING && Miner.shouldBeMiner()) return onevone();
        if Globals.closestEnemy is None:
            if len(Globals.catRobots) > 0:
                Attack.catMicro()
            return False
        if Globals.closestEnemy.health - Globals.rc.getHealth() > 13 or Globals.squeaksReadLastRound + 2 < len(Globals.enemyRobots):
            Attack.holdLine()
        elif Globals.squeaksReadLastRound >= len(Globals.enemyRobots):
            Attack.moveIn()
        else:
            Attack.holdLine()
        if Globals.rc.isActionReady():
            #
            # for (int i = 0; i < 8; i++) {
            #     if (rc.canCarryRat(rc.getLocation().add(adjacentDirections[i])) && rc.senseRobotAtLocation(rc.getLocation().add(adjacentDirections[i])).getTeam().equals(opponentTeam)) {
            #         rc.carryRat(rc.getLocation().add(adjacentDirections[i]));
            #     }
            # }
            #
            #  */
            for i in range(8):
                if Globals.rc.canAttack(Globals.rc.getLocation().add(Globals.adjacentDirections[i])) and Globals.rc.senseRobotAtLocation(Globals.rc.getLocation().add(Globals.adjacentDirections[i])).type != UnitType.CAT:
                    Globals.rc.attack(Globals.rc.getLocation().add(Globals.adjacentDirections[i]))
        return True

    @staticmethod
    def throwDamage(pos, dir, enemy):
        x = pos
        for i in range(8):
            x = x.add(dir)
            if i != 0 and not Globals.rc.onTheMap(x):
                return 46 - i * 4
            if not Globals.rc.canSenseLocation(x):
                return 0
            info = Globals.rc.senseMapInfo(x)
            if not info.isPassable():
                if i != 0 and (info.isWall() or info.isDirt()):
                    return 46 - i * 4
                return 0
            elif Globals.rc.isLocationOccupied(x):
                bot = Globals.rc.senseRobotAtLocation(x)
                if i != 0 and bot.team == Globals.rc.getTeam():
                    return min(enemy.health, 46 - i * 4) - min(bot.health, 46 - i * 4)
                elif i != 0 and bot.team == opponent(Globals.rc.getTeam()):
                    return min(enemy.health, 46 - i * 4) + min(bot.health, 46 - i * 4)
                elif i != 0 and bot.team == Team.NEUTRAL:
                    return enemy.health
                else:
                    return 0
        return 0

    @staticmethod
    def gunner():
        Attack.holdingRounds += 1
        safeDirs = Attack.getSafeDirections()
        if Globals.rc.getCarrying() is None:
            Attack.holdingRounds = 0
            return
        Globals.rc.setIndicatorString("gunner")
        if Globals.rc.canThrowRat() and Globals.closestEnemyKing is not None:
            if Globals.rc.getLocation().distanceSquaredTo(Globals.closestEnemyKing) <= 15:
                if Globals.rc.canTurn() or Globals.rc.getLocation().directionTo(Globals.closestEnemyKing) == Globals.rc.getDirection():
                    Vision.turn(Globals.rc.getLocation().directionTo(Globals.closestEnemyKing))
                    if Globals.rc.canThrowRat():
                        Globals.rc.throwRat()
        if not Globals.rc.isActionReady() and Globals.closestEnemy is not None:
            for i in range(len(safeDirs)):
                if safeDirs[i] == Direction.CENTER:
                    break
                if Globals.rc.canMove(safeDirs[i]):
                    Globals.rc.move(safeDirs[i])
                    break
            return
        Globals.rc.setIndicatorString("can shoot")

        if Globals.rc.isActionReady() and Direction.CENTER in safeDirs:
            shoot = Globals.rc.getDirection()
            loc = Globals.rc.getLocation().add(shoot)
            if Vision.hasSeenLocation(loc) and Vision.sensePassability(loc) and not Globals.rc.canSenseRobotAtLocation(loc) and Globals.rc.canSenseRobotAtLocation(loc.add(shoot)) and Globals.rc.senseRobotAtLocation(loc.add(shoot)).getTeam() == Globals.opponentTeam:
                Globals.rc.throwRat()
            elif Globals.rc.canTurn():
                shoot = shoot.rotateLeft()
                loc = Globals.rc.getLocation().add(shoot)
                if Vision.hasSeenLocation(loc) and Vision.sensePassability(loc) and not Globals.rc.canSenseRobotAtLocation(loc) and Globals.rc.canSenseRobotAtLocation(loc.add(shoot)) and Globals.rc.senseRobotAtLocation(loc.add(shoot)).getTeam() == Globals.opponentTeam:
                    Vision.turn(shoot)
                    Globals.rc.throwRat()
                else:
                    shoot = Globals.rc.getDirection().rotateRight()
                    loc = Globals.rc.getLocation().add(shoot)
                    if Vision.hasSeenLocation(loc) and Vision.sensePassability(loc) and not Globals.rc.canSenseRobotAtLocation(loc) and Globals.rc.canSenseRobotAtLocation(loc.add(shoot)) and Globals.rc.senseRobotAtLocation(loc.add(shoot)).getTeam() == Globals.opponentTeam:
                        Vision.turn(shoot)
                        Globals.rc.throwRat()



        #TODO move to frontline/ move in to throw
        if Globals.closestEnemy is not None:
            for i in range(8):
                x = Globals.closestEnemy.location.add(Globals.adjacentDirections[i]).add(Globals.adjacentDirections[i])
                if x.isAdjacentTo(Globals.rc.getLocation()) and Globals.rc.getLocation().directionTo(x) in safeDirs and (Globals.rc.canTurn(Globals.rc.getLocation().add(Globals.rc.getLocation().directionTo(x)).directionTo(Globals.closestEnemy.location)) or Globals.rc.getLocation().add(Globals.rc.getLocation().directionTo(x)).directionTo(Globals.closestEnemy.location) == Globals.rc.getDirection()):
                    dir = Globals.rc.getLocation().directionTo(x)
                    if Globals.rc.canMove(dir) or dir == Direction.CENTER:
                        if dir != Direction.CENTER:
                            Globals.rc.move(dir)
                        Vision.turn(Globals.rc.getLocation().directionTo(Globals.closestEnemy.location))
                        if Globals.rc.canThrowRat():
                            Globals.rc.throwRat()
                            Attack.holdingRounds = 0
                            return
        if not Globals.rc.isActionReady():
            return
        for j in range(8):
            x = Globals.rc.getLocation().add(Globals.adjacentDirections[j]).add(Globals.adjacentDirections[j])
            if (Vision.hasSeenLocation(x) and (Vision.isWall(x) or Vision.isDirt(x))) or (not Globals.rc.onTheMap(x) and Globals.rc.onTheMap(x.add(x.directionTo(Globals.rc.getLocation())))):
                Vision.turn(Globals.adjacentDirections[j])
                if Globals.rc.canThrowRat():
                    Globals.rc.throwRat()
                    Attack.holdingRounds = 0
                    return
        if Attack.holdingRounds == 8 or (not Globals.rc.isMovementReady() and Direction.CENTER not in safeDirs):
            #desperateThrow();
            d = Attack.newBestThrowingDirection(Globals.rc.getCarrying())
            if d is not None and Globals.rc.canTurn(d):
                Vision.turn(d)
            if Globals.rc.canThrowRat():
                Globals.rc.throwRat()
            Attack.holdingRounds = 0

    @staticmethod
    def indexOf(arr, dir):
        for i in range(len(arr)):
            if arr[i] == dir:
                return i
        return -1

    @staticmethod
    def willGetKidnapped(loc, dir, ignoreID):
        arr = [0] * 8
        for i in range(len(Globals.adjacentDirections)):
            if Globals.rc.canSenseLocation(loc.add(Globals.adjacentDirections[i])) and not Globals.rc.sensePassability(loc.add(Globals.adjacentDirections[i])):
                continue
            for j in range(len(Globals.enemyRobots)):
                if Globals.enemyRobots[j].getID() == ignoreID:
                    continue
                if Globals.enemyRobots[j].location.isAdjacentTo(loc.add(Globals.adjacentDirections[i])) or Globals.enemyRobots[j].location == loc.add(Globals.adjacentDirections[i]):
                    if arr[i] == 0:
                        arr[i] = 1
                    if Globals.enemyRobots[j].health > Globals.rc.getHealth():
                        arr[i] = 2
        if dir is not None:
            x = Attack.indexOf(Globals.adjacentDirections, dir)
            for i in range(len(arr)):
                if arr[i] >= 1 and (i - x + 8) % 8 > 1:
                    return True
                if arr[i] == 2:
                    return True
        for i in range(len(arr)):
            if arr[(i + 7) % 8] >= 1:
                for j in range(i + 1, len(arr)):
                    if arr[j] >= 1:
                        return True
                break
        return False

    @staticmethod
    def attackType(type):
        if not Globals.rc.isActionReady():
            return False

        # find attackable robot of type
        if type == UnitType.CAT:
            for nearbyRobot in Globals.catRobots:
                cat = nearbyRobot.getLocation()
                m1 = MapLocation(cat.x, cat.y)
                m2 = MapLocation(cat.x + 1, cat.y)
                m3 = MapLocation(cat.x, cat.y + 1)
                m4 = MapLocation(cat.x + 1, cat.y + 1)
                if Globals.rc.canAttack(m1):
                    Globals.rc.attack(m1)
                if Globals.rc.canAttack(m2):
                    Globals.rc.attack(m2)
                if Globals.rc.canAttack(m3):
                    Globals.rc.attack(m3)
                if Globals.rc.canAttack(m4):
                    Globals.rc.attack(m4)
        else:
            for nearbyRobot in Globals.enemyRobots:
                if nearbyRobot.getType() == type:
                    # attack if can
                    boost = 0
                    if type == UnitType.RAT_KING:
                        boost = 0
                    else:
                        if nearbyRobot.getHealth() == 11:
                            boost = 1
                        elif nearbyRobot.getHealth() == 12:
                            boost = 2
                    if Globals.rc.getRawCheese() == 0 and Globals.rc.getGlobalCheese() < Globals.safeCheeseReserve // 2:
                        boost = 0
                    for loc in Globals.getRobotLocations(nearbyRobot.getLocation(), type):
                        if Globals.rc.canAttack(loc, boost):
                            if boost > 0:
                                Globals.rc.setIndicatorDot(Globals.rc.getLocation(), 255, 255, 0)
                                print("Boosted attack!")
                            Globals.rc.attack(loc, boost)
                            return True
        return False

    @staticmethod
    def attackKing():
        return Attack.attackType(UnitType.RAT_KING)

    @staticmethod
    def attackBaby():
        return Attack.attackType(UnitType.BABY_RAT)

    @staticmethod
    def attackCat():
        return Attack.attackType(UnitType.CAT)
