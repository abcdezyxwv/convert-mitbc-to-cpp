# Port of bestsofar/Utils/Symmetry.java. See py/CONVENTIONS.md.
from api import *
from Utils.Comms import Comms
from Utils.Globals import Globals
from Utils.Vision import Vision


class Symmetry(Globals):

    vertical = 1
    horizontal = 2
    rotational = 4

    symm = 0  # 0: possible, 1: impossible

    @staticmethod
    def isSymmetryPossible(s):
        return (Symmetry.symm & s) != 0

    @staticmethod
    def symmetricallyOpposite(loc, s):
        if s == Symmetry.vertical:
            return MapLocation(Globals.mapWidth - 1 - loc.x, loc.y)
        if s == Symmetry.horizontal:
            return MapLocation(loc.x, Globals.mapHeight - 1 - loc.y)
        if s == Symmetry.rotational:
            return MapLocation(Globals.mapWidth - 1 - loc.x, Globals.mapHeight - 1 - loc.y)
        return None

    @staticmethod
    def getPossibleSymmetries():
        if Symmetry.symm == 0:
            return [1, 2, 4]
        if Symmetry.symm == 1:
            return [2, 4]
        if Symmetry.symm == 2:
            return [1, 4]
        if Symmetry.symm == 4:
            return [2, 4]
        if Symmetry.symm == 3:
            return [4]
        if Symmetry.symm == 5:
            return [2]
        if Symmetry.symm == 6:
            return [1]
        Globals.rc.setIndicatorString("what the hecky? no symmetries!")
        print("what the hecky? no symmetries!")
        return None

    @staticmethod
    def updateNearbySymmetry():
        possibleSymmetries = Symmetry.getPossibleSymmetries()

        # special case king to not bytecode exceed cuz its vision is bigger
        if isRatKingType(Globals.rc.getType()):  # Java: rc.getType().isRatKingType()
            # Java: rc.getType().getVisionRadiusSquared()
            for loc in Globals.rc.getAllLocationsWithinRadiusSquared(Globals.rc.getLocation(), Vision.visionConeRadiusSquared(Globals.rc.getType())):
                map = Globals.rc.senseMapInfo(loc)

                for s in possibleSymmetries:
                    opp = Symmetry.symmetricallyOpposite(loc, s)

                    if Vision.hasSeenLocation(opp):
                        if map.hasCheeseMine() != Vision.isMine(opp):
                            Symmetry.symm |= s
                        if map.isWall() != Vision.isWall(opp):
                            Symmetry.symm |= s
            return

        # baby rat
        for map in Globals.surroundings:
            loc = map.getMapLocation()

            mine = map.hasCheeseMine()
            wall = map.isWall()

            if not mine and not wall:
                continue  # save bytecode by only checking if the current cell is special

            for s in possibleSymmetries:
                opp = Symmetry.symmetricallyOpposite(loc, s)

                if Vision.hasSeenLocation(opp):
                    if mine != Vision.isMine(opp):
                        Symmetry.symm |= s
                    if wall != Vision.isWall(opp):
                        Symmetry.symm |= s

    @staticmethod
    def updateSymmetryFromGlobal():
        globalSymm = Comms.getSymmetry()
        Symmetry.symm |= globalSymm

    @staticmethod
    def commSymmetryToNearby():
        globalSymm = Comms.getSymmetry()

        # only if is within hearing distance of king
        if Globals.rc.getLocation().isWithinDistanceSquared(Globals.kingPos[0], 16):
            if Symmetry.symm != globalSymm:
                Globals.rc.squeak(Symmetry.symm)
                Globals.hasSqueaked = True
                print("squeaked new symmetry to king: " + str(Symmetry.symm))
        # squeak every round because we're doing it anyways
        elif not Globals.hasSqueaked and Symmetry.symm != globalSymm:
            Globals.rc.squeak(Symmetry.symm)
            Globals.hasSqueaked = True

    @staticmethod
    def hearNearbySymmetrySqueaks():
        for message in Globals.newestSqueaks:
            if 0 <= message.getBytes() and message.getBytes() < 8:
                Symmetry.symm |= message.getBytes()
