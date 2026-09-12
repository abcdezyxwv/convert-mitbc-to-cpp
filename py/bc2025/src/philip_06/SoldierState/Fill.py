# Port of philip_06/SoldierState/Fill.java. See py/CONVENTIONS.md.
# Module-form imports for bot-internal deps (cyclic import graph) - names
# resolve at call time.
from api import *
import RobotPlayer
import Soldier
from roles import Mopper
from roles import Splasher


# java.util.Random.nextBoolean() has no equivalent on api.py's Random.
def _rngNextBoolean():
    return RobotPlayer.RobotPlayer.rng.nextInt(2) != 0


class Fill:

    class Move:

        # variables
        edge = None
        vertexA = None
        vertexB = None
        roundsExploring = 0

        stuck = False
        moveRight = False
        pastLocs = []

        # utility functions
        @staticmethod
        def init(rc):
            Fill.Move.roundsExploring = 0
            Fill.Move.moveRight = _rngNextBoolean()
            # init explore stuff
            nsEdge = False
            loc = rc.getLocation()
            maxX = rc.getMapWidth()
            maxY = rc.getMapHeight()
            # find closest edge
            if min(loc.x, maxX - loc.x) > min(loc.y, maxY - loc.y):
                nsEdge = True
            if min(loc.x, maxX - loc.x) < min(loc.y, maxY - loc.y):
                nsEdge = False
            if min(loc.x, maxX - loc.x) == min(loc.y, maxY - loc.y):
                nsEdge = _rngNextBoolean()
            if nsEdge:
                Fill.Move.edge = Direction.SOUTH if loc.y < maxY // 2 else Direction.NORTH  # maxY > 0: Java int division
            else:
                Fill.Move.edge = Direction.WEST if loc.x < maxX // 2 else Direction.EAST  # maxX > 0: Java int division
            # randomise a point
            if Fill.Move.edge == Direction.NORTH:
                Fill.Move.vertexA = MapLocation(2 + RobotPlayer.RobotPlayer.rng.nextInt(maxX - 4), maxY - 1 - RobotPlayer.RobotPlayer.rng.nextInt(6))
                Fill.Move.vertexB = MapLocation(Fill.Move.vertexA.x, 2)
            if Fill.Move.edge == Direction.SOUTH:
                Fill.Move.vertexA = MapLocation(2 + RobotPlayer.RobotPlayer.rng.nextInt(maxX - 4), RobotPlayer.RobotPlayer.rng.nextInt(6))
                Fill.Move.vertexB = MapLocation(Fill.Move.vertexA.x, maxY - 2)
            if Fill.Move.edge == Direction.EAST:
                Fill.Move.vertexA = MapLocation(maxX - 1 - RobotPlayer.RobotPlayer.rng.nextInt(6), 2 + RobotPlayer.RobotPlayer.rng.nextInt(maxY - 4))
                Fill.Move.vertexB = MapLocation(2, Fill.Move.vertexA.y)
            if Fill.Move.edge == Direction.WEST:
                Fill.Move.vertexA = MapLocation(RobotPlayer.RobotPlayer.rng.nextInt(6), 2 + RobotPlayer.RobotPlayer.rng.nextInt(maxY - 4))
                Fill.Move.vertexB = MapLocation(maxX - 2, Fill.Move.vertexA.y)

        # action functions
        @staticmethod
        def explore(rc):
            Fill.Move.roundsExploring += 1
            if Fill.Move.vertexA is None and Fill.Move.vertexB is None:
                Fill.Move.init(rc)
            if Fill.Move.vertexA is not None:
                Mopper.Mopper.moveTowardsMindlessly(rc, Fill.Move.vertexA)
                if Fill.Move.roundsExploring > 69:
                    Fill.Move.vertexA = None
                    Fill.Move.roundsExploring = 0
                elif rc.canSenseLocation(Fill.Move.vertexA) and not rc.senseMapInfo(Fill.Move.vertexA).isPassable():
                    Fill.Move.vertexA = None
                    Fill.Move.roundsExploring = 0
                elif rc.getLocation().isWithinDistanceSquared(Fill.Move.vertexA, 2):
                    Fill.Move.vertexA = None
                    Fill.Move.roundsExploring = 0
            elif Fill.Move.vertexB is not None:
                Mopper.Mopper.moveTowardsMindlessly(rc, Fill.Move.vertexB)
                if Fill.Move.roundsExploring > 69:
                    Fill.Move.vertexB = None
                    Fill.Move.roundsExploring = 0
                elif rc.canSenseLocation(Fill.Move.vertexB) and not rc.senseMapInfo(Fill.Move.vertexB).isPassable():
                    Fill.Move.vertexB = None
                    Fill.Move.roundsExploring = 0
                elif rc.getLocation().isWithinDistanceSquared(Fill.Move.vertexB, 2):
                    Fill.Move.vertexB = None
                    Fill.Move.roundsExploring = 0

    directions = [
        Direction.NORTH,
        Direction.NORTHEAST,
        Direction.EAST,
        Direction.SOUTHEAST,
        Direction.SOUTH,
        Direction.SOUTHWEST,
        Direction.WEST,
        Direction.NORTHWEST,
    ]

    marked = []
    colours = [[False] * 9 for _ in range(9)]

    @staticmethod
    def getCacheCol(rc, curr):
        return Fill.colours[rc.getLocation().x - curr.x + 4][rc.getLocation().y - curr.y + 4]

    @staticmethod
    def getCachePaint(rc, curr):
        if Fill.colours[rc.getLocation().x - curr.x + 4][rc.getLocation().y - curr.y + 4]:
            return PaintType.ALLY_SECONDARY
        return PaintType.ALLY_PRIMARY

    @staticmethod
    def isCorrect(rc, mp):
        curr = rc.senseMapInfo(mp).getPaint().isSecondary()
        return curr == Fill.getCacheCol(rc, mp)

    @staticmethod
    def attack(rc, mp):
        colour = Fill.getCacheCol(rc, mp)
        if rc.canAttack(mp):
            rc.attack(mp, colour)

    @staticmethod
    def interfere(rc, mp):
        if rc.getNumberTowers() == GameConstants.MAX_NUMBER_OF_TOWERS:
            return False
        for ruin in Soldier.Soldier.ruins:
            if rc.senseRobotAtLocation(ruin) is None:
                if ruin.isWithinDistanceSquared(mp, 8):
                    return True
        return False

    dest = None

    @staticmethod
    def run(rc):
        rc.setIndicatorString("Filler")
#         Check if it needs to be turned into an attacker
        Fill.dest = None
        # Precompute the desired colours
        Fill.marked.clear()
        Fill.colours = [[False] * 9 for _ in range(9)]
        closestNotDone = None
        for map in rc.senseNearbyMapInfos():
            if map.getMark().isAlly() and map.getMark().isSecondary():
                if rc.canSenseLocation(map.getMapLocation().add(Direction.NORTH)) and not rc.senseMapInfo(map.getMapLocation().add(Direction.NORTH)).hasRuin():
                    Fill.marked.append(map)
                if not rc.canSenseLocation(map.getMapLocation().add(Direction.NORTH)):
                    # Hope and pray :skull:
                    Fill.marked.append(map)
            '''
            if (map.getPaint() == PaintType.EMPTY && !map.hasRuin() && !map.isWall() && (dest == null || rc.getLocation().distanceSquaredTo(map.getMapLocation()) < rc.getLocation().distanceSquaredTo(dest))) {
                dest = map.getMapLocation();
                rc.setIndicatorDot(dest, 255, 0, 0);
            }
             '''
        for m in Fill.marked:
            for i in range(-2, 3):
                for j in range(-2, 3):
                    curr = MapLocation(m.getMapLocation().x + i, m.getMapLocation().y + j)
                    if rc.onTheMap(curr) and rc.canSenseLocation(curr):
                        colour = False
                        dist = curr.distanceSquaredTo(m.getMapLocation())
                        if dist == 0 or dist == 5 or dist == 8:
                            colour = True
                        Fill.colours[rc.getLocation().x - curr.x + 4][rc.getLocation().y - curr.y + 4] = colour
                        if rc.senseMapInfo(curr).getPaint() != Fill.getCachePaint(rc, curr) and not rc.senseMapInfo(curr).getPaint().isEnemy() and (closestNotDone is None or rc.getLocation().distanceSquaredTo(curr) < rc.getLocation().distanceSquaredTo(closestNotDone)):
                            closestNotDone = curr
#        See if it needs to move (cleared everything)

        #`rc.setIndicatorString(Integer.toString(rem));
        if closestNotDone is None:
            if rc.getRoundNum() < 200:
                for i in range(4):
                    if Mopper.Mopper.randomDestination is not None and Mopper.Mopper.randomDestination.distanceSquaredTo(rc.getLocation()) > Mopper.Mopper.randomDestination.distanceSquaredTo(MapLocation(rc.getMapWidth() // 2, rc.getMapHeight() // 2)):  # >= 0: Java int division
                        Mopper.Mopper.resetDest(rc)
                    else:
                        break
            if rc.senseMapInfo(rc.getLocation()).getPaint().isEnemy():
                Mopper.Mopper.findAnyAllyCell(rc)
                if Mopper.Mopper.allyCell is None:
                    Fill.Move.explore(rc)
                else:
                    Mopper.Mopper.moveTowardsMindlessly(rc, Mopper.Mopper.allyCell)
            else:
                Fill.Move.explore(rc)
            if not rc.senseMapInfo(rc.getLocation()).getPaint().isAlly() and rc.canAttack(rc.getLocation()):
                rc.attack(rc.getLocation(), True)
            for direction in Fill.directions:
                if rc.onTheMap(rc.getLocation().add(direction)) and not rc.senseMapInfo(rc.getLocation().add(direction)).getPaint().isAlly() and rc.canAttack(rc.getLocation().add(direction)):
                    rc.attack(rc.getLocation().add(direction), True)
        else:
            # Try to paint current square first (minimises paint loss)
            if rc.senseMapInfo(rc.getLocation()).getPaint().isAlly() or rc.senseMapInfo(rc.getLocation()).getPaint().isEnemy():
                for mp in rc.senseNearbyMapInfos(4):
                    hit = mp.getMapLocation()
                    if not rc.senseMapInfo(hit).getPaint().isEnemy() and (rc.senseMapInfo(hit).getPaint() != Fill.getCachePaint(rc, hit)):
                        point = rc.senseMapInfo(hit)
                        if not point.hasRuin() and not point.isWall() and rc.canAttack(hit) and not Fill.interfere(rc, hit):
                            Fill.attack(rc, hit)
                if closestNotDone is not None:
                    Mopper.Mopper.moveTowardsMindfully(rc, closestNotDone)
            else:
                Fill.attack(rc, rc.getLocation())
            Mopper.Mopper.moveTowardsMindfully(rc, closestNotDone)
        #Mopper.explore(rc);
        if not rc.senseMapInfo(rc.getLocation()).getPaint().isAlly() and rc.canAttack(rc.getLocation()):
            rc.attack(rc.getLocation(), True)
        for direction in Fill.directions:
            if rc.onTheMap(rc.getLocation().add(direction)) and not rc.senseMapInfo(rc.getLocation().add(direction)).getPaint().isAlly() and rc.canAttack(rc.getLocation().add(direction)):
                rc.attack(rc.getLocation().add(direction), True)
