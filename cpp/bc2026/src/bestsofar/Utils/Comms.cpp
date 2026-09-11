#include "Utils/Comms.hpp"

#include <algorithm>

namespace Utils {

void Comms::init() {
    if (rc.getType() == UnitType::RAT_KING) {
        rc.writeSharedArray(63, 1);
    }
}
void Comms::startTurn() {
    if (rc.getType() == UnitType::RAT_KING) {
        // Locations
        int x = (rc.readSharedArray(63)>>3*(rc.getRoundNum()%3))%8;
        rc.writeSharedArray(2*x, rc.getLocation().x);
        rc.writeSharedArray(2*x+1, rc.getLocation().y);

        int v = rc.readSharedArray(63);
        switch (rc.getRoundNum()%3) {
            case 0:
                v += 1;
                v &= 0b111000111;
                break;
            case 1:
                v += 8;
                v &= 0b111111;
                break;
            case 2:
                v += 64;
                v &= 0b111111000;
        }
        rc.writeSharedArray(63, v);
    }
    int n = getNumKings();
    for (int i = 0; i < n; i++) {
        kingPos[i] = MapLocation(rc.readSharedArray(2*i), rc.readSharedArray(2*i+1));
    }
    for (int i = n; i < 5; i++) {
        kingPos[i] = MapLocation::NONE;
    }
}
int Comms::getNumKings() {
    return (rc.readSharedArray(63)>>3*((rc.getRoundNum()+2)%3))%8;
}
int Comms::getSymmetry() {
    return rc.readSharedArray(10);
}
void Comms::updateSymmetry(int x) {
    rc.writeSharedArray(10, x);
}
int Comms::encodeDir(Direction dir) {
    switch (dir.e) {
        case Direction::EAST: return 0;
        case Direction::WEST: return 1;
        case Direction::NORTH: return 2;
        case Direction::SOUTH: return 3;
        case Direction::NORTHEAST: return 4;
        case Direction::NORTHWEST: return 5;
        case Direction::SOUTHEAST: return 6;
        case Direction::SOUTHWEST: return 7;
        default: return 0;
    }
}
Direction Comms::decodeDir(int dir) {
    switch (dir) {
        case 0: return Direction::all[Direction::EAST];
        case 1: return Direction::all[Direction::WEST];
        case 2: return Direction::all[Direction::NORTH];
        case 3: return Direction::all[Direction::SOUTH];
        case 4: return Direction::all[Direction::NORTHEAST];
        case 5: return Direction::all[Direction::NORTHWEST];
        case 6: return Direction::all[Direction::SOUTHEAST];
        case 7: return Direction::all[Direction::SOUTHWEST];
        default: return Direction::all[Direction::EAST];
    }
}
void Comms::squeakEnemies() {
    // ignore if no threats (trust anson 1v1 micro)
    if ((enemyRobots.size() < 1) || hasSqueaked || (catRobots.size() > 0 && isRatKingType(rc.getType()))) return;
    // evaluate all the threats based off some heuristic
    RobotInfo weakest, strongest;
    int wScore = 1000000, sScore = 0;
    for (const RobotInfo& enemy : enemyRobots) {
        // Rat king is always the strongest
        if (enemy.getType() == UnitType::RAT_KING) {
            strongest = enemy;
            sScore = 1000000;
            if (isNullRobot(weakest)) weakest = enemy;
        } else {
            int score = 1000 + 2*enemy.getHealth();
            int penalty = std::max(0, 6 - (rc.getLocation().distanceSquaredTo(enemy.getLocation()) / 5));
            score += 10*penalty;
            // cheese slows them down
            score -= enemy.getRawCheeseAmount();
            // having a rat is really op
            RobotInfo gun = getCarryingRobot(enemy);
            if (!isNullRobot(gun)) {
                if (gun.getTeam() == myTeam) score += 100*penalty;
                else score += 60*penalty;
            }
            if (score <= wScore) {
                weakest = enemy;
                wScore = score;
            }
            if (score > sScore) {
                strongest = enemy;
                sScore = score;
            }
        }
    }


    // Communicate the weakest + strongest
    // encode weakest
    int msg = 0;
    if (!isNullRobot(weakest)) {
        // map x, map y, direction
        MapLocation wloc = weakest.getLocation();
        rc.setIndicatorDot(wloc, 0, 255, 0);
        msg += ((wloc.x) << 9) + ((wloc.y) << 3) + encodeDir(weakest.getDirection());
    }
    msg <<= 15;

    msg += rc.getHealth();

    msg += (rc.getDirection().getDirectionOrderNum()-1)<<12;

    msg = -msg;
    if (!hasSqueaked) {
        rc.squeak(msg);
        hasSqueaked = true;
    }
}
vector<AdditionalClasses::Threat> Comms::readThreats() {
    int sz = 0;
    for (const Message& m : newestSqueaks) if (m.getBytes() <= -1) {
        sz += 2;
    }
    vector<AdditionalClasses::Threat> threats(sz);
    int ptr = 0;
    for (const Message& m : newestSqueaks) if (m.getBytes() <= -1) {
        int msg = -m.getBytes();
        // strongest first
        Direction dir = decodeDir(msg & 0b111);
        msg = msg >> 3;
        int x, y;
        y = (msg & 0b111111);
        msg = msg >> 6;
        x = (msg & 0b111111);
        msg = msg >> 6;
        threats[ptr++] = AdditionalClasses::Threat(MapLocation(x, y), dir, true);
        // weakest second
        dir = decodeDir(msg & 0b111);
        msg = msg >> 3;
        y = (msg & 0b111111);
        msg = msg >> 6;
        x = (msg & 0b111111);
        threats[ptr++] = AdditionalClasses::Threat(MapLocation(x, y), dir, false);
    }
    return threats;
}
void Comms::alertHunters(RobotInfo cat) {
    if (cat.getType() != UnitType::CAT) return;
    rc.writeSharedArray(62, cat.getID()%1024);
}
void Comms::updatePreyLoc(MapLocation loc) {
    int msg = (1 << 27) + (loc.x << 6) + loc.y;
    if (!hasSqueaked) {
        rc.squeak(msg);
        hasSqueaked = true;
    }
}
MapLocation Comms::getPreyLoc() {
    for (const Message& m : newestSqueaks) if (m.getBytes() > 0) {
        int msg = m.getBytes();
        if ((msg&(1 << 27)) > 0) {
            int x, y;
            y = msg&0b111111;
            msg = msg >> 6;
            x = msg&0b111111;
            return MapLocation(x, y);
        }
    }
    return MapLocation(-1, -1);
}

void Comms::squeakEnemyKing(MapLocation loc) {
    int msg = (1 << 25) + (loc.x << 6) + loc.y;
    if (!hasSqueaked) {
        rc.squeak(msg);
        hasSqueaked = true;
    }
}

MapLocation Comms::getEnemyKing() {
    for (const Message& m : newestSqueaks) if (m.getBytes() > 0) {
        int msg = m.getBytes();
        if ((msg&(1 << 25)) > 0) {
            int x, y;
            y = msg&0b111111;
            msg = msg >> 6;
            x = msg&0b111111;
            return MapLocation(x, y);
        }
    }
    return MapLocation::NONE;
}

void Comms::squeakNewKing(MapLocation mine) {
    int msg = (1 << 28) + (mine.x<<6) + mine.y;
    if (!hasSqueaked) {
        rc.squeak(msg);
        hasSqueaked = true;
    }
}
MapLocation Comms::checkForNewKings() {
    for (const Message& m : newestSqueaks) if (m.getBytes() > 0) {
        int msg = m.getBytes();
        if ((msg&(1 << 28)) > 0) {
            int x, y;
            y = msg&0b111111;
            msg = msg >> 6;
            x = msg&0b111111;
            return MapLocation(x, y);
        }
    }
    return MapLocation::NONE;
}

void Comms::encodeNewKingPos(MapLocation mine) {
    rc.writeSharedArray(57, 0);
    rc.writeSharedArray(58, mine.x+1);
    rc.writeSharedArray(59, mine.y+1);
}

void Comms::clearNewKing() {
    rc.writeSharedArray(58, 0);
}

int Comms::getNumberBots() {
    return rc.readSharedArray(57);
}

void Comms::incNewKingBotCount(int cur) {
    rc.writeSharedArray(57, std::min(cur+1, 20));
}

MapLocation Comms::needNewKing() {
    int x = rc.readSharedArray(58), y = rc.readSharedArray(59);
    return x > 0 ? MapLocation(x-1, y-1) : MapLocation::NONE;
}


void Comms::beingThrown() {
    if (!hasSqueaked){
        rc.squeak(7 + locationLastRound.directionTo(rc.getLocation()).getDirectionOrderNum());
    }
    hasSqueaked = true;
}
vector<AdditionalClasses::Thrown> Comms::getAlliesThrown() {
    int sz = 0;
    for (const Message& msg : newestSqueaks) if (8 <= msg.getBytes() && msg.getBytes() < 16)
        sz++;
    vector<AdditionalClasses::Thrown> ret(sz);
    sz = 0;
    for (const Message& msg : newestSqueaks) if (8 <= msg.getBytes() && msg.getBytes() < 16) {
        // TODO: FINISH THIS ONCE THE STUFF IS ANSWERED IN #BUG REPORTS
        ret[sz++] = AdditionalClasses::Thrown(rc.getLocation(), rc.getDirection());
    }
    return ret;
}

void Comms::squeakForSacrifices(MapLocation loc) {
    int msg = (1 << 24) + (loc.x << 6) + loc.y;
    if (!hasSqueaked) {
        rc.squeak(msg);
        hasSqueaked = true;
    }
}


void Comms::squeakForSacrificesToo(MapLocation loc) {
    int msg = (1 << 29) + (loc.x << 6) + loc.y;
    if (!hasSqueaked) {
        rc.squeak(msg);
        hasSqueaked = true;
    }
}

MapLocation Comms::getSacrifices() {
    MapLocation secondary = MapLocation::NONE;
    for (const Message& m : newestSqueaks) if (m.getBytes() > 0) {
        int msg = m.getBytes();
        if ((msg&(1 << 24)) > 0) {
            int x, y;
            y = msg&0b111111;
            msg = msg >> 6;
            x = msg&0b111111;
            return MapLocation(x, y);
        }
        if ((msg&(1 << 29)) > 0) {
            int x, y;
            y = msg&0b111111;
            msg = msg >> 6;
            x = msg&0b111111;
            secondary = MapLocation(x+1000, y+1000);
        }
    }
    return secondary;
}

}  // namespace Utils
