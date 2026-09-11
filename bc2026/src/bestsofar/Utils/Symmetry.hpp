#pragma once
#include "api.hpp"
#include "Utils/Globals.hpp"

namespace Utils {

struct Symmetry : Globals {
    static constexpr int vertical = 1;
    static constexpr int horizontal = 2;
    static constexpr int rotational = 4;

    static int symm;  // 0: possible, 1: impossible

    static bool isSymmetryPossible(int s);
    static MapLocation symmetricallyOpposite(MapLocation loc, int s);
    static vector<int> getPossibleSymmetries();
    static void updateNearbySymmetry();
    static void updateSymmetryFromGlobal();
    static void commSymmetryToNearby();
    static void hearNearbySymmetrySqueaks();
};

}  // namespace Utils
