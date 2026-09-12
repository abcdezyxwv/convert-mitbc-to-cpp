# Port of philip_06/Helper/Comms.java. See py/CONVENTIONS.md.
# Bot-internal imports use the module form (`import X` / `from pkg import X`)
# and sit below the class because this bot's import graph is cyclic - names
# resolve at call time, like the reechee port's `import RobotPlayer` +
# `RobotPlayer.RobotPlayer.*`.
from api import *

# Java: import java.util.Map - Map.entry(a, b) is ported as the tuple (a, b)


def _jmod(a, b):
    # Java % truncates toward zero; Python % floors (the two differ when the
    # dividend is negative, and msg.getBytes() can carry a negative int32).
    return a - int(a / b) * b


class Comms:
    @staticmethod
    def encode(rc, pri, ML, roundNum, msg):
        message = 0
        # UnitType 0: tower, 1: soldier, 2: mopper, 3: splasher
        if rc.getType() == UnitType.SOLDIER:
            message = 1
        elif rc.getType() == UnitType.MOPPER:
            message = 2
        elif rc.getType() == UnitType.SPLASHER:
            message = 3
        message = (message << 3)
        # Priority
        message += pri
        message = (message << 6)
        # Map Location
        message += ML.x
        message = (message << 6)
        message += ML.y
        message = (message << 11)
        # Which round
        message += roundNum
        message = (message << 3)
        # What message
        message += msg
        return message

    @staticmethod
    def decode(message):
        ans = [0] * 6
        ans[5] = _jmod(message, 1 << 3)
        message = (message >> 3)
        ans[4] = _jmod(message, 1 << 11)
        message = (message >> 11)
        ans[3] = _jmod(message, 1 << 6)
        message = (message >> 6)
        ans[2] = _jmod(message, 1 << 6)
        message = (message >> 6)
        ans[1] = _jmod(message, 1 << 3)
        message = (message >> 3)
        ans[0] = message
        # Returns an array containing:
        # {Unit Type, Priority, Map Location, Round info, Message}
        return ans

    @staticmethod
    def encodeLocation(loc):
        return (loc.x << 6) + loc.y

    @staticmethod
    def decodeLocation(k):
        return MapLocation(_jmod(k >> 6, 64), _jmod(k, 64))

    @staticmethod
    def encodeReport(loc, type):
        # types:
        # 0: Spawn Mopper to go to (x,y) (mainly to cleanup paint ruining ruins
        # 1: Attack (x,y) , spawn an army of bots to the location
        return (loc.x << 6) + loc.y + (type << 12)

    needMopperHelp = None
    turnLastSeen = -1000

    @staticmethod
    def getMsg(rc):
        if rc.getType().isRobotType():
            if rc.getType() == UnitType.MOPPER:
                for msg in rc.readMessages(rc.getRoundNum() - 1):
                    if Comms.decodeLocation(msg.getBytes()) == MapLocation(61, 61):
                        continue
                    Mopper.Mopper.orderedTo = Comms.decodeLocation(msg.getBytes())
                return
            for msg in rc.readMessages(rc.getRoundNum() - 1):
                if msg.getBytes() >> 30 == 1:
                    RobotPlayer.RobotPlayer.lastSeenEnemy = 0
                if Comms.decodeLocation(msg.getBytes()) == MapLocation(61, 61):
                    continue
                print(Comms.decodeLocation(msg.getBytes()))
                Soldier.Soldier.attack = Comms.decodeLocation(msg.getBytes())
                Splasher.Splasher.destination = Comms.decodeLocation(msg.getBytes())
        else:
            for msg in rc.readMessages(rc.getRoundNum() - 1):
                val = msg.getBytes()
                if val >> 30 != 0:
                    Comms.needMopperHelp = Comms.decodeLocation(val)
                    Comms.turnLastSeen = _jmod(val >> 12, 1 << 12)
                    Tower.Tower.toSpawn.clear()
                    Tower.Tower.toSpawn.append((UnitType.MOPPER, Comms.needMopperHelp))  # Java: Map.entry -> tuple
                    #System.out.println("Need mopper help at "+needMopperHelp);
                    continue
                if _jmod(val >> 12, 2) == 0:
                    Actions.Actions.spawn(rc, UnitType.MOPPER, Comms.decodeLocation(val))
                else:
                    if Comms.decodeLocation(val) == MapLocation(61, 61):
                        continue
                    RobotPlayer.RobotPlayer.lastSeenEnemy = rc.getRoundNum()
                    Tower.Tower.target = Comms.decodeLocation(val)
                    Tower.Tower.targetRound = rc.getRoundNum()
                    rc.setIndicatorLine(rc.getLocation(), Comms.decodeLocation(val), 0, 0, 0)
                    Tower.Tower.toSpawn.append((UnitType.SOLDIER, Comms.decodeLocation(val)))  # Java: Map.entry -> tuple
                    Tower.Tower.toSpawn.append((UnitType.SOLDIER, Comms.decodeLocation(val)))  # Java: Map.entry -> tuple
                # Java: val>>13%2==0 parses as (val >> (13 % 2)) == 0
                if val >> 13 % 2 == 0 and rc.canBroadcastMessage():
                    rc.broadcastMessage(val + (1 << 13))

    @staticmethod
    def sendMsg(rc):
        if rc.getType().isTowerType():
            if Comms.needMopperHelp is not None and rc.getRoundNum() - Comms.turnLastSeen <= (rc.getMapHeight() + rc.getMapWidth()) // 5:
                for ri in rc.senseNearbyRobots(-1, rc.getTeam()):
                    if ri.type == UnitType.MOPPER:
                        if rc.canSendMessage(ri.location):
                            rc.sendMessage(ri.location, Comms.encodeLocation(Comms.needMopperHelp))
                            #System.out.println("Send message "+needMopperHelp+" to "+ri.location);
            return
        if Build.Build.enemyPaintCell is not None and (rc.getRoundNum() - Build.Build.turnEnemyPaintCell <= (rc.getMapWidth() + rc.getMapHeight()) // 7 or Build.Build.askForMopper):
            for ri in rc.senseNearbyRobots(-1, rc.getTeam()):
                if ri.getType().isTowerType():
                    if rc.canSendMessage(ri.getLocation()):
                        rc.sendMessage(ri.getLocation(), Comms.encodeReport(Build.Build.enemyPaintCell, Build.Build.turnEnemyPaintCell + (1 << 18)))
                        Build.Build.enemyPaintCell = None
                        Build.Build.askForMopper = False
                        return
                        #// + (1<<19) so the 30th bit is set
                        # encode the location, then the turn the location was last seen to be disrupting
        if RobotPlayer.RobotPlayer.lastEnemyTower is not None:
            for loc in rc.senseNearbyRuins(-1):
                if rc.senseRobotAtLocation(loc) is not None and rc.senseRobotAtLocation(loc).getTeam() == rc.getTeam():
                    if rc.canSendMessage(loc):
                        rc.sendMessage(loc, Comms.encodeReport(RobotPlayer.RobotPlayer.lastEnemyTower, 1))
                        RobotPlayer.RobotPlayer.lastEnemyTower = None
                        return


# Java's file-level imports, deferred below the class: several sibling modules
# do `from Helper.Comms import Comms`, which only resolves once the class
# object already exists in the partially-initialised module.
import RobotPlayer
import Soldier
from SoldierState import Build
from utils import Actions
from roles import Mopper
from roles import Splasher
from roles import Tower
