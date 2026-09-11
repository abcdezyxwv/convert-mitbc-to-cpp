#include "Utils/Symmetry.hpp"

#include <iostream>

#include "Utils/Comms.hpp"
#include "Utils/Globals.hpp"
#include "Utils/Vision.hpp"

namespace Utils {

int Symmetry::symm = 0;  // 0: possible, 1: impossible

bool Symmetry::isSymmetryPossible(int s) {
    return (symm & s) != 0;
}

MapLocation Symmetry::symmetricallyOpposite(MapLocation loc, int s) {
    if (s == vertical) return MapLocation(mapWidth - 1 - loc.x, loc.y);
    if (s == horizontal) return MapLocation(loc.x, mapHeight - 1 - loc.y);
    if (s == rotational) return MapLocation(mapWidth - 1 - loc.x, mapHeight - 1 - loc.y);
    return MapLocation::NONE;
}

vector<int> Symmetry::getPossibleSymmetries() {
    if (symm == 0) return {1, 2, 4};
    if (symm == 1) return {2, 4};
    if (symm == 2) return {1, 4};
    if (symm == 4) return {2, 4};
    if (symm == 3) return {4};
    if (symm == 5) return {2};
    if (symm == 6) return {1};
    rc.setIndicatorString("what the hecky? no symmetries!");
    std::cout << "what the hecky? no symmetries!" << '\n';
    return {};  // Java: return null (callers then NPE - see notes)
}

void Symmetry::updateNearbySymmetry() {
    vector<int> possibleSymmetries = getPossibleSymmetries();

    // special case king to not bytecode exceed cuz its vision is bigger
    if (isRatKingType(rc.getType())) {
        for (const MapLocation& loc : rc.getAllLocationsWithinRadiusSquared(
                 rc.getLocation(), Vision::visionConeRadiusSquared(rc.getType()))) {
            MapInfo map = rc.senseMapInfo(loc);

            for (const int& s : possibleSymmetries) {
                MapLocation opp = symmetricallyOpposite(loc, s);

                if (Vision::hasSeenLocation(opp)) {
                    if (map.hasCheeseMine() != Vision::isMine(opp)) symm |= s;
                    if (map.isWall() != Vision::isWall(opp)) symm |= s;
                }
            }
        }
        return;
    }

    // baby rat
    for (const MapInfo& map : surroundings) {
        MapLocation loc = map.getMapLocation();

        bool mine = map.hasCheeseMine();
        bool wall = map.isWall();

        if (!mine && !wall) continue;  // save bytecode by only checking if the current cell is special

        for (const int& s : possibleSymmetries) {
            MapLocation opp = symmetricallyOpposite(loc, s);

            if (Vision::hasSeenLocation(opp)) {
                if (mine != Vision::isMine(opp)) symm |= s;
                if (wall != Vision::isWall(opp)) symm |= s;
            }
        }
    }
}

void Symmetry::updateSymmetryFromGlobal() {
    int globalSymm = Comms::getSymmetry();
    symm |= globalSymm;
}

void Symmetry::commSymmetryToNearby() {
    int globalSymm = Comms::getSymmetry();

    // only if is within hearing distance of king
    if (rc.getLocation().isWithinDistanceSquared(kingPos[0], 16)) {
        if (symm != globalSymm) {
            rc.squeak(symm);
            hasSqueaked = true;
            std::cout << "squeaked new symmetry to king: " + std::to_string(symm) << '\n';
        }
    }
    // squeak every round because we're doing it anyways
    else if (!hasSqueaked && Symmetry::symm != globalSymm) {
        rc.squeak(Symmetry::symm);
        hasSqueaked = true;
    }
}

void Symmetry::hearNearbySymmetrySqueaks() {
    for (const Message& message : newestSqueaks) {
        if (0 <= message.getBytes() && message.getBytes() < 8) {
            symm |= message.getBytes();
        }
    }
}

}  // namespace Utils
