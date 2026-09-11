#include "utils/Actions.hpp"
#include "utils/Constants.hpp"
#include "RobotPlayer.hpp"
#include "Helper/Comms.hpp"
#include "roles/Mopper.hpp"
#include "roles/Tower.hpp"

namespace philip_06 {
namespace utils {

std::unordered_map<MapLocation, int> Actions::badRuins;

bool Actions::spawn(RobotController rc, UnitType type, MapLocation dest) {
    // RobotPlayer::rng is api.hpp's ::Random, which has no nextBoolean();
    // java.util.Random.nextBoolean() is `next(1) != 0`, i.e. a fair coin, so
    // `nextInt(2) != 0` is the faithful stand-in (the RNG stream already
    // differs from java.util.Random's - see CONVENTIONS.md).
    if (dest == MapLocation(61, 61) && !roles::Tower::target.isNull() &&
        RobotPlayer::rng.nextInt(2) != 0)
        dest = roles::Tower::target;
    for (const Direction& dir : Direction::allDirections()) {
        if (rc.canBuildRobot(type, rc.getLocation().add(dir))) {
            rc.buildRobot(type, rc.getLocation().add(dir));
            if (rc.canSendMessage(rc.getLocation().add(dir))) {
                rc.sendMessage(rc.getLocation().add(dir), Helper::Comms::encodeLocation(dest));
            }
            return true;
        }
    }
    return false;
}

void Actions::makeTower(RobotController rc, MapLocation ruin) {
    if (ruin.isNull()) return;
    if (rc.getNumberTowers() == GameConstants::MAX_NUMBER_OF_TOWERS) return;
    if (badRuins.count(ruin)) {
        if (rc.getRoundNum() - badRuins.at(ruin) < 10)
            return;
        else
            badRuins.erase(ruin);
    }
    if (rc.getLocation().distanceSquaredTo(ruin) > 9) {
        roles::Mopper::moveTowardsMindlessly(rc, ruin);
        return;
    }
    // Java `UnitType type = null;` - UnitType is an enum class here, so the
    // null state is tracked by a companion flag; `type` is only read once
    // typeIsNull is false.
    UnitType type = UnitType::SOLDIER;
    bool typeIsNull = true;
    if (isAlly(rc.senseMapInfo(ruin.add(Direction::all[Direction::NORTH])).getMark())) {
        type = UnitType::LEVEL_ONE_PAINT_TOWER;
        typeIsNull = false;
    } else if (isAlly(rc.senseMapInfo(ruin.add(Direction::all[Direction::EAST])).getMark())) {
        type = UnitType::LEVEL_ONE_MONEY_TOWER;
        typeIsNull = false;
    } else if (isAlly(rc.senseMapInfo(ruin.add(Direction::all[Direction::SOUTH])).getMark())) {
        type = UnitType::LEVEL_ONE_DEFENSE_TOWER;
        typeIsNull = false;
    }
    if (typeIsNull) {
        if (RobotPlayer::rng.nextInt(3) == 1 || rc.getMoney() > 5000) {
            type = UnitType::LEVEL_ONE_PAINT_TOWER;
            if (rc.canMark(ruin.add(Direction::all[Direction::NORTH])))
                rc.mark(ruin.add(Direction::all[Direction::NORTH]), false);
        } else {
            type = UnitType::LEVEL_ONE_MONEY_TOWER;
            if (rc.canMark(ruin.add(Direction::all[Direction::EAST])))
                rc.mark(ruin.add(Direction::all[Direction::EAST]), false);
        }
    }
    MapLocation best = MapLocation::NONE;
    int _cost = 0;
    bool _colour = false;
    vector<vector<bool>> arr = rc.getTowerPattern(type);
    for (int i = -2; i <= 2; i++) {
        for (int j = -2; j <= 2; j++) {
            if (i == 0 && j == 0) continue;
            if (rc.canSenseLocation(ruin.translate(i, j))) {
                PaintType cur = rc.senseMapInfo(ruin.translate(i, j)).getPaint();
                if (cur == PaintType::EMPTY ||
                    (cur == PaintType::ALLY_PRIMARY && arr[i + 2][j + 2]) ||
                    (cur == PaintType::ALLY_SECONDARY && !arr[i + 2][j + 2])) {
                    _cost++;
                    if (best.isNull() || rc.getLocation().distanceSquaredTo(best) >
                                             rc.getLocation().distanceSquaredTo(ruin.translate(i, j))) {
                        best = ruin.translate(i, j);
                        _colour = arr[i + 2][j + 2];
                    }
                } else if (cur == PaintType::ENEMY_PRIMARY || cur == PaintType::ENEMY_SECONDARY) {
                    _cost = 1000000;
                }
            }
        }
    }
    if (_cost >= 25) {
        badRuins[ruin] = rc.getRoundNum();
    } else if (!best.isNull()) {
        rc.setIndicatorDot(best, 255, 0, 0);
        if (rc.canAttack(best))
            rc.attack(best, _colour);
    }
    if (rc.senseNearbyRobots(ruin, rc.getLocation().distanceSquaredTo(ruin), rc.getTeam())
            .empty()) {
        if (!best.isNull() && rc.getLocation().distanceSquaredTo(best) > 9)
            roles::Mopper::moveTowardsMindlessly(rc, best);
        else
            roles::Mopper::moveTowardsMindlessly(rc, ruin);
    }
    if (rc.canCompleteTowerPattern(type, ruin))
        rc.completeTowerPattern(type, ruin);
}

void Actions::getPaint(RobotController rc) {
    if (rc.getHealth() <= 40) return;
    for (const MapLocation& loc : rc.senseNearbyRuins(-1)) {
        RobotInfo bot = rc.senseRobotAtLocation(loc);
        // RobotInfo has no NONE sentinel in api.hpp; a default RobotInfo's
        // location is MapLocation::NONE, used here as the null proxy.
        if (bot.getLocation().isNull()) continue;
        if (rc.canTransferPaint(
                loc, -std::min(Constants::paintCapacity(rc.getType()) - rc.getPaint(),
                               bot.paintAmount)))
            rc.transferPaint(loc, -std::min(Constants::paintCapacity(rc.getType()) - rc.getPaint(),
                                            bot.paintAmount));
    }
}

}  // namespace utils
}  // namespace philip_06
