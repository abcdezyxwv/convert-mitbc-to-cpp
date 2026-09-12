# Port of philip_06/Helper/Pathfind.java. See py/CONVENTIONS.md.
# Bot-internal imports use the module form (`import X` / `from pkg import X`)
# and sit below the class because this bot's import graph is cyclic - names
# resolve at call time, like the reechee port's `import RobotPlayer` +
# `RobotPlayer.RobotPlayer.*`.
from api import *


class Pathfind:
    dest = None
    exploreDirection = None  # Java: declared, never used

    @staticmethod
    def setDest(rc, loc):
        #if (loc == null) {
        #    dest = new MapLocation(RobotPlayer.rng.nextInt(rc.getMapWidth()), RobotPlayer.rng.nextInt(rc.getMapHeight()));
        #} else {
        Pathfind.dest = loc
        #}

    @staticmethod
    def makeMove(rc):
        #if (dest == null) dest = new MapLocation(rc.getMapWidth()/2, rc.getMapHeight()/2);
        if Pathfind.dest is None:
            Pathfind.explore(rc)
            return
        rc.setIndicatorLine(rc.getLocation(), Pathfind.dest, 0, 255, 0)
        Mopper.Mopper.moveTowardsMindlessly(rc, Pathfind.dest)

    @staticmethod
    def explore(rc):
        Mopper.Mopper.explore(rc)


# Java's file-level imports, deferred below the class (cyclic import graph).
from roles import Mopper
import RobotPlayer  # only referenced inside the commented-out code above
