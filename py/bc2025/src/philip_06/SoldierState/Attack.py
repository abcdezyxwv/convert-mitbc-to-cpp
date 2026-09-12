# Port of philip_06/SoldierState/Attack.java. See py/CONVENTIONS.md.
# Module-form imports for bot-internal deps (cyclic import graph) - names
# resolve at call time. Splasher is used fully qualified in the Java.
from api import *
import RobotPlayer
from roles import Mopper
from roles import Splasher


class Attack:

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

    target = None
    next = None
    found = False

    @staticmethod
    def rotational(rc, curr):
        return MapLocation(rc.getMapWidth() - curr.x - 1, rc.getMapHeight() - curr.y - 1)

    @staticmethod
    def vertical(rc, curr):
        return MapLocation(rc.getMapWidth() - curr.x - 1, curr.y)

    @staticmethod
    def horizontal(rc, curr):
        return MapLocation(curr.x, rc.getMapHeight() - curr.y - 1)

    @staticmethod
    def onMap(rc, curr):
        return curr.x >= 0 and curr.x < rc.getMapWidth() and curr.y >= 0 and curr.y < rc.getMapHeight()

    @staticmethod
    def run(rc):
        # Check if there are any close ones
        ruins = rc.senseNearbyRuins(-1)
        for ruin in ruins:
            robot = rc.senseRobotAtLocation(ruin)
            if robot is not None and robot.getTeam() != rc.getTeam() and ruin != Attack.target:
                if ruin == Attack.next:
                    Attack.target = Attack.next
                    Attack.next = ruin
                    break
                if Attack.found:
                    Attack.next = ruin
                else:
                    Attack.found = True
                    Attack.target = ruin
                break

        if Attack.target is None:
            Attack.target = Splasher.Splasher.getNextCorner(rc)
        if rc.canSenseLocation(Attack.target) and (rc.senseRobotAtLocation(Attack.target) is None or rc.senseRobotAtLocation(Attack.target).getTeam() == rc.getTeam()):
            Attack.target = Attack.next
            Attack.next = None
        if Attack.target is None:
            RobotPlayer.RobotPlayer.rush = False
            RobotPlayer.RobotPlayer.fill = True
            RobotPlayer.RobotPlayer.build = False
            Attack.target = Splasher.Splasher.getNextCorner(rc)

        # Begin kiting
        if rc.getLocation().isWithinDistanceSquared(Attack.target, 20):
            if rc.senseRobotAtLocation(Attack.target) is None:
                # Destroyed building
                if Attack.next is not None:
                    Attack.target = Attack.next
                    Attack.next = None
                    Attack.found = True
                else:
                    Attack.found = False
                    RobotPlayer.RobotPlayer.rush = False
                    RobotPlayer.RobotPlayer.fill = True
                    RobotPlayer.RobotPlayer.build = False
                    Attack.target = Splasher.Splasher.getNextCorner(rc)
            else:
                # Kiting
                if rc.getLocation().isWithinDistanceSquared(Attack.target, 9):
                    if rc.canAttack(Attack.target):
                        rc.attack(Attack.target)
                    dir = rc.getLocation().directionTo(Attack.target)
                    for i in range(4):
                        if rc.canMove(dir.opposite()):
                            rc.move(dir.opposite())
                        dir = dir.rotateLeft()
                elif rc.isActionReady():
                    if rc.canMove(rc.getLocation().directionTo(Attack.target)):
                        rc.move(rc.getLocation().directionTo(Attack.target))
                    else:
                        Mopper.Mopper.moveTowardsMindlessly(rc, Attack.target)
                    if rc.canAttack(Attack.target):
                        rc.attack(Attack.target)
        else:
            Mopper.Mopper.moveTowardsMindlessly(rc, Attack.target)
