# Port of bestsofar/Utils/CatsAreWalls.java. See py/CONVENTIONS.md.
from api import *
from Utils.Globals import Globals
from Utils.Vision import Vision


class CatsAreWalls(Globals):

    @staticmethod
    def pretend(loc, dir):
        # Java: switch (dir)
        if dir == Direction.SOUTHWEST:
            loc = loc.add(Direction.SOUTH)
            if Globals.rc.onTheMap(loc):
                Vision.isDangerous[loc.x] |= 1 << loc.y
            loc = loc.add(Direction.WEST)
            if Globals.rc.onTheMap(loc):
                Vision.isDangerous[loc.x] |= 1 << loc.y
            loc = loc.add(Direction.NORTH)
            if Globals.rc.onTheMap(loc):
                Vision.isDangerous[loc.x] |= 1 << loc.y
        elif dir == Direction.SOUTHEAST:
            loc = loc.add(Direction.SOUTHEAST)
            if Globals.rc.onTheMap(loc):
                Vision.isDangerous[loc.x] |= 1 << loc.y
            loc = loc.add(Direction.EAST)
            if Globals.rc.onTheMap(loc):
                Vision.isDangerous[loc.x] |= 1 << loc.y
            loc = loc.add(Direction.NORTH)
            if Globals.rc.onTheMap(loc):
                Vision.isDangerous[loc.x] |= 1 << loc.y
        elif dir == Direction.NORTHWEST:
            loc = loc.add(Direction.NORTHWEST)
            if Globals.rc.onTheMap(loc):
                Vision.isDangerous[loc.x] |= 1 << loc.y
            loc = loc.add(Direction.NORTH)
            if Globals.rc.onTheMap(loc):
                Vision.isDangerous[loc.x] |= 1 << loc.y
            loc = loc.add(Direction.EAST)
            if Globals.rc.onTheMap(loc):
                Vision.isDangerous[loc.x] |= 1 << loc.y
        elif dir == Direction.NORTHEAST:
            loc = loc.add(Direction.EAST).add(Direction.NORTHEAST)
            if Globals.rc.onTheMap(loc):
                Vision.isDangerous[loc.x] |= 1 << loc.y
            loc = loc.add(Direction.NORTH)
            if Globals.rc.onTheMap(loc):
                Vision.isDangerous[loc.x] |= 1 << loc.y
            loc = loc.add(Direction.WEST)
            if Globals.rc.onTheMap(loc):
                Vision.isDangerous[loc.x] |= 1 << loc.y
        elif dir == Direction.NORTH:
            loc = loc.add(Direction.NORTH).add(Direction.NORTH)
            if Globals.rc.onTheMap(loc):
                Vision.isDangerous[loc.x] |= 1 << loc.y
            loc = loc.add(Direction.EAST)
            if Globals.rc.onTheMap(loc):
                Vision.isDangerous[loc.x] |= 1 << loc.y
        elif dir == Direction.SOUTH:
            loc = loc.add(Direction.SOUTH)
            if Globals.rc.onTheMap(loc):
                Vision.isDangerous[loc.x] |= 1 << loc.y
            loc = loc.add(Direction.EAST)
            if Globals.rc.onTheMap(loc):
                Vision.isDangerous[loc.x] |= 1 << loc.y
        elif dir == Direction.WEST:
            loc = loc.add(Direction.WEST)
            if Globals.rc.onTheMap(loc):
                Vision.isDangerous[loc.x] |= 1 << loc.y
            loc = loc.add(Direction.NORTH)
            if Globals.rc.onTheMap(loc):
                Vision.isDangerous[loc.x] |= 1 << loc.y
        elif dir == Direction.EAST:
            loc = loc.add(Direction.EAST).add(Direction.EAST)
            if Globals.rc.onTheMap(loc):
                Vision.isDangerous[loc.x] |= 1 << loc.y
            loc = loc.add(Direction.NORTH)
            if Globals.rc.onTheMap(loc):
                Vision.isDangerous[loc.x] |= 1 << loc.y

    @staticmethod
    def unpretend(loc, dir):
        # Java: switch (dir)
        if dir == Direction.SOUTHWEST:
            loc = loc.add(Direction.SOUTH)
            if Globals.rc.onTheMap(loc):
                Vision.isDangerous[loc.x] &= ~(1 << loc.y)
            loc = loc.add(Direction.WEST)
            if Globals.rc.onTheMap(loc):
                Vision.isDangerous[loc.x] &= ~(1 << loc.y)
            loc = loc.add(Direction.NORTH)
            if Globals.rc.onTheMap(loc):
                Vision.isDangerous[loc.x] &= ~(1 << loc.y)
        elif dir == Direction.SOUTHEAST:
            loc = loc.add(Direction.SOUTHEAST)
            if Globals.rc.onTheMap(loc):
                Vision.isDangerous[loc.x] &= ~(1 << loc.y)
            loc = loc.add(Direction.EAST)
            if Globals.rc.onTheMap(loc):
                Vision.isDangerous[loc.x] &= ~(1 << loc.y)
            loc = loc.add(Direction.NORTH)
            if Globals.rc.onTheMap(loc):
                Vision.isDangerous[loc.x] &= ~(1 << loc.y)
        elif dir == Direction.NORTHWEST:
            loc = loc.add(Direction.NORTHWEST)
            if Globals.rc.onTheMap(loc):
                Vision.isDangerous[loc.x] &= ~(1 << loc.y)
            loc = loc.add(Direction.NORTH)
            if Globals.rc.onTheMap(loc):
                Vision.isDangerous[loc.x] &= ~(1 << loc.y)
            loc = loc.add(Direction.EAST)
            if Globals.rc.onTheMap(loc):
                Vision.isDangerous[loc.x] &= ~(1 << loc.y)
        elif dir == Direction.NORTHEAST:
            loc = loc.add(Direction.EAST).add(Direction.NORTHEAST)
            if Globals.rc.onTheMap(loc):
                Vision.isDangerous[loc.x] &= ~(1 << loc.y)
            loc = loc.add(Direction.NORTH)
            if Globals.rc.onTheMap(loc):
                Vision.isDangerous[loc.x] &= ~(1 << loc.y)
            loc = loc.add(Direction.WEST)
            if Globals.rc.onTheMap(loc):
                Vision.isDangerous[loc.x] &= ~(1 << loc.y)
        elif dir == Direction.NORTH:
            loc = loc.add(Direction.NORTH).add(Direction.NORTH)
            if Globals.rc.onTheMap(loc):
                Vision.isDangerous[loc.x] &= ~(1 << loc.y)
            loc = loc.add(Direction.EAST)
            if Globals.rc.onTheMap(loc):
                Vision.isDangerous[loc.x] &= ~(1 << loc.y)
        elif dir == Direction.SOUTH:
            loc = loc.add(Direction.SOUTH)
            if Globals.rc.onTheMap(loc):
                Vision.isDangerous[loc.x] &= ~(1 << loc.y)
            loc = loc.add(Direction.EAST)
            if Globals.rc.onTheMap(loc):
                Vision.isDangerous[loc.x] &= ~(1 << loc.y)
        elif dir == Direction.WEST:
            loc = loc.add(Direction.WEST)
            if Globals.rc.onTheMap(loc):
                Vision.isDangerous[loc.x] &= ~(1 << loc.y)
            loc = loc.add(Direction.NORTH)
            if Globals.rc.onTheMap(loc):
                Vision.isDangerous[loc.x] &= ~(1 << loc.y)
        elif dir == Direction.EAST:
            loc = loc.add(Direction.EAST).add(Direction.EAST)
            if Globals.rc.onTheMap(loc):
                Vision.isDangerous[loc.x] &= ~(1 << loc.y)
            loc = loc.add(Direction.NORTH)
            if Globals.rc.onTheMap(loc):
                Vision.isDangerous[loc.x] &= ~(1 << loc.y)
