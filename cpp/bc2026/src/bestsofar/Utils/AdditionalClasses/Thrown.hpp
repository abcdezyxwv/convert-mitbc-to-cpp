#pragma once
#include "api.hpp"

namespace Utils {
namespace AdditionalClasses {

struct Thrown {
    MapLocation loc;
    Direction dir;

    Thrown() = default;
    Thrown(MapLocation m, Direction d) : loc(m), dir(d) {}

    bool isSafe(MapLocation check) {
        if (check == loc) return false;
        check = check.subtract(dir);
        if (check == loc) return false;
        check = check.subtract(dir);
        if (check == loc) return false;
        return true;
    }
};

}  // namespace AdditionalClasses
}  // namespace Utils
