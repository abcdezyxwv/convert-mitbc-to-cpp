# Port of philip_06/SoldierState/Build.java. See py/CONVENTIONS.md.
# Module-form imports for bot-internal deps (cyclic import graph) - names
# resolve at call time.
from api import *
import RobotPlayer
import Soldier
from Helper import Comms
from roles import Mopper
from roles import Splasher
from SoldierState import Attack
from SoldierState import Fill


# java.util.Random.nextBoolean() has no equivalent on api.py's Random.
def _rngNextBoolean():
    return RobotPlayer.RobotPlayer.rng.nextInt(2) != 0


class Build:
    dest = None
    destination = None
    found = False
    built = False

    lastStuck = -100
    turnsWasted = 0
    moneyLastTurn = 0
    toFinish = None
    turnAdded = None
    movingTowardsToFinish = False
    enemyPaintCell = None
    halfBuilt = None
    turnEnemyPaintCell = -100
    askForMopper = False
    wontBegForMore = None

    @staticmethod
    def run(rc):
        if rc.getNumberTowers() == 25:
            Attack.Attack.run(rc)
            return
        if (Build.halfBuilt is not None and rc.canSenseLocation(Build.halfBuilt) and rc.canSenseRobotAtLocation(Build.halfBuilt)) or (Build.halfBuilt is not None and Build.toFinish and Build.halfBuilt.x == Build.toFinish[-1].x and Build.halfBuilt.y == Build.toFinish[-1].y):
            #System.out.println("Byebye halfbuilt");
            Build.halfBuilt = None
        if Build.askForMopper:
            for bot in rc.senseNearbyRobots(-1, rc.getTeam()):
                if bot.getType() == UnitType.MOPPER:
                    Build.askForMopper = False
                    Build.enemyPaintCell = None
                    break
            if not rc.senseMapInfo(rc.getLocation()).getPaint().isAlly() and rc.canAttack(rc.getLocation()):
                rc.attack(rc.getLocation(), True)
            for direction in Fill.Fill.directions:
                if rc.onTheMap(rc.getLocation().add(direction)) and not rc.senseMapInfo(rc.getLocation().add(direction)).getPaint().isAlly() and rc.canAttack(rc.getLocation().add(direction)):
                    rc.attack(rc.getLocation().add(direction), True)
            Comms.Comms.sendMsg(rc)
            Soldier.Soldier.retreat(rc)
            rc.setIndicatorString("begging for a mopper")
            return
        if Build.turnsWasted == 3 and rc.getRoundNum() - Build.lastStuck <= 6:
            Build.halfBuilt = None
            Mopper.Mopper.explore(rc)
            if rc.senseMapInfo(rc.getLocation()).getPaint() == PaintType.EMPTY and rc.canAttack(rc.getLocation()):
                rc.attack(rc.getLocation(), _rngNextBoolean())
            for dir in Direction.allDirections():
                if rc.canSenseLocation(rc.getLocation().add(dir)) and rc.senseMapInfo(rc.getLocation().add(dir)).getPaint() == PaintType.EMPTY and rc.canAttack(rc.getLocation().add(dir)):
                    rc.attack(rc.getLocation().add(dir), _rngNextBoolean())
            rc.setIndicatorString("Exploring")
            Build.moneyLastTurn = rc.getMoney()
            return
        if Build.halfBuilt is not None:
            Build.destination = Build.halfBuilt
        rc.setIndicatorString("Building ahh")
        rc.setIndicatorDot(rc.getLocation(), 0, 255, 0)
        if rc.getNumberTowers() == GameConstants.MAX_NUMBER_OF_TOWERS:
            return
        for loc in rc.senseNearbyRuins(-1):
            if rc.canCompleteTowerPattern(UnitType.LEVEL_ONE_PAINT_TOWER, loc):
                if rc.getType() == UnitType.SOLDIER and Build.movingTowardsToFinish and Build.toFinish[-1] is loc:  # Java: == (reference identity)
                    Build.toFinish.pop()
                    Build.movingTowardsToFinish = False
                rc.completeTowerPattern(UnitType.LEVEL_ONE_PAINT_TOWER, loc)
                Build.built = True
            if rc.canCompleteTowerPattern(UnitType.LEVEL_ONE_MONEY_TOWER, loc):
                if rc.getType() == UnitType.SOLDIER and Build.movingTowardsToFinish and Build.toFinish[-1] is loc:  # Java: == (reference identity)
                    Build.toFinish.pop()
                    Build.movingTowardsToFinish = False
                rc.completeTowerPattern(UnitType.LEVEL_ONE_MONEY_TOWER, loc)
                Build.built = True
            if rc.canCompleteTowerPattern(UnitType.LEVEL_ONE_DEFENSE_TOWER, loc):
                if rc.getType() == UnitType.SOLDIER and Build.movingTowardsToFinish and Build.toFinish[-1] is loc:  # Java: == (reference identity)
                    Build.toFinish.pop()
                    Build.movingTowardsToFinish = False
                rc.completeTowerPattern(UnitType.LEVEL_ONE_DEFENSE_TOWER, loc)
                Build.built = True
        # Go to centre at the start
        while Build.turnAdded and rc.getRoundNum() - Build.turnAdded[-1] > 80 and not Build.movingTowardsToFinish:
            Build.toFinish.pop()
            Build.turnAdded.pop()
        # Check for ruins
        Build.dest = None
        # Drain nearby paint
        for ruin in rc.senseNearbyRuins(-1):
            #if (rc.senseRobotAtLocation(ruin) != null && built) rc.setIndicatorString("bruh gimme paint");
            if rc.senseRobotAtLocation(ruin) is None and rc.canSenseLocation(ruin.add(Direction.SOUTH)):
                if Build.dest is None or rc.getLocation().distanceSquaredTo(ruin) < rc.getLocation().distanceSquaredTo(Build.dest):
                    Build.dest = ruin
                    Build.found = True
            elif ruin.isAdjacentTo(rc.getLocation()) and Build.built:
                tower = rc.senseRobotAtLocation(ruin)
                if tower.getTeam() == rc.getTeam():
                    # Steal as much paint as possible
                    steal = min(200 - rc.getPaint(), tower.getPaintAmount())
                    if rc.canTransferPaint(ruin, -steal):
                        rc.transferPaint(ruin, -steal)
        if Build.dest is not None and rc.getRoundNum() < 500:
            giveUpOnRuin = False
            for dx in range(-2, 3):
                for dy in range(-2, 3):
                    if dx == 0 and dy == 0:
                        continue
                    ml = MapLocation(Build.dest.x + dx, Build.dest.y + dy)
                    if not rc.canSenseLocation(ml):
                        continue
                    if ml.x == rc.getLocation().x and ml.y == rc.getLocation().y:
                        continue
                    ri = rc.senseRobotAtLocation(ml)
                    if ri is not None and ri.getTeam() == rc.getTeam():
                        if ri.getPaintAmount() < rc.getPaint() or (ri.getPaintAmount() == rc.getPaint() and ri.ID < rc.getID()):
                            giveUpOnRuin = True
            for dx in range(-3, 4):
                for dy in range(-3, 4):
                    if dx == 0 and dy == 0:
                        continue
                    ml = MapLocation(Build.dest.x + dx, Build.dest.y + dy)
                    if not rc.canSenseLocation(ml):
                        continue
                    if ml.x == rc.getLocation().x and ml.y == rc.getLocation().y:
                        continue
                    ri = rc.senseRobotAtLocation(ml)
                    if ri is not None and ri.getTeam() != rc.getTeam():
                        giveUpOnRuin = False
            if giveUpOnRuin:
                if Build.destination is None or rc.canSenseLocation(Build.destination) or rc.getRoundNum() % 40 == 32:
                    Build.destination = MapLocation(RobotPlayer.RobotPlayer.rng.nextInt(rc.getMapWidth()), RobotPlayer.RobotPlayer.rng.nextInt(rc.getMapHeight())) if (rc.getID()) % 4 == 0 else Splasher.Splasher.getNextCorner(rc)
                Build.dest = Build.destination
        if rc.getMoney() < 400 and Build.movingTowardsToFinish:
            Build.movingTowardsToFinish = False
            if Build.destination is None or rc.canSenseLocation(Build.destination) or rc.getRoundNum() % 40 == 32:
                Build.destination = MapLocation(RobotPlayer.RobotPlayer.rng.nextInt(rc.getMapWidth()), RobotPlayer.RobotPlayer.rng.nextInt(rc.getMapHeight())) if (rc.getID()) % 4 == 0 else Splasher.Splasher.getNextCorner(rc)
            Build.dest = Build.destination
        #if (rc.getPaint() < 40 && !toFinish.isEmpty())
        #    movingTowardsToFinish = true;
        Build.built = False
        if Build.dest is None or (Build.toFinish and Build.dest.x == Build.toFinish[-1].x and Build.dest.y == Build.toFinish[-1].y and not Build.movingTowardsToFinish):
            if Build.destination is None or rc.canSenseLocation(Build.destination) or rc.getRoundNum() % 40 == 32:
                Build.destination = MapLocation(RobotPlayer.RobotPlayer.rng.nextInt(rc.getMapWidth()), RobotPlayer.RobotPlayer.rng.nextInt(rc.getMapHeight())) if (rc.getID()) % 4 == 0 else Splasher.Splasher.getNextCorner(rc)
            Build.dest = Build.destination
        if Build.movingTowardsToFinish:
            Build.dest = Build.toFinish[-1]
        if Build.movingTowardsToFinish:
            if rc.canSenseLocation(Build.dest):
                if rc.senseRobotAtLocation(Build.dest) is not None:
                    Build.toFinish.pop()
                    Build.turnAdded.pop()
                    Build.movingTowardsToFinish = False
        elif Build.toFinish:
            keepGoing = True
            dx = -2
            while dx <= 2 and keepGoing:
                dy = -2
                while dy <= 2 and keepGoing:
                    if dx == 0 and dy == 0:
                        dy += 1
                        continue
                    loc = MapLocation(Build.toFinish[-1].x + dx, Build.toFinish[-1].y + dy)
                    if rc.canSenseLocation(loc) and rc.senseMapInfo(loc).getPaint() == PaintType.EMPTY:
                        Build.dest = Build.toFinish[-1]
                        Build.toFinish.pop()
                        Build.turnAdded.pop()
                        keepGoing = False
                    dy += 1
                dx += 1
        Mopper.Mopper.moveTowardsMindfully(rc, Build.dest)
        rc.setIndicatorLine(rc.getLocation(), Build.dest, 255, 0, 0)
        if Build.movingTowardsToFinish:
            rc.setIndicatorLine(rc.getLocation(), Build.dest, 120, 120, 120)
            if rc.canSenseLocation(Build.dest):
                if rc.senseRobotAtLocation(Build.dest) is not None:
                    Build.toFinish.pop()
                    Build.turnAdded.pop()
                    Build.movingTowardsToFinish = False
        # Try to paint the current location
        marked = []
        for map in rc.senseNearbyMapInfos():
            if map.getMark().isAlly() and map.getMark().isSecondary():
                if rc.canSenseLocation(map.getMapLocation().add(Direction.NORTH)) and not rc.senseMapInfo(map.getMapLocation().add(Direction.NORTH)).hasRuin():
                    marked.append(map)
                if not rc.canSenseLocation(map.getMapLocation().add(Direction.NORTH)):
                    # Hope and pray :skull:
                    marked.append(map)
        col = False
        for map in marked:
            if rc.getLocation().isWithinDistanceSquared(map.getMapLocation(), 8):
                dist = rc.getLocation().distanceSquaredTo(map.getMapLocation())
                if dist == 0 or dist == 5 or dist == 8:
                    col = True

        if rc.senseMapInfo(rc.getLocation()).getPaint() == PaintType.EMPTY:
            colour = col
            if rc.canSenseLocation(Build.dest.add(Direction.SOUTH)) and rc.senseMapInfo(Build.dest.add(Direction.SOUTH)).getMark().isAlly():
                colour = True
                money = rc.senseMapInfo(Build.dest.add(Direction.SOUTH)).getMark().isSecondary()
                if money:
                    dist = Build.dest.distanceSquaredTo(rc.getLocation())
                    if dist == 1 or dist == 8:
                        colour = False
                else:
                    colour = False
                    dist = Build.dest.distanceSquaredTo(rc.getLocation())
                    if dist == 2 or dist == 8:
                        colour = True
            if rc.canAttack(rc.getLocation()):
                rc.attack(rc.getLocation(), colour)

        # See if it needs to change direction
        '''
        if (rc.canSenseLocation(dest) && !found) {
            if ((rc.getID())%3 == 0) dest = new MapLocation(RobotPlayer.rng.nextInt(rc.getMapWidth()), RobotPlayer.rng.nextInt(rc.getMapHeight()));
            else dest = Splasher.getNextCorner(rc);
        }
         '''

        # Try to complete tower
        if Build.found and rc.canSenseLocation(Build.dest) and rc.canSenseLocation(Build.dest.add(Direction.SOUTH)) and rc.senseMapInfo(Build.dest).hasRuin():
            if not rc.senseMapInfo(Build.dest.add(Direction.SOUTH)).getMark().isAlly():
                r = RobotPlayer.RobotPlayer.rng.nextInt(2)
                if rc.getNumberTowers() <= 4:
                    if rc.canMark(Build.dest.add(Direction.SOUTH)):
                        rc.mark(Build.dest.add(Direction.SOUTH), True)
                        Build.halfBuilt = Build.dest
                elif rc.getNumberTowers() <= 6:
                    if rc.canMark(Build.dest.add(Direction.SOUTH)):
                        rc.mark(Build.dest.add(Direction.SOUTH), False)
                        Build.halfBuilt = Build.dest
                elif r == 0 or rc.getMoney() > 5000:
                    if rc.canMark(Build.dest.add(Direction.SOUTH)):
                        rc.mark(Build.dest.add(Direction.SOUTH), False)
                        Build.halfBuilt = Build.dest
                else:
                    if rc.canMark(Build.dest.add(Direction.SOUTH)):
                        rc.mark(Build.dest.add(Direction.SOUTH), True)
                        Build.halfBuilt = Build.dest
            if rc.isActionReady() and rc.senseMapInfo(Build.dest.add(Direction.SOUTH)).getMark().isAlly():
                money = rc.senseMapInfo(Build.dest.add(Direction.SOUTH)).getMark().isSecondary()
                def_ = rc.getRoundNum() - RobotPlayer.RobotPlayer.lastSeenEnemy < 5 and rc.getRoundNum() > 2 * (rc.getMapWidth() + rc.getMapHeight())  # Java: boolean def
                rc.setIndicatorDot(Build.dest, 255, 0, 255)
                done = False
                dx = -2
                while not done and dx < 3:
                    for dy in range(-2, 3):
                        if not rc.canSenseLocation(MapLocation(Build.dest.x + dx, Build.dest.y + dy)) or (dx == 0 and dy == 0):
                            continue
                        todo = rc.senseMapInfo(MapLocation(Build.dest.x + dx, Build.dest.y + dy))
                        if todo.getPaint().isEnemy():
                            Build.enemyPaintCell = MapLocation(Build.dest.x + dx, Build.dest.y + dy)
                            Build.turnEnemyPaintCell = rc.getRoundNum()
                            continue
                        if not todo.hasRuin() and rc.canAttack(todo.getMapLocation()) and todo.getMapLocation().isWithinDistanceSquared(Build.dest, 8):
                            if not todo.hasRuin() and rc.canAttack(todo.getMapLocation()) and todo.getMapLocation().isWithinDistanceSquared(Build.dest, 8):
                                colour = True
                                if def_:
                                    colour = Build.dest.distanceSquaredTo(todo.getMapLocation()) <= 4
                                elif money:
                                    dist = Build.dest.distanceSquaredTo(todo.getMapLocation())
                                    if dist == 1 or dist == 8:
                                        colour = False
                                else:
                                    colour = False
                                    dist = Build.dest.distanceSquaredTo(todo.getMapLocation())
                                    if dist == 2 or dist == 8:
                                        colour = True
                                # Check that the pattern isn't done already
                                if todo.getPaint().isAlly() and todo.getPaint().isSecondary() == colour:
                                    continue
                                if rc.canAttack(todo.getMapLocation()):
                                    rc.attack(todo.getMapLocation(), colour)
                                    Build.turnsWasted = 0
                                    Build.halfBuilt = Build.dest
                                    #System.out.println("Hello halfBuilt "+halfBuilt);
                                    done = True
                                    break
                    dx += 1
                if Build.enemyPaintCell is not None:
                    #System.out.println(lastStuck + " " + turnsWasted);
                    if Build.lastStuck == rc.getRoundNum() - 1:
                        Build.turnsWasted += 1
                    else:
                        Build.turnsWasted = 1
                    Build.lastStuck = rc.getRoundNum()
                    if Build.turnsWasted == 3 and Build.toFinish and Build.toFinish[-1].x == Build.dest.x and Build.toFinish[-1].y == Build.dest.y:
                        Build.toFinish.pop()
                        Build.turnAdded.pop()
                        Build.movingTowardsToFinish = False
                    if Build.turnsWasted == 3:
                        print(Build.wontBegForMore)
                        for ri in rc.senseNearbyRobots(Build.dest, 8, rc.getTeam()):
                            if ri.type == UnitType.SOLDIER and (ri.getPaintAmount() < rc.getPaint() or (ri.getPaintAmount() == rc.getPaint() and ri.ID < rc.getID())):
                                Build.wontBegForMore = Build.dest
                                return
                        if Build.wontBegForMore is not Build.dest:  # Java: != (reference identity)
                            Build.askForMopper = True
                        Build.wontBegForMore = Build.dest
                elif rc.isActionReady():
                    for ri in rc.senseNearbyRobots(Build.dest, 8, rc.getTeam()):
                        if ri.type == UnitType.SOLDIER and (ri.getPaintAmount() > rc.getPaint() or (ri.getPaintAmount() == rc.getPaint() and ri.ID < rc.getID())):
                            Build.turnsWasted = 3
                            Build.lastStuck = rc.getRoundNum()
                            return
                    if not Build.toFinish or Build.toFinish[-1].x != Build.dest.x or Build.toFinish[-1].y != Build.dest.y:
                        Build.toFinish.append(Build.dest)
                        Build.turnAdded.append(rc.getRoundNum())
                else:
                    Build.turnsWasted = 0
                    Build.enemyPaintCell = None
        elif Build.toFinish:
            Build.enemyPaintCell = None
            if rc.getMoney() > Build.moneyLastTurn and (1000.0 - rc.getMoney()) / (rc.getMoney() - Soldier.Soldier.moneyLastTurn) < 1.3 * (max(abs(rc.getLocation().x - Build.toFinish[-1].x), abs(rc.getLocation().y - Build.toFinish[-1].y))):
                Build.movingTowardsToFinish = True
                rc.setIndicatorString("Moving towards finish " + str(Build.toFinish[-1]) + " now " + str((1000.0 - rc.getMoney()) / (rc.getMoney() - Soldier.Soldier.moneyLastTurn)) + " " + str(1.3 * (max(abs(rc.getLocation().x - Build.toFinish[-1].x), abs(rc.getLocation().y - Build.toFinish[-1].y)))))
