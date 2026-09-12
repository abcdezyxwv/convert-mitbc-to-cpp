# Port of philip_06/roles/Mopper.java. See py/CONVENTIONS.md.
from api import *
import RobotPlayer
from Helper import Comms
from SoldierState import Fill
from roles import Splasher


class Mopper:
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
    directionsOrder = None  # Java: HashMap<Direction, Integer> directionsOrder = null

    class State(Enum):
        NICE = 0
        BULLY = 1
        CONFUSED = 2

    mood = State.NICE

    @staticmethod
    def shuffleArray(array):  # private in Java
        for i in range(len(array) - 1, 0, -1):
            index = RobotPlayer.RobotPlayer.rng.nextInt(i + 1)
            if index != i:
                temp = array[index]
                array[index] = array[i]
                array[i] = temp

    destination = None
    TurnsWasted = 0

    @staticmethod
    def canMoveMopper(rc, dir):
        return rc.canMove(dir) and rc.senseMapInfo(rc.getLocation().add(dir)).getPaint().isAlly() and (Mopper.closestEnemyTower is None or Mopper.closestEnemyTower.distanceSquaredTo(rc.getLocation().add(dir)) > 9 or Mopper.closestEnemyTower.distanceSquaredTo(rc.getLocation().add(dir)) > Mopper.closestEnemyTower.distanceSquaredTo(rc.getLocation()))

    @staticmethod
    def wander(rc):
        if not rc.isMovementReady():
            return
        if Mopper.destination is None or rc.canSenseLocation(Mopper.destination) or rc.getRoundNum() % 69 == 0 or Mopper.TurnsWasted >= 3:
            Mopper.destination = MapLocation(RobotPlayer.RobotPlayer.rng.nextInt(rc.getMapWidth()), RobotPlayer.RobotPlayer.rng.nextInt(rc.getMapHeight())) if (rc.getID()) % 4 == 0 else Splasher.Splasher.getNextCorner(rc)
            Mopper.TurnsWasted = 0
        Mopper.pastLocs.clear()
        rc.setIndicatorLine(rc.getLocation(), Mopper.destination, 255, 255, 0)
        dir = rc.getLocation().directionTo(Mopper.destination)
        if Mopper.canMoveMopper(rc, dir):
            rc.move(dir)
            return
        dir = dir.rotateLeft()
        if Mopper.canMoveMopper(rc, dir):
            rc.move(dir)
            return
        dir = dir.rotateRight()
        dir = dir.rotateRight()
        if Mopper.canMoveMopper(rc, dir):
            rc.move(dir)
            return
        Mopper.TurnsWasted += 1
        dir = dir.rotateRight()
        if Mopper.canMoveMopper(rc, dir):
            rc.move(dir)
            return
        dir = dir.opposite()
        if Mopper.canMoveMopper(rc, dir):
            rc.move(dir)
            return
        dir = dir.rotateLeft()
        if Mopper.canMoveMopper(rc, dir):
            rc.move(dir)
            return
        dir = dir.rotateLeft()
        dir = dir.rotateLeft()
        if Mopper.canMoveMopper(rc, dir):
            rc.move(dir)
            return
        dir = dir.rotateRight()
        if Mopper.canMoveMopper(rc, dir):
            rc.move(dir)
            return

    randomDestination = None

    @staticmethod
    def explore(rc):
        if not rc.isMovementReady():
            return False
        if Mopper.randomDestination is None or Mopper.randomDestination == rc.getLocation() or rc.getRoundNum() % 69 == 0:
            Mopper.randomDestination = MapLocation(RobotPlayer.RobotPlayer.rng.nextInt(rc.getMapWidth()), RobotPlayer.RobotPlayer.rng.nextInt(rc.getMapHeight())) if (rc.getID()) % 4 == 0 else Splasher.Splasher.getNextCorner(rc)
        Mopper.pastLocs.clear()
        return Mopper.moveTowardsMindfully(rc, Mopper.randomDestination)

    @staticmethod
    def resetDest(rc):
        Mopper.randomDestination = MapLocation(RobotPlayer.RobotPlayer.rng.nextInt(rc.getMapWidth()), RobotPlayer.RobotPlayer.rng.nextInt(rc.getMapHeight())) if (rc.getID()) % 4 == 0 else Splasher.Splasher.getNextCorner(rc)

    # add tower evasion
    moveRight = True
    stuck = False
    pastLocs = []

    @staticmethod
    def noBacktrack(rc, dir):
        if len(Mopper.pastLocs) == 4:
            for i in range(3):
                Mopper.pastLocs[i] = Mopper.pastLocs[i + 1]
            Mopper.pastLocs.pop()
        for loc in Mopper.pastLocs:
            if rc.getLocation().add(dir) == loc:
                return False
        return True

    @staticmethod
    def moveTowardsMindlessly(rc, loc):
        if not rc.isMovementReady():
            return False
        rc.setIndicatorLine(rc.getLocation(), loc, 255, 0, 255)
        dir = rc.getLocation().directionTo(loc)
        if rc.getRoundNum() % 120 == 0:
            Mopper.moveRight = not Mopper.moveRight
        if rc.canMove(dir) and rc.senseMapInfo(rc.getLocation().add(dir)).getPaint().isAlly() and Mopper.noBacktrack(rc, dir):
            rc.move(dir)
            Mopper.pastLocs.append(rc.getLocation())
            Mopper.stuck = False
            return True
        if Mopper.moveRight:
            dir = dir.rotateRight()
        else:
            dir = dir.rotateLeft()
        if rc.canMove(dir) and rc.senseMapInfo(rc.getLocation().add(dir)).getPaint().isAlly() and Mopper.noBacktrack(rc, dir):
            rc.move(dir)
            Mopper.pastLocs.append(rc.getLocation())
            Mopper.stuck = False
            return True
        if Mopper.moveRight:
            dir = dir.rotateLeft()
        else:
            dir = dir.rotateRight()
        if Mopper.moveRight:
            dir = dir.rotateLeft()
        else:
            dir = dir.rotateRight()
        if not Mopper.stuck:
            if rc.canMove(dir) and rc.senseMapInfo(rc.getLocation().add(dir)).getPaint().isAlly() and Mopper.noBacktrack(rc, dir):
                rc.move(dir)
                Mopper.pastLocs.append(rc.getLocation())
                return True
        if Mopper.moveRight:
            dir = dir.rotateRight()
        else:
            dir = dir.rotateLeft()
        if rc.canMove(dir) and not rc.senseMapInfo(rc.getLocation().add(dir)).getPaint().isEnemy() and Mopper.noBacktrack(rc, dir):
            rc.move(dir)
            Mopper.pastLocs.append(rc.getLocation())
            Mopper.stuck = False
            return True
        if Mopper.moveRight:
            dir = dir.rotateRight()
        else:
            dir = dir.rotateLeft()
        if rc.canMove(dir) and not rc.senseMapInfo(rc.getLocation().add(dir)).getPaint().isEnemy() and Mopper.noBacktrack(rc, dir):
            rc.move(dir)
            Mopper.pastLocs.append(rc.getLocation())
            Mopper.stuck = False
            return True
        if Mopper.moveRight:
            dir = dir.rotateLeft()
        else:
            dir = dir.rotateRight()
        if Mopper.moveRight:
            dir = dir.rotateLeft()
        else:
            dir = dir.rotateRight()
        if not Mopper.stuck:
            if rc.canMove(dir) and not rc.senseMapInfo(rc.getLocation().add(dir)).getPaint().isEnemy() and Mopper.noBacktrack(rc, dir):
                rc.move(dir)
                Mopper.pastLocs.append(rc.getLocation())
                return True
        if Mopper.moveRight:
            dir = dir.rotateRight()
        else:
            dir = dir.rotateLeft()
        if rc.canMove(dir) and Mopper.noBacktrack(rc, dir):
            rc.move(dir)
            Mopper.pastLocs.append(rc.getLocation())
            Mopper.stuck = False
            return True
        if Mopper.moveRight:
            dir = dir.rotateRight()
        else:
            dir = dir.rotateLeft()
        if rc.canMove(dir) and Mopper.noBacktrack(rc, dir):
            rc.move(dir)
            Mopper.pastLocs.append(rc.getLocation())
            Mopper.stuck = False
            return True
        if Mopper.moveRight:
            dir = dir.rotateLeft()
        else:
            dir = dir.rotateRight()
        if Mopper.moveRight:
            dir = dir.rotateLeft()
        else:
            dir = dir.rotateRight()
        if not Mopper.stuck:
            if rc.canMove(dir) and Mopper.noBacktrack(rc, dir):
                rc.move(dir)
                Mopper.pastLocs.append(rc.getLocation())
                return True
        if Mopper.moveRight:
            dir = dir.rotateRight()
        else:
            dir = dir.rotateLeft()
        Mopper.stuck = True
        rc.setIndicatorString("Stuck" + ("Right" if Mopper.moveRight else "Left"))
        if Mopper.moveRight:
            dir = dir.rotateRight()
            dir = dir.rotateRight()
            if rc.canMove(dir) and Mopper.noBacktrack(rc, dir):
                rc.move(dir)
                Mopper.pastLocs.append(rc.getLocation())
                return False
            dir = dir.rotateRight()
            if rc.canMove(dir) and Mopper.noBacktrack(rc, dir):
                rc.move(dir)
                Mopper.pastLocs.append(rc.getLocation())
                return False
            dir = dir.rotateRight()
            if rc.canMove(dir) and Mopper.noBacktrack(rc, dir):
                rc.move(dir)
                Mopper.pastLocs.append(rc.getLocation())
                return False
            dir = dir.rotateRight()
            if rc.canMove(dir) and Mopper.noBacktrack(rc, dir):
                rc.move(dir)
                Mopper.pastLocs.append(rc.getLocation())
                return False
            dir = dir.rotateRight()
            if rc.canMove(dir) and Mopper.noBacktrack(rc, dir):
                rc.move(dir)
                Mopper.pastLocs.append(rc.getLocation())
                return False
            dir = dir.rotateRight()
            if rc.canMove(dir) and Mopper.noBacktrack(rc, dir):
                rc.move(dir)
                Mopper.pastLocs.append(rc.getLocation())
                return False
            dir = dir.rotateRight()
            if rc.canMove(dir):
                rc.move(dir)
                Mopper.pastLocs.append(rc.getLocation())
                return False
            dir = dir.rotateRight()
            if rc.canMove(dir):
                rc.move(dir)
                Mopper.pastLocs.append(rc.getLocation())
                return False
            dir = dir.rotateRight()
            if rc.canMove(dir):
                rc.move(dir)
                Mopper.pastLocs.append(rc.getLocation())
                return False
            dir = dir.rotateRight()
            if rc.canMove(dir):
                rc.move(dir)
                Mopper.pastLocs.append(rc.getLocation())
                return False
            dir = dir.rotateRight()
            if rc.canMove(dir):
                rc.move(dir)
                Mopper.pastLocs.append(rc.getLocation())
                return False
            dir = dir.rotateRight()
            if rc.canMove(dir):
                rc.move(dir)
                Mopper.pastLocs.append(rc.getLocation())
                return False
            dir = dir.rotateRight()
            if rc.canMove(dir):
                rc.move(dir)
                Mopper.pastLocs.append(rc.getLocation())
                return False
            dir = dir.rotateRight()
            if rc.canMove(dir):
                rc.move(dir)
                Mopper.pastLocs.append(rc.getLocation())
                return False
        else:
            dir = dir.rotateLeft()
            dir = dir.rotateLeft()
            if rc.canMove(dir) and Mopper.noBacktrack(rc, dir):
                rc.move(dir)
                Mopper.pastLocs.append(rc.getLocation())
                return False
            dir = dir.rotateLeft()
            if rc.canMove(dir) and Mopper.noBacktrack(rc, dir):
                rc.move(dir)
                Mopper.pastLocs.append(rc.getLocation())
                return False
            dir = dir.rotateLeft()
            if rc.canMove(dir) and Mopper.noBacktrack(rc, dir):
                rc.move(dir)
                Mopper.pastLocs.append(rc.getLocation())
                return False
            dir = dir.rotateLeft()
            if rc.canMove(dir) and Mopper.noBacktrack(rc, dir):
                rc.move(dir)
                Mopper.pastLocs.append(rc.getLocation())
                return False
            dir = dir.rotateLeft()
            if rc.canMove(dir) and Mopper.noBacktrack(rc, dir):
                rc.move(dir)
                Mopper.pastLocs.append(rc.getLocation())
                return False
            dir = dir.rotateLeft()
            if rc.canMove(dir) and Mopper.noBacktrack(rc, dir):
                rc.move(dir)
                Mopper.pastLocs.append(rc.getLocation())
                return False
            dir = dir.rotateLeft()
            if rc.canMove(dir):
                rc.move(dir)
                Mopper.pastLocs.append(rc.getLocation())
                return False
            dir = dir.rotateLeft()
            if rc.canMove(dir):
                rc.move(dir)
                Mopper.pastLocs.append(rc.getLocation())
                return False
            dir = dir.rotateLeft()
            if rc.canMove(dir):
                rc.move(dir)
                Mopper.pastLocs.append(rc.getLocation())
                return False
            dir = dir.rotateLeft()
            if rc.canMove(dir):
                rc.move(dir)
                Mopper.pastLocs.append(rc.getLocation())
                return False
            dir = dir.rotateLeft()
            if rc.canMove(dir):
                rc.move(dir)
                Mopper.pastLocs.append(rc.getLocation())
                return False
            dir = dir.rotateLeft()
            if rc.canMove(dir):
                rc.move(dir)
                Mopper.pastLocs.append(rc.getLocation())
                return False
            dir = dir.rotateLeft()
            if rc.canMove(dir):
                rc.move(dir)
                Mopper.pastLocs.append(rc.getLocation())
                return False
            dir = dir.rotateLeft()
            if rc.canMove(dir):
                rc.move(dir)
                Mopper.pastLocs.append(rc.getLocation())
                return False
        return False

    lastRefresh = -1
    social = [False] * 8

    @staticmethod
    def refresh(rc):
        print(Clock.getBytecodeNum())
        if Mopper.directionsOrder is None:
            Mopper.directionsOrder = {}
            for i in range(8):
                Mopper.directionsOrder[Mopper.directions[i]] = i
        hasBad = [[False] * 5 for _ in range(5)]
        for i in range(-2, 3):
            for j in range(-2, 3):
                if i == 0 and j == 0:
                    continue
                loc = MapLocation(rc.getLocation().x + i, rc.getLocation().y + j)
                if rc.canSenseLocation(loc) and rc.senseRobotAtLocation(loc) is not None and rc.senseRobotAtLocation(loc).getTeam() == rc.getTeam():
                    hasBad[i + 2][j + 2] = True
        for dir in Mopper.directions:
            Mopper.social[Mopper.directionsOrder[dir]] = False
            a = rc.getLocation().add(dir).x
            b = rc.getLocation().add(dir).y
            #
            # for dx in range(-1, 2):
            #     for dy in range(-1, 2):
            #         if hasBad[2 + rc.getLocation().x - (a + dx)][2 + rc.getLocation().y - (b + dy)]:
            #             Mopper.social[Mopper.directionsOrder[dir]] = True
            #
        print(Clock.getBytecodeNum())
        Mopper.lastRefresh = rc.getRoundNum()

    # Java has BOTH a method `RobotInfo closestEnemyTower(RobotController)` and a
    # field `MapLocation closestEnemyTower` - legal in Java, not in Python. The
    # METHOD is renamed to closestEnemyTowerInfo; the FIELD keeps the name.
    @staticmethod
    def closestEnemyTowerInfo(rc):
        ans = None
        for loc in rc.senseNearbyRuins(-1):
            info = rc.senseRobotAtLocation(loc)
            if info is None or info.getTeam() == rc.getTeam():
                continue
            if ans is None or info.location.distanceSquaredTo(rc.getLocation()) < ans.location.distanceSquaredTo(rc.getLocation()):
                ans = info
        return ans

    @staticmethod
    def moveTowardsMindfully(rc, loc):
        if not rc.isMovementReady():
            return False
        tower = Mopper.closestEnemyTowerInfo(rc)
        rc.setIndicatorLine(rc.getLocation(), loc, 255, 255, 255)
        dir = rc.getLocation().directionTo(loc)
        if rc.getRoundNum() % 120 == 0:
            Mopper.moveRight = not Mopper.moveRight
        if rc.canMove(dir) and rc.senseMapInfo(rc.getLocation().add(dir)).getPaint().isAlly() and Mopper.noBacktrack(rc, dir) and (tower is None or tower.location.distanceSquaredTo(rc.getLocation().add(dir)) > 9):
            rc.move(dir)
            Mopper.pastLocs.append(rc.getLocation())
            Mopper.stuck = False
            return True
        if Mopper.moveRight:
            dir = dir.rotateRight()
        else:
            dir = dir.rotateLeft()
        if rc.canMove(dir) and rc.senseMapInfo(rc.getLocation().add(dir)).getPaint().isAlly() and Mopper.noBacktrack(rc, dir) and (tower is None or tower.location.distanceSquaredTo(rc.getLocation().add(dir)) > 9):
            rc.move(dir)
            Mopper.pastLocs.append(rc.getLocation())
            Mopper.stuck = False
            return True
        if Mopper.moveRight:
            dir = dir.rotateLeft()
        else:
            dir = dir.rotateRight()
        if Mopper.moveRight:
            dir = dir.rotateLeft()
        else:
            dir = dir.rotateRight()
        if not Mopper.stuck:
            # print(rc.canMove(dir))
            if rc.canMove(dir) and rc.senseMapInfo(rc.getLocation().add(dir)).getPaint().isAlly() and Mopper.noBacktrack(rc, dir) and (tower is None or tower.location.distanceSquaredTo(rc.getLocation().add(dir)) > 9):
                # print(rc.canMove(dir))
                rc.move(dir)
                Mopper.pastLocs.append(rc.getLocation())
                return True
        if Mopper.moveRight:
            dir = dir.rotateRight()
        else:
            dir = dir.rotateLeft()
        if rc.canMove(dir) and not rc.senseMapInfo(rc.getLocation().add(dir)).getPaint().isEnemy() and Mopper.noBacktrack(rc, dir) and (tower is None or tower.location.distanceSquaredTo(rc.getLocation().add(dir)) > 9):
            rc.move(dir)
            Mopper.pastLocs.append(rc.getLocation())
            Mopper.stuck = False
            return True
        if Mopper.moveRight:
            dir = dir.rotateRight()
        else:
            dir = dir.rotateLeft()
        if rc.canMove(dir) and not rc.senseMapInfo(rc.getLocation().add(dir)).getPaint().isEnemy() and Mopper.noBacktrack(rc, dir) and (tower is None or tower.location.distanceSquaredTo(rc.getLocation().add(dir)) > 9):
            rc.move(dir)
            Mopper.pastLocs.append(rc.getLocation())
            Mopper.stuck = False
            return True
        if Mopper.moveRight:
            dir = dir.rotateLeft()
        else:
            dir = dir.rotateRight()
        if Mopper.moveRight:
            dir = dir.rotateLeft()
        else:
            dir = dir.rotateRight()
        if not Mopper.stuck:
            if rc.canMove(dir) and not rc.senseMapInfo(rc.getLocation().add(dir)).getPaint().isEnemy() and Mopper.noBacktrack(rc, dir) and (tower is None or tower.location.distanceSquaredTo(rc.getLocation().add(dir)) > 9):
                rc.move(dir)
                Mopper.pastLocs.append(rc.getLocation())
                return True
        if Mopper.moveRight:
            dir = dir.rotateRight()
        else:
            dir = dir.rotateLeft()
        if rc.canMove(dir) and Mopper.noBacktrack(rc, dir) and (tower is None or tower.location.distanceSquaredTo(rc.getLocation().add(dir)) > 9):
            rc.move(dir)
            Mopper.pastLocs.append(rc.getLocation())
            Mopper.stuck = False
            return True
        if Mopper.moveRight:
            dir = dir.rotateRight()
        else:
            dir = dir.rotateLeft()
        if rc.canMove(dir) and Mopper.noBacktrack(rc, dir) and (tower is None or tower.location.distanceSquaredTo(rc.getLocation().add(dir)) > 9):
            rc.move(dir)
            Mopper.pastLocs.append(rc.getLocation())
            Mopper.stuck = False
            return True
        if Mopper.moveRight:
            dir = dir.rotateLeft()
        else:
            dir = dir.rotateRight()
        if Mopper.moveRight:
            dir = dir.rotateLeft()
        else:
            dir = dir.rotateRight()
        if not Mopper.stuck:
            if rc.canMove(dir) and Mopper.noBacktrack(rc, dir) and (tower is None or tower.location.distanceSquaredTo(rc.getLocation().add(dir)) > 9):
                rc.move(dir)
                Mopper.pastLocs.append(rc.getLocation())
                return True
        if Mopper.moveRight:
            dir = dir.rotateRight()
        else:
            dir = dir.rotateLeft()
        # UWU
        if rc.canMove(dir) and rc.senseMapInfo(rc.getLocation().add(dir)).getPaint().isAlly() and Mopper.noBacktrack(rc, dir):
            rc.move(dir)
            Mopper.pastLocs.append(rc.getLocation())
            Mopper.stuck = False
            return True
        if Mopper.moveRight:
            dir = dir.rotateRight()
        else:
            dir = dir.rotateLeft()
        if rc.canMove(dir) and rc.senseMapInfo(rc.getLocation().add(dir)).getPaint().isAlly() and Mopper.noBacktrack(rc, dir):
            rc.move(dir)
            Mopper.pastLocs.append(rc.getLocation())
            Mopper.stuck = False
            return True
        if Mopper.moveRight:
            dir = dir.rotateLeft()
        else:
            dir = dir.rotateRight()
        if Mopper.moveRight:
            dir = dir.rotateLeft()
        else:
            dir = dir.rotateRight()
        if not Mopper.stuck:
            if rc.canMove(dir) and rc.senseMapInfo(rc.getLocation().add(dir)).getPaint().isAlly() and Mopper.noBacktrack(rc, dir):
                rc.move(dir)
                Mopper.pastLocs.append(rc.getLocation())
                return True
        if Mopper.moveRight:
            dir = dir.rotateRight()
        else:
            dir = dir.rotateLeft()
        # UWU UWU
        if rc.canMove(dir) and not rc.senseMapInfo(rc.getLocation().add(dir)).getPaint().isEnemy() and Mopper.noBacktrack(rc, dir):
            rc.move(dir)
            Mopper.pastLocs.append(rc.getLocation())
            Mopper.stuck = False
            return True
        if Mopper.moveRight:
            dir = dir.rotateRight()
        else:
            dir = dir.rotateLeft()
        if rc.canMove(dir) and not rc.senseMapInfo(rc.getLocation().add(dir)).getPaint().isEnemy() and Mopper.noBacktrack(rc, dir):
            rc.move(dir)
            Mopper.pastLocs.append(rc.getLocation())
            Mopper.stuck = False
            return True
        if Mopper.moveRight:
            dir = dir.rotateLeft()
        else:
            dir = dir.rotateRight()
        if Mopper.moveRight:
            dir = dir.rotateLeft()
        else:
            dir = dir.rotateRight()
        if not Mopper.stuck:
            if rc.canMove(dir) and not rc.senseMapInfo(rc.getLocation().add(dir)).getPaint().isEnemy() and Mopper.noBacktrack(rc, dir):
                rc.move(dir)
                Mopper.pastLocs.append(rc.getLocation())
                return True
        if Mopper.moveRight:
            dir = dir.rotateRight()
        else:
            dir = dir.rotateLeft()
        # UWU UWU UWU
        rc.setIndicatorDot(rc.getLocation(), 120, 120, 120)
        if rc.canMove(dir) and rc.senseMapInfo(rc.getLocation().add(dir)).getPaint().isAlly() and Mopper.noBacktrack(rc, dir):
            rc.move(dir)
            Mopper.pastLocs.append(rc.getLocation())
            Mopper.stuck = False
            return True
        if Mopper.moveRight:
            dir = dir.rotateRight()
        else:
            dir = dir.rotateLeft()
        if rc.canMove(dir) and rc.senseMapInfo(rc.getLocation().add(dir)).getPaint().isAlly() and Mopper.noBacktrack(rc, dir):
            rc.move(dir)
            Mopper.pastLocs.append(rc.getLocation())
            Mopper.stuck = False
            return True
        if Mopper.moveRight:
            dir = dir.rotateLeft()
        else:
            dir = dir.rotateRight()
        if Mopper.moveRight:
            dir = dir.rotateLeft()
        else:
            dir = dir.rotateRight()
        if not Mopper.stuck:
            if rc.canMove(dir) and rc.senseMapInfo(rc.getLocation().add(dir)).getPaint().isAlly() and Mopper.noBacktrack(rc, dir):
                rc.move(dir)
                Mopper.pastLocs.append(rc.getLocation())
                return True
        if Mopper.moveRight:
            dir = dir.rotateRight()
        else:
            dir = dir.rotateLeft()
        if rc.canMove(dir) and not rc.senseMapInfo(rc.getLocation().add(dir)).getPaint().isEnemy() and Mopper.noBacktrack(rc, dir):
            rc.move(dir)
            Mopper.pastLocs.append(rc.getLocation())
            Mopper.stuck = False
            return True
        if Mopper.moveRight:
            dir = dir.rotateRight()
        else:
            dir = dir.rotateLeft()
        if rc.canMove(dir) and not rc.senseMapInfo(rc.getLocation().add(dir)).getPaint().isEnemy() and Mopper.noBacktrack(rc, dir):
            rc.move(dir)
            Mopper.pastLocs.append(rc.getLocation())
            Mopper.stuck = False
            return True
        if Mopper.moveRight:
            dir = dir.rotateLeft()
        else:
            dir = dir.rotateRight()
        if Mopper.moveRight:
            dir = dir.rotateLeft()
        else:
            dir = dir.rotateRight()
        if not Mopper.stuck:
            if rc.canMove(dir) and not rc.senseMapInfo(rc.getLocation().add(dir)).getPaint().isEnemy() and Mopper.noBacktrack(rc, dir):
                rc.move(dir)
                Mopper.pastLocs.append(rc.getLocation())
                return True
        if Mopper.moveRight:
            dir = dir.rotateRight()
        else:
            dir = dir.rotateLeft()
        if rc.canMove(dir) and Mopper.noBacktrack(rc, dir):
            rc.move(dir)
            Mopper.pastLocs.append(rc.getLocation())
            Mopper.stuck = False
            return True
        if Mopper.moveRight:
            dir = dir.rotateRight()
        else:
            dir = dir.rotateLeft()
        if rc.canMove(dir) and Mopper.noBacktrack(rc, dir):
            rc.move(dir)
            Mopper.pastLocs.append(rc.getLocation())
            Mopper.stuck = False
            return True
        if Mopper.moveRight:
            dir = dir.rotateLeft()
        else:
            dir = dir.rotateRight()
        if Mopper.moveRight:
            dir = dir.rotateLeft()
        else:
            dir = dir.rotateRight()
        if not Mopper.stuck:
            if rc.canMove(dir) and Mopper.noBacktrack(rc, dir):
                rc.move(dir)
                Mopper.pastLocs.append(rc.getLocation())
                return True
        if Mopper.moveRight:
            dir = dir.rotateRight()
        else:
            dir = dir.rotateLeft()
        Mopper.stuck = True
        rc.setIndicatorString("Stuck" + ("Right" if Mopper.moveRight else "Left"))
        if Mopper.moveRight:
            dir = dir.rotateRight()
            dir = dir.rotateRight()
            if rc.canMove(dir) and Mopper.noBacktrack(rc, dir):
                rc.move(dir)
                Mopper.pastLocs.append(rc.getLocation())
                return False
            dir = dir.rotateRight()
            if rc.canMove(dir) and Mopper.noBacktrack(rc, dir):
                rc.move(dir)
                Mopper.pastLocs.append(rc.getLocation())
                return False
            dir = dir.rotateRight()
            if rc.canMove(dir) and Mopper.noBacktrack(rc, dir):
                rc.move(dir)
                Mopper.pastLocs.append(rc.getLocation())
                return False
            dir = dir.rotateRight()
            if rc.canMove(dir) and Mopper.noBacktrack(rc, dir):
                rc.move(dir)
                Mopper.pastLocs.append(rc.getLocation())
                return False
            dir = dir.rotateRight()
            if rc.canMove(dir) and Mopper.noBacktrack(rc, dir):
                rc.move(dir)
                Mopper.pastLocs.append(rc.getLocation())
                return False
            dir = dir.rotateRight()
            if rc.canMove(dir) and Mopper.noBacktrack(rc, dir):
                rc.move(dir)
                Mopper.pastLocs.append(rc.getLocation())
                return False
            dir = dir.rotateRight()
            if rc.canMove(dir):
                rc.move(dir)
                Mopper.pastLocs.append(rc.getLocation())
                return False
            dir = dir.rotateRight()
            if rc.canMove(dir):
                rc.move(dir)
                Mopper.pastLocs.append(rc.getLocation())
                return False
            dir = dir.rotateRight()
            if rc.canMove(dir):
                rc.move(dir)
                Mopper.pastLocs.append(rc.getLocation())
                return False
            dir = dir.rotateRight()
            if rc.canMove(dir):
                rc.move(dir)
                Mopper.pastLocs.append(rc.getLocation())
                return False
            dir = dir.rotateRight()
            if rc.canMove(dir):
                rc.move(dir)
                Mopper.pastLocs.append(rc.getLocation())
                return False
            dir = dir.rotateRight()
            if rc.canMove(dir):
                rc.move(dir)
                Mopper.pastLocs.append(rc.getLocation())
                return False
            dir = dir.rotateRight()
            if rc.canMove(dir):
                rc.move(dir)
                Mopper.pastLocs.append(rc.getLocation())
                return False
            dir = dir.rotateRight()
            if rc.canMove(dir):
                rc.move(dir)
                Mopper.pastLocs.append(rc.getLocation())
                return False
        else:
            dir = dir.rotateLeft()
            dir = dir.rotateLeft()
            if rc.canMove(dir) and Mopper.noBacktrack(rc, dir):
                rc.move(dir)
                Mopper.pastLocs.append(rc.getLocation())
                return False
            dir = dir.rotateLeft()
            if rc.canMove(dir) and Mopper.noBacktrack(rc, dir):
                rc.move(dir)
                Mopper.pastLocs.append(rc.getLocation())
                return False
            dir = dir.rotateLeft()
            if rc.canMove(dir) and Mopper.noBacktrack(rc, dir):
                rc.move(dir)
                Mopper.pastLocs.append(rc.getLocation())
                return False
            dir = dir.rotateLeft()
            if rc.canMove(dir) and Mopper.noBacktrack(rc, dir):
                rc.move(dir)
                Mopper.pastLocs.append(rc.getLocation())
                return False
            dir = dir.rotateLeft()
            if rc.canMove(dir) and Mopper.noBacktrack(rc, dir):
                rc.move(dir)
                Mopper.pastLocs.append(rc.getLocation())
                return False
            dir = dir.rotateLeft()
            if rc.canMove(dir) and Mopper.noBacktrack(rc, dir):
                rc.move(dir)
                Mopper.pastLocs.append(rc.getLocation())
                return False
            dir = dir.rotateLeft()
            if rc.canMove(dir):
                rc.move(dir)
                Mopper.pastLocs.append(rc.getLocation())
                return False
            dir = dir.rotateLeft()
            if rc.canMove(dir):
                rc.move(dir)
                Mopper.pastLocs.append(rc.getLocation())
                return False
            dir = dir.rotateLeft()
            if rc.canMove(dir):
                rc.move(dir)
                Mopper.pastLocs.append(rc.getLocation())
                return False
            dir = dir.rotateLeft()
            if rc.canMove(dir):
                rc.move(dir)
                Mopper.pastLocs.append(rc.getLocation())
                return False
            dir = dir.rotateLeft()
            if rc.canMove(dir):
                rc.move(dir)
                Mopper.pastLocs.append(rc.getLocation())
                return False
            dir = dir.rotateLeft()
            if rc.canMove(dir):
                rc.move(dir)
                Mopper.pastLocs.append(rc.getLocation())
                return False
            dir = dir.rotateLeft()
            if rc.canMove(dir):
                rc.move(dir)
                Mopper.pastLocs.append(rc.getLocation())
                return False
            dir = dir.rotateLeft()
            if rc.canMove(dir):
                rc.move(dir)
                Mopper.pastLocs.append(rc.getLocation())
                return False
        return False

    # unfinished stuff very important trust
    enemyCell = None
    allyCell = None

    @staticmethod
    def findEnemyCell(rc):
        nearby = rc.senseNearbyMapInfos()
        closest = None
        for mi in nearby:
            if not mi.getPaint().isEnemy():
                continue
            if closest is None or rc.getLocation().distanceSquaredTo(mi.getMapLocation()) < rc.getLocation().distanceSquaredTo(closest.getMapLocation()):
                closest = mi
        if closest is not None:
            Mopper.enemyCell = closest.getMapLocation()
        else:
            Mopper.enemyCell = None

    @staticmethod
    def findAnyAllyCell(rc):
        nearby = rc.senseNearbyMapInfos()
        closest = None
        for mi in nearby:
            if not mi.getPaint().isAlly():
                continue
            if closest is None or rc.getLocation().distanceSquaredTo(mi.getMapLocation()) < rc.getLocation().distanceSquaredTo(closest.getMapLocation()):
                closest = mi
        if closest is not None:
            Mopper.allyCell = closest.getMapLocation()

    @staticmethod
    def findAllyCell(rc):
        nearby = rc.senseNearbyMapInfos()
        furthest = None
        for mi in nearby:
            if not mi.getPaint().isAlly() or not mi.isPassable():
                continue
            if furthest is None or rc.getLocation().distanceSquaredTo(mi.getMapLocation()) > rc.getLocation().distanceSquaredTo(furthest.getMapLocation()):
                furthest = mi
        if furthest is not None:
            Mopper.allyCell = furthest.getMapLocation()

    @staticmethod
    def cleanUpSomePaint(rc, loc):
        if (loc is not None and not rc.canAttack(loc)) or not rc.isActionReady():
            return False
        nearby = rc.senseNearbyMapInfos()
        closest = None
        for mi in nearby:
            if not mi.getPaint().isEnemy() or not rc.canSenseRobotAtLocation(mi.getMapLocation()) or rc.senseRobotAtLocation(mi.getMapLocation()) is None or rc.senseRobotAtLocation(mi.getMapLocation()).getTeam() == rc.getTeam():
                continue
            if closest is not None:
                if rc.getLocation().distanceSquaredTo(mi.getMapLocation()) < rc.getLocation().distanceSquaredTo(closest.getMapLocation()):
                    closest = mi
            else:
                closest = mi
        if closest is not None and rc.canAttack(closest.getMapLocation()):
            rc.attack(closest.getMapLocation())
        elif loc is not None:
            rc.attack(loc)
        Mopper.enemyCell = None
        return True

    @staticmethod
    def paintEnemyCell(rc):
        if Mopper.enemyCell is None or not rc.isActionReady():
            return False
        if Mopper.cleanUpSomePaint(rc, Mopper.enemyCell):
            Mopper.enemyCell = None
            return True
        successful = Mopper.moveTowardsMindfully(rc, Mopper.enemyCell)
        if not successful:
            return False
        if Mopper.cleanUpSomePaint(rc, Mopper.enemyCell):
            Mopper.enemyCell = None
            return True
        return False

    @staticmethod
    def donatePaint(rc):
        if rc.getPaint() <= 60:
            return
        nearby = rc.senseNearbyRobots(8, rc.getTeam())
        lowest = None
        for ri in nearby:
            if ri.type != UnitType.MOPPER and ri.type != UnitType.SPLASHER and ri.type != UnitType.SOLDIER:
                continue
            if lowest is None or ri.getPaintAmount() < lowest.getPaintAmount():
                lowest = ri
        if lowest is None:
            return
        if lowest.type == UnitType.SPLASHER and lowest.getPaintAmount() >= 240:
            return
        if lowest.type == UnitType.MOPPER and lowest.getPaintAmount() >= 45:
            return
        if lowest.type == UnitType.SOLDIER and lowest.getPaintAmount() >= 120:
            return
        if lowest.type == UnitType.SPLASHER:
            amt = min(300 - lowest.getPaintAmount(), rc.getPaint() - 40)
        elif lowest.type == UnitType.MOPPER:
            amt = min(100 - lowest.getPaintAmount(), rc.getPaint() - 50)
        else:
            amt = min(200 - lowest.getPaintAmount(), rc.getPaint() - 50)
        if not rc.canTransferPaint(lowest.getLocation(), amt):
            Mopper.moveTowardsMindfully(rc, lowest.getLocation())
        if rc.canTransferPaint(lowest.getLocation(), amt):
            rc.transferPaint(lowest.getLocation(), amt)

    @staticmethod
    def stealPaint(rc):
        if rc.getPaint() >= 90 or not rc.isActionReady():
            return
        for ri in rc.senseNearbyRobots(2, rc.getTeam()):
            if ri.type != UnitType.MOPPER and ri.type != UnitType.SPLASHER and ri.type != UnitType.SOLDIER:
                if ri.getPaintAmount() > 10:
                    amt = min(ri.getPaintAmount(), 100 - rc.getPaint())
                    if rc.canTransferPaint(ri.getLocation(), -amt):
                        rc.transferPaint(ri.getLocation(), -amt)
                        return
                    ret = Mopper.moveTowardsMindfully(rc, ri.getLocation())
                    if not ret:
                        return
                    if rc.canTransferPaint(ri.getLocation(), -amt):
                        rc.transferPaint(ri.getLocation(), -amt)
                        return
                return

    @staticmethod
    def move(rc):
        if not rc.isMovementReady():
            return
        if rc.senseMapInfo(rc.getLocation()).getPaint().isEnemy():
            Mopper.findAnyAllyCell(rc)
            if Mopper.allyCell is None:
                for dir in Mopper.directions:
                    if not rc.senseMapInfo(rc.getLocation().add(dir)).getPaint().isEnemy():
                        if rc.canMove(dir):
                            rc.move(dir)
                            return
                Mopper.explore(rc)
            else:
                Mopper.moveTowardsMindfully(rc, Mopper.allyCell)
                # Java: `== allyCell` was reference identity (always false
                # for distinct MapLocations) -> `is`
                if rc.getLocation() is Mopper.allyCell:
                    Mopper.allyCell = None
        elif rc.senseMapInfo(rc.getLocation()).getPaint().isAlly():
            if Mopper.enemyCell is None:
                Mopper.wander(rc)
            else:
                if rc.getLocation().distanceSquaredTo(Mopper.enemyCell) <= 2 or rc.getActionCooldownTurns() > 2:
                    return
                Mopper.moveTowardsMindfully(rc, Mopper.enemyCell)
        else:
            if Mopper.enemyCell is None or rc.getActionCooldownTurns() > 2:
                Mopper.findAnyAllyCell(rc)
                if Mopper.allyCell is None:
                    Mopper.explore(rc)
                else:
                    Mopper.moveTowardsMindfully(rc, Mopper.allyCell)
                    # Java: `== allyCell` was reference identity -> `is`
                    if rc.getLocation() is Mopper.allyCell:
                        Mopper.allyCell = None
            else:
                if rc.getLocation().distanceSquaredTo(Mopper.enemyCell) <= 2:
                    if not rc.senseMapInfo(rc.getLocation()).getPaint().isAlly():
                        Mopper.findAnyAllyCell(rc)
                        if Mopper.allyCell is None:
                            for dir in Mopper.directions:
                                if not rc.senseMapInfo(rc.getLocation().add(dir)).getPaint().isEnemy():
                                    if rc.canMove(dir):
                                        rc.move(dir)
                                        return
                            Mopper.explore(rc)
                        else:
                            Mopper.moveTowardsMindfully(rc, Mopper.allyCell)
                            # Java: `== allyCell` was reference identity -> `is`
                            if rc.getLocation() is Mopper.allyCell:
                                Mopper.allyCell = None
                    return
                Mopper.moveTowardsMindfully(rc, Mopper.enemyCell)

    orderedTo = None

    @staticmethod
    def followOrders(rc):
        if Mopper.orderedTo is None:
            return
        # print("Im a good bunny " + str(Clock.getBytecodeNum()))
        rc.setIndicatorString("Folliwng orders to " + str(Mopper.orderedTo))
        rc.setIndicatorLine(rc.getLocation(), Mopper.orderedTo, 69, 69, 255)
        if rc.canSenseLocation(Mopper.orderedTo) and not rc.senseMapInfo(Mopper.orderedTo).getPaint().isEnemy():
            Mopper.orderedTo = None
            return
        if not rc.canSenseLocation(Mopper.orderedTo):
            Mopper.cleanUpSomePaint(rc, None)
            Mopper.moveTowardsMindfully(rc, Mopper.orderedTo)
            Mopper.cleanUpSomePaint(rc, None)
        else:
            if rc.canAttack(Mopper.orderedTo):
                rc.attack(Mopper.orderedTo)
                Mopper.orderedTo = None
                return
            Mopper.moveTowardsMindfully(rc, Mopper.orderedTo)
            if rc.canAttack(Mopper.orderedTo):
                rc.attack(Mopper.orderedTo)
                Mopper.orderedTo = None

    @staticmethod
    def doStuff(rc):
        Comms.Comms.getMsg(rc)
        Mopper.followOrders(rc)
        Mopper.donatePaint(rc)
        Mopper.findEnemyCell(rc)
        if Mopper.enemyCell is not None:
            Mopper.paintEnemyCell(rc)
        Mopper.move(rc)
        Mopper.stealPaint(rc)

    victim = None

    @staticmethod
    def findClosestVictim(rc):
        closest = None
        for ri in rc.senseNearbyRobots(-1, opponent(rc.getTeam())):
            if closest is None or rc.getLocation().distanceSquaredTo(ri.getLocation()) <= rc.getLocation().distanceSquaredTo(closest):
                closest = ri.getLocation()
        if closest is not None:
            Mopper.victim = closest

    @staticmethod
    def attackVictim(rc):
        if not rc.isActionReady():
            return False
        if Mopper.victim is None or rc.getLocation().distanceSquaredTo(Mopper.victim) > 8:
            return False
        if rc.canAttack(Mopper.victim):
            rc.attack(Mopper.victim)
            return True
        successful = Mopper.moveTowardsMindfully(rc, Mopper.victim)
        if not successful:
            return False
        if rc.canAttack(Mopper.victim):
            rc.attack(Mopper.victim)
            return True
        return False

    @staticmethod
    def beBully(rc):
        Mopper.findClosestVictim(rc)
        isBully = Mopper.attackVictim(rc)
        if not isBully:
            Mopper.doStuff(rc)
        else:
            Mopper.moveTowardsMindfully(rc, Mopper.victim)

    # TODO: add feature where if cant move anywhere in a certain amount of time, then we explore for a certain number of turns
    # Java: @SuppressWarnings("unused")
    @staticmethod
    def paint(loc):
        curr = loc.getPaint()
        if curr == PaintType.ALLY_PRIMARY or curr == PaintType.ALLY_SECONDARY or loc.isWall():
            return 1
        if curr == PaintType.EMPTY:
            return 0
        else:
            return -1

    closestEnemyTower = None

    @staticmethod
    def run(rc):
        tower = Mopper.closestEnemyTowerInfo(rc)
        Mopper.closestEnemyTower = None if tower is None else tower.location
        # Java: switch (mood)
        if Mopper.mood == Mopper.State.NICE:
            Mopper.doStuff(rc)
        elif Mopper.mood == Mopper.State.BULLY:
            Mopper.beBully(rc)
        else:
            Mopper.doStuff(rc)
