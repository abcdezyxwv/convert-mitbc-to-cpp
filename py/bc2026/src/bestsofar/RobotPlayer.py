# Port of bestsofar/RobotPlayer.java. See py/CONVENTIONS.md.
import traceback

from api import *
import Baby
import King
from Utils.Globals import Globals


class RobotPlayer:
    @staticmethod
    def run(rc):
        Globals.init(rc)

        while True:
            try:

                Globals.startTurn()

                # Java: switch on getType() - the expression is evaluated once
                t = rc.getType()
                if t == UnitType.BABY_RAT:
                    Baby.Baby.run()

                elif t == UnitType.RAT_KING:
                    King.King.run()

                Globals.endTurn()


                Clock.doYield()
            except GameActionException:
                print("GameActionException")
                traceback.print_exc()

            except Exception:
                print("Exception")
                traceback.print_exc()
