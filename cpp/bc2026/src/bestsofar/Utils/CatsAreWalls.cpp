#include "Utils/CatsAreWalls.hpp"

#include "Utils/Globals.hpp"
#include "Utils/Vision.hpp"

namespace Utils {

void CatsAreWalls::pretend(MapLocation loc, Direction dir) {
    switch (dir.e) {
        case Direction::SOUTHWEST:
            loc = loc.add(Direction::all[Direction::SOUTH]);
            if (rc.onTheMap(loc)) Vision::isDangerous[loc.x] |= 1LL << loc.y;
            loc = loc.add(Direction::all[Direction::WEST]);
            if (rc.onTheMap(loc)) Vision::isDangerous[loc.x] |= 1LL << loc.y;
            loc = loc.add(Direction::all[Direction::NORTH]);
            if (rc.onTheMap(loc)) Vision::isDangerous[loc.x] |= 1LL << loc.y;
            break;
        case Direction::SOUTHEAST:
            loc = loc.add(Direction::all[Direction::SOUTHEAST]);
            if (rc.onTheMap(loc)) Vision::isDangerous[loc.x] |= 1LL << loc.y;
            loc = loc.add(Direction::all[Direction::EAST]);
            if (rc.onTheMap(loc)) Vision::isDangerous[loc.x] |= 1LL << loc.y;
            loc = loc.add(Direction::all[Direction::NORTH]);
            if (rc.onTheMap(loc)) Vision::isDangerous[loc.x] |= 1LL << loc.y;
            break;
        case Direction::NORTHWEST:
            loc = loc.add(Direction::all[Direction::NORTHWEST]);
            if (rc.onTheMap(loc)) Vision::isDangerous[loc.x] |= 1LL << loc.y;
            loc = loc.add(Direction::all[Direction::NORTH]);
            if (rc.onTheMap(loc)) Vision::isDangerous[loc.x] |= 1LL << loc.y;
            loc = loc.add(Direction::all[Direction::EAST]);
            if (rc.onTheMap(loc)) Vision::isDangerous[loc.x] |= 1LL << loc.y;
            break;
        case Direction::NORTHEAST:
            loc = loc.add(Direction::all[Direction::EAST]).add(Direction::all[Direction::NORTHEAST]);
            if (rc.onTheMap(loc)) Vision::isDangerous[loc.x] |= 1LL << loc.y;
            loc = loc.add(Direction::all[Direction::NORTH]);
            if (rc.onTheMap(loc)) Vision::isDangerous[loc.x] |= 1LL << loc.y;
            loc = loc.add(Direction::all[Direction::WEST]);
            if (rc.onTheMap(loc)) Vision::isDangerous[loc.x] |= 1LL << loc.y;
            break;
        case Direction::NORTH:
            loc = loc.add(Direction::all[Direction::NORTH]).add(Direction::all[Direction::NORTH]);
            if (rc.onTheMap(loc)) Vision::isDangerous[loc.x] |= 1LL << loc.y;
            loc = loc.add(Direction::all[Direction::EAST]);
            if (rc.onTheMap(loc)) Vision::isDangerous[loc.x] |= 1LL << loc.y;
            break;
        case Direction::SOUTH:
            loc = loc.add(Direction::all[Direction::SOUTH]);
            if (rc.onTheMap(loc)) Vision::isDangerous[loc.x] |= 1LL << loc.y;
            loc = loc.add(Direction::all[Direction::EAST]);
            if (rc.onTheMap(loc)) Vision::isDangerous[loc.x] |= 1LL << loc.y;
            break;
        case Direction::WEST:
            loc = loc.add(Direction::all[Direction::WEST]);
            if (rc.onTheMap(loc)) Vision::isDangerous[loc.x] |= 1LL << loc.y;
            loc = loc.add(Direction::all[Direction::NORTH]);
            if (rc.onTheMap(loc)) Vision::isDangerous[loc.x] |= 1LL << loc.y;
            break;
        case Direction::EAST:
            loc = loc.add(Direction::all[Direction::EAST]).add(Direction::all[Direction::EAST]);
            if (rc.onTheMap(loc)) Vision::isDangerous[loc.x] |= 1LL << loc.y;
            loc = loc.add(Direction::all[Direction::NORTH]);
            if (rc.onTheMap(loc)) Vision::isDangerous[loc.x] |= 1LL << loc.y;
            break;
        default:
            break;
    }
}

void CatsAreWalls::unpretend(MapLocation loc, Direction dir) {
    switch (dir.e) {
        case Direction::SOUTHWEST:
            loc = loc.add(Direction::all[Direction::SOUTH]);
            if (rc.onTheMap(loc)) Vision::isDangerous[loc.x] &= ~(1LL << loc.y);
            loc = loc.add(Direction::all[Direction::WEST]);
            if (rc.onTheMap(loc)) Vision::isDangerous[loc.x] &= ~(1LL << loc.y);
            loc = loc.add(Direction::all[Direction::NORTH]);
            if (rc.onTheMap(loc)) Vision::isDangerous[loc.x] &= ~(1LL << loc.y);
            break;
        case Direction::SOUTHEAST:
            loc = loc.add(Direction::all[Direction::SOUTHEAST]);
            if (rc.onTheMap(loc)) Vision::isDangerous[loc.x] &= ~(1LL << loc.y);
            loc = loc.add(Direction::all[Direction::EAST]);
            if (rc.onTheMap(loc)) Vision::isDangerous[loc.x] &= ~(1LL << loc.y);
            loc = loc.add(Direction::all[Direction::NORTH]);
            if (rc.onTheMap(loc)) Vision::isDangerous[loc.x] &= ~(1LL << loc.y);
            break;
        case Direction::NORTHWEST:
            loc = loc.add(Direction::all[Direction::NORTHWEST]);
            if (rc.onTheMap(loc)) Vision::isDangerous[loc.x] &= ~(1LL << loc.y);
            loc = loc.add(Direction::all[Direction::NORTH]);
            if (rc.onTheMap(loc)) Vision::isDangerous[loc.x] &= ~(1LL << loc.y);
            loc = loc.add(Direction::all[Direction::EAST]);
            if (rc.onTheMap(loc)) Vision::isDangerous[loc.x] &= ~(1LL << loc.y);
            break;
        case Direction::NORTHEAST:
            loc = loc.add(Direction::all[Direction::EAST]).add(Direction::all[Direction::NORTHEAST]);
            if (rc.onTheMap(loc)) Vision::isDangerous[loc.x] &= ~(1LL << loc.y);
            loc = loc.add(Direction::all[Direction::NORTH]);
            if (rc.onTheMap(loc)) Vision::isDangerous[loc.x] &= ~(1LL << loc.y);
            loc = loc.add(Direction::all[Direction::WEST]);
            if (rc.onTheMap(loc)) Vision::isDangerous[loc.x] &= ~(1LL << loc.y);
            break;
        case Direction::NORTH:
            loc = loc.add(Direction::all[Direction::NORTH]).add(Direction::all[Direction::NORTH]);
            if (rc.onTheMap(loc)) Vision::isDangerous[loc.x] &= ~(1LL << loc.y);
            loc = loc.add(Direction::all[Direction::EAST]);
            if (rc.onTheMap(loc)) Vision::isDangerous[loc.x] &= ~(1LL << loc.y);
            break;
        case Direction::SOUTH:
            loc = loc.add(Direction::all[Direction::SOUTH]);
            if (rc.onTheMap(loc)) Vision::isDangerous[loc.x] &= ~(1LL << loc.y);
            loc = loc.add(Direction::all[Direction::EAST]);
            if (rc.onTheMap(loc)) Vision::isDangerous[loc.x] &= ~(1LL << loc.y);
            break;
        case Direction::WEST:
            loc = loc.add(Direction::all[Direction::WEST]);
            if (rc.onTheMap(loc)) Vision::isDangerous[loc.x] &= ~(1LL << loc.y);
            loc = loc.add(Direction::all[Direction::NORTH]);
            if (rc.onTheMap(loc)) Vision::isDangerous[loc.x] &= ~(1LL << loc.y);
            break;
        case Direction::EAST:
            loc = loc.add(Direction::all[Direction::EAST]).add(Direction::all[Direction::EAST]);
            if (rc.onTheMap(loc)) Vision::isDangerous[loc.x] &= ~(1LL << loc.y);
            loc = loc.add(Direction::all[Direction::NORTH]);
            if (rc.onTheMap(loc)) Vision::isDangerous[loc.x] &= ~(1LL << loc.y);
            break;
        default:
            break;
    }
}

}  // namespace Utils
