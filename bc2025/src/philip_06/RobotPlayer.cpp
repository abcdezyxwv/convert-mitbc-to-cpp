#include "RobotPlayer.hpp"
#include "Soldier.hpp"
#include "SoldierState/Build.hpp"
#include "roles/Mopper.hpp"
#include "roles/Splasher.hpp"
#include "roles/Tower.hpp"
#include "utils/Constants.hpp"
#include <iostream>

namespace philip_06 {

Random RobotPlayer::rng;  // Java: = null (java.util.Random -> api.hpp Random)
bool RobotPlayer::rush = false;
bool RobotPlayer::fill = false;
bool RobotPlayer::retreat = false;
bool RobotPlayer::build = false;
bool RobotPlayer::built = false;
int RobotPlayer::aliveTurns = 0;
int RobotPlayer::lastSeenEnemy = 0;
MapLocation RobotPlayer::lastEnemyTower;

void RobotPlayer::run(RobotController rc) {
    if (rc.getType() != UnitType::SOLDIER && rc.getType() != UnitType::MOPPER)
        utils::Constants::setup(rc);
    // Java: if (rng == null) rng = new Random(rc.getID()^6969);  (no null state in C++)
    rng = Random(rc.getID() ^ 6969);
    roles::Mopper::pastLocs = vector<MapLocation>();
    lastSeenEnemy = rc.getRoundNum();
    while (true) {
        if (rc.senseNearbyRobots(-1, opponent(rc.getTeam())).size() > 0)
            lastSeenEnemy = rc.getRoundNum();
        aliveTurns++;
        int valid = 0;
        for (const MapLocation& ruin : rc.senseNearbyRuins(-1)) {
            if (rc.senseRobotAtLocation(ruin).getLocation().isNull()) {
                valid++;
                break;
            } else if (rc.senseRobotAtLocation(ruin).getTeam() == rc.getTeam()) {
                if (rc.canSenseLocation(ruin.add(Direction::all[Direction::SOUTH])) &&
                    rc.canRemoveMark(ruin.add(Direction::all[Direction::SOUTH]))) {
                    rc.removeMark(ruin.add(Direction::all[Direction::SOUTH]));
                }
            }
        }
        if (valid == 0) {
            for (const MapInfo& loc : rc.senseNearbyMapInfos(8))
                if (loc.hasRuin() || loc.isWall()) valid++;
            // Now consider conflict between other SRPs
            for (const MapInfo& loc : rc.senseNearbyMapInfos()) {
                if (isSecondary(loc.getMark())) {
                    if (!rc.canSenseLocation(loc.getMapLocation().add(Direction::all[Direction::NORTH])) ||
                        (rc.canSenseLocation(loc.getMapLocation().add(Direction::all[Direction::NORTH])) &&
                         !rc.senseMapInfo(loc.getMapLocation().add(Direction::all[Direction::NORTH])).hasRuin()))
                        if (loc.getMapLocation().distanceSquaredTo(rc.getLocation()) != 16) valid++;
                }
            }
        }
        // Check that there is actually enough space
        if (valid == 0 && rc.canMark(rc.getLocation())) {
            if (rc.getLocation().x > 1 && rc.getLocation().x < rc.getMapWidth() - 2) {
                if (rc.getLocation().y > 1 && rc.getLocation().y < rc.getMapHeight() - 2) {
                    rc.mark(rc.getLocation(), true);
                }
            }
        }
        for (const MapInfo& loc : rc.senseNearbyMapInfos()) {
            if (loc.hasRuin()) {
                if (rc.canCompleteTowerPattern(UnitType::LEVEL_ONE_PAINT_TOWER, loc.getMapLocation())) {
                    if (rc.getType() == UnitType::SOLDIER && SoldierState::Build::movingTowardsToFinish &&
                        SoldierState::Build::toFinish.back() == loc.getMapLocation()) {
                        SoldierState::Build::toFinish.pop_back();
                        SoldierState::Build::movingTowardsToFinish = false;
                    }
                    rc.completeTowerPattern(UnitType::LEVEL_ONE_PAINT_TOWER, loc.getMapLocation());
                    built = true;
                }
                if (rc.canCompleteTowerPattern(UnitType::LEVEL_ONE_MONEY_TOWER, loc.getMapLocation())) {
                    if (rc.getType() == UnitType::SOLDIER && SoldierState::Build::movingTowardsToFinish &&
                        SoldierState::Build::toFinish.back() == loc.getMapLocation()) {
                        SoldierState::Build::toFinish.pop_back();
                        SoldierState::Build::movingTowardsToFinish = false;
                    }
                    rc.completeTowerPattern(UnitType::LEVEL_ONE_MONEY_TOWER, loc.getMapLocation());
                    built = true;
                }
                if (rc.canCompleteTowerPattern(UnitType::LEVEL_ONE_DEFENSE_TOWER, loc.getMapLocation())) {
                    if (rc.getType() == UnitType::SOLDIER && SoldierState::Build::movingTowardsToFinish &&
                        SoldierState::Build::toFinish.back() == loc.getMapLocation()) {
                        SoldierState::Build::toFinish.pop_back();
                        SoldierState::Build::movingTowardsToFinish = false;
                    }
                    rc.completeTowerPattern(UnitType::LEVEL_ONE_DEFENSE_TOWER, loc.getMapLocation());
                    built = true;
                }
            }
            if (isAlly(loc.getMark()) && isSecondary(loc.getMark())) {
                if (rc.canCompleteResourcePattern(loc.getMapLocation())) {
                    rc.completeResourcePattern(loc.getMapLocation());
                }
            }
        }
        try {
            switch (rc.getType()) {
                case UnitType::SOLDIER: Soldier::run(rc); break;
                case UnitType::MOPPER: roles::Mopper::run(rc); break;
                case UnitType::SPLASHER: roles::Splasher::run(rc); break;
                default: roles::Tower::run(rc); break;
            }
            Clock::yield();
        } catch (const GameActionException& e) {
            std::cout << "GameActionException" << '\n';
            std::cout << e.what() << '\n';
        } catch (const std::exception& e) {
            std::cout << "Exception" << '\n';
            std::cout << e.what() << '\n';
        }
    }
}

}  // namespace philip_06
