#include "Soldier.hpp"

#include <algorithm>

#include "Helper/Comms.hpp"
#include "RobotPlayer.hpp"
#include "SoldierState/Attack.hpp"
#include "SoldierState/Build.hpp"
#include "SoldierState/Fill.hpp"
#include "SoldierState/Retreat.hpp"
#include "roles/Mopper.hpp"

namespace philip_06 {

using Helper::Comms;
using roles::Mopper;
using SoldierState::Attack;
using SoldierState::Build;
using SoldierState::Fill;
using SoldierState::Retreat;

bool Soldier::builder = false;
int Soldier::turnsAlive = 0;
MapLocation Soldier::spawn;  // Java: null
std::unordered_set<MapLocation> Soldier::paintTowers;
vector<MapLocation> Soldier::ruins;
bool Soldier::messenger = false;
MapLocation Soldier::messageLoc;  // Java: null
int Soldier::priority = 0, Soldier::roundNum = 0;
int Soldier::message = 0;
int Soldier::moneyLastTurn = 0;
bool Soldier::defaultFill = false;
MapLocation Soldier::attack;  // Java: null

void Soldier::retreat(RobotController rc) {
    MapLocation bestOpt = MapLocation::NONE;
    for (const MapLocation& curr : paintTowers) {
        if (bestOpt.isNull() ||
            (rc.getLocation().distanceSquaredTo(curr) <
                 rc.getLocation().distanceSquaredTo(bestOpt) &&
             (!rc.canSenseLocation(bestOpt) ||
              !rc.senseRobotAtLocation(bestOpt).location.isNull()))) {
            bestOpt = curr;
        }
    }
    if (bestOpt.isNull()) {
        bestOpt = MapLocation(RobotPlayer::rng.nextInt(rc.getMapWidth()),
                              RobotPlayer::rng.nextInt(rc.getMapHeight()));
        roles::Mopper::moveTowardsMindfully(rc, bestOpt);
        return;
    }
    int transfer = paintCapacityOf(rc.getType()) - rc.getPaint();
    if (rc.canSenseLocation(bestOpt) && !rc.senseRobotAtLocation(bestOpt).location.isNull()) {
        transfer = std::min(transfer, rc.senseRobotAtLocation(bestOpt).getPaintAmount());
        // rc.setIndicatorString(std::to_string(transfer));
        if (rc.canTransferPaint(bestOpt, -transfer)) rc.transferPaint(bestOpt, -transfer);
    }
    Mopper::moveTowardsMindfully(rc, bestOpt);
}

void Soldier::stealPaint(RobotController rc) {
    if (rc.getPaint() >= 180 || !rc.isActionReady()) return;
    for (const RobotInfo& ri : rc.senseNearbyRobots(2, rc.getTeam())) {
        if (ri.type != UnitType::MOPPER && ri.type != UnitType::SPLASHER &&
            ri.type != UnitType::SOLDIER) {
            if (ri.getPaintAmount() > 150) {
                int amt = std::min(ri.getPaintAmount() - 150, 200 - rc.getPaint());
                if (rc.canTransferPaint(ri.getLocation(), -amt)) {
                    rc.transferPaint(ri.getLocation(), -amt);
                    return;
                }
                bool ret = Mopper::moveTowardsMindfully(rc, ri.getLocation());
                if (!ret) return;
                if (rc.canTransferPaint(ri.getLocation(), -amt)) {
                    rc.transferPaint(ri.getLocation(), -amt);
                    return;
                }
            }
            return;
        }
    }
}

void Soldier::donatePaint(RobotController rc) {
    if (rc.getPaint() <= 60) return;
    RobotInfo lowest;  // Java: null
    for (const RobotInfo& ri : rc.senseNearbyRobots(8, rc.getTeam()))
        if (lowest.location.isNull() || ri.getPaintAmount() < lowest.getPaintAmount()) lowest = ri;
    for (const MapLocation& ml : ruins) {
        RobotInfo ri = rc.senseRobotAtLocation(ml);
        if (ri.location.isNull()) continue;
        if (ri.type == UnitType::LEVEL_ONE_PAINT_TOWER ||
            ri.type == UnitType::LEVEL_TWO_PAINT_TOWER ||
            ri.type == UnitType::LEVEL_THREE_PAINT_TOWER) {
            if (ri.getPaintAmount() <= 600)
                if (lowest.location.isNull() || isRobotType(lowest.getType())) lowest = ri;
        }
    }
    if (lowest.location.isNull()) return;
    if (lowest.type == UnitType::SPLASHER && lowest.getPaintAmount() >= 240) return;
    if (lowest.type == UnitType::MOPPER && lowest.getPaintAmount() >= 45) return;
    if (lowest.type == UnitType::SOLDIER && lowest.getPaintAmount() >= 120) return;
    int amt;
    if (lowest.type == UnitType::SPLASHER)
        amt = std::min(300 - lowest.getPaintAmount(), rc.getPaint() - 40);
    else if (lowest.type == UnitType::MOPPER)
        amt = std::min(100 - lowest.getPaintAmount(), rc.getPaint() - 50);
    else if (lowest.type == UnitType::SOLDIER)
        amt = std::min(200 - lowest.getPaintAmount(), rc.getPaint() - 40);
    else
        amt = std::min(1000 - lowest.getPaintAmount(), rc.getPaint() - 50);
    if (!rc.canTransferPaint(lowest.getLocation(), amt))
        Mopper::moveTowardsMindlessly(rc, lowest.getLocation());
    if (rc.canTransferPaint(lowest.getLocation(), amt))
        rc.transferPaint(lowest.getLocation(), amt);
}

void Soldier::run(RobotController rc) {
    turnsAlive++;
    ruins = rc.senseNearbyRuins(-1);

    // Get messages
    if (rc.getHealth() <= 40)
        donatePaint(rc);
    else
        stealPaint(rc);
    Comms::getMsg(rc);
    Comms::sendMsg(rc);

    // Maintain list of paint towers
    for (const MapLocation& loc : rc.senseNearbyRuins(-1)) {
        RobotInfo tower = rc.senseRobotAtLocation(loc);
        if (tower.location.isNull() || rc.getTeam() == opponent(rc.getTeam())) {
            if (!tower.location.isNull()) RobotPlayer::lastEnemyTower = loc;
            paintTowers.erase(loc);
            continue;
        }
        if (tower.getPaintAmount() >= 150 || paintPerTurnOf(tower.getType()) > 0)
            paintTowers.insert(loc);
        else
            paintTowers.erase(loc);
    }
    // Precompute stuff when it just spawned
    if (turnsAlive == 1) {
        builder = RobotPlayer::rng.nextInt(6) == 0;
        Build::toFinish.clear();
        Build::turnAdded.clear();
        for (const RobotInfo& robot : rc.senseNearbyRobots(4)) {
            if (robot.getTeam() == rc.getTeam() && isTowerType(robot.getType())) {
                spawn = robot.getLocation();
            }
        }
        Attack::target = Attack::rotational(rc, spawn);
        MapLocation a = Attack::vertical(rc, spawn), b = Attack::horizontal(rc, spawn);
        if (Attack::target.distanceSquaredTo(a) < Attack::target.distanceSquaredTo(b)) {
            Attack::next = a;
        } else {
            Attack::next = b;
        }
        Attack::found = true;
        // See which mode it toggles to
        if (rc.getRoundNum() < std::max(100, rc.getMapWidth() + rc.getMapHeight())) {
            // Paint towers: two builders
            // Money towers: one filler one builder
            if (rc.senseRobotAtLocation(spawn).getType() == UnitType::LEVEL_ONE_MONEY_TOWER) {
                if (rc.senseRobotAtLocation(spawn).getPaintAmount() > 200) {
                    RobotPlayer::fill = true;
                }
            }
        } else {
            // 4 fillers : 1 builder
            if (RobotPlayer::rng.nextInt(5) != 3) RobotPlayer::fill = true;
        }
        if (rc.getRoundNum() <= 2 && paintTowers.empty()) defaultFill = true;
    }

    if (!attack.isNull() && !builder) {
        Attack::next = Attack::target;
        Attack::target = attack;
        RobotPlayer::rush = true;
        messenger = false;
    }

    if (!RobotPlayer::rush) {
        // See if it needs to coordinate attack
        for (const MapLocation& ruin : ruins) {
            if (canSenseRobotAtLocation(rc, ruin)) {
                RobotInfo ri = rc.senseRobotAtLocation(ruin);
                if (ri.getTeam() != rc.getTeam()) {
                    RobotPlayer::rush = true;
                    Attack::next = Attack::target;
                    Attack::target = ruin;
                    // See if it needs to be a messenger instead
                    // Calculate how many turns it can live
                    int power = rc.getPaint() / 10;
                    power = std::min(power, rc.getHealth() / (aoeAttackStrengthOf(ri.getType()) +
                                                              attackStrengthOf(ri.getType())));
                    if (power < 3) {
                        // meaningless attack
                        messenger = true;
                        messageLoc = ruin;
                        priority = 7 - scale(ruin.distanceSquaredTo(spawn), 0,
                                             rc.getMapHeight() * rc.getMapHeight() +
                                                 rc.getMapWidth() * rc.getMapWidth(),
                                             3, 7);
                        roundNum = rc.getRoundNum();
                        message = 0;
                        break;
                    }
                }
            } else {
                RobotPlayer::build = true;
            }
        }
        // See if it needs to coordinate a splasher attack
        // Prereq: > 40% sensed is enemy + > 4 enemies sensed
        // Only required when lowest hp soldier and senses less than 3 splashers
        // More important => overrides attack
        if ((int)rc.senseNearbyRobots(-1, opponent(rc.getTeam())).size() > 4) {
            int splashers = 0;
            bool req = true;
            for (const RobotInfo& splash : rc.senseNearbyRobots(-1, rc.getTeam())) {
                if (splash.getType() == UnitType::SPLASHER) {
                    splashers++;
                } else if (splash.getType() == UnitType::SOLDIER &&
                           splash.getLocation().isAdjacentTo(rc.getLocation())) {
                    if (splash.getPaintAmount() < rc.getPaint()) req = false;
                }
            }
            int enemy = 0;
            if (splashers < 3 && req) {
                for (const MapInfo& mi : rc.senseNearbyMapInfos())
                    if (isEnemy(mi.getPaint())) enemy++;
                if (enemy > 20) {
                    messenger = true;
                    messageLoc = rc.getLocation();
                    priority = 7 - scale(rc.getLocation().distanceSquaredTo(spawn), 0,
                                         rc.getMapHeight() * rc.getMapHeight() +
                                             rc.getMapWidth() * rc.getMapWidth(),
                                         1, 5);
                    roundNum = rc.getRoundNum();
                    message = 1;
                }
            }
        }
    }
    if (!Build::toFinish.empty()) {
        RobotPlayer::rush = false;
        RobotPlayer::build = true;
    }
    // Check if all towers are done lol
    if (rc.getNumberTowers() == 25) {
        RobotPlayer::fill = true;
        RobotPlayer::build = false;
    }

    RobotPlayer::retreat = !RobotPlayer::rush && rc.getPaint() < 20;

    // State machine
    if (Build::movingTowardsToFinish || Build::askForMopper) {
        Build::run(rc);
    } else if (RobotPlayer::retreat) {
        // std::cout << "Retreat" << '\n';
        // std::cout << Clock::getBytecodeNum() << '\n';
        Retreat::run(rc);
        rc.setIndicatorString("Retreating");
        // std::cout << Clock::getBytecodeNum() << '\n';
    } else if (RobotPlayer::rush) {
        // std::cout << "Rush" << '\n';
        // std::cout << Clock::getBytecodeNum() << '\n';
        Attack::run(rc);
        rc.setIndicatorString("Rushing");
        // std::cout << Clock::getBytecodeNum() << '\n';
    } else if ((RobotPlayer::fill || (defaultFill)) && !RobotPlayer::build) {
        // std::cout << "Fill" << '\n';
        // std::cout << Clock::getBytecodeNum() << '\n';
        Fill::run(rc);
        rc.setIndicatorString("Filling");
        // std::cout << Clock::getBytecodeNum() << '\n';
    } else {
        // std::cout << "Build" << '\n';
        // std::cout << Clock::getBytecodeNum() << '\n';
        Build::run(rc);
        // rc.setIndicatorString("Building");

        // std::cout << Clock::getBytecodeNum() << '\n';
    }
    moneyLastTurn = rc.getMoney();
    //    Utils::attackTowers(rc);
}

}  // namespace philip_06
