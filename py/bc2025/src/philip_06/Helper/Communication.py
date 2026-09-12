# Port of philip_06/Helper/Communication.java. See py/CONVENTIONS.md.
from api import *


def _jmod(a, b):
    # Java % truncates toward zero; Python % floors (the two differ when the
    # dividend is negative, and msg.getBytes() can carry a negative int32).
    return a - int(a / b) * b


class Communication:
    @staticmethod
    def encode(rc, pri, ML, msg):
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
        message += rc.getRoundNum()
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
