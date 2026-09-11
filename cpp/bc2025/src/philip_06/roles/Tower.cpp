#include "roles/Tower.hpp"

#include <algorithm>

#include "Helper/Comms.hpp"
#include "RobotPlayer.hpp"
#include "utils/Actions.hpp"

namespace philip_06 {
namespace roles {

using philip_06::Helper::Comms;
using philip_06::utils::Actions;

std::deque<std::pair<UnitType, MapLocation>> Tower::toSpawn;
MapLocation Tower::target;  // Java: null
int Tower::targetRound = 0;

void Tower::run(RobotController rc) {
    bool hasMopper = false;
    bool hasSplasher = false;
    int noEnemyPaint = 0;
    for (const RobotInfo& bot : rc.senseNearbyRobots(-1, rc.getTeam())) {
        if (bot.getType() == UnitType::MOPPER)
            hasMopper = true;
        if (bot.getType() == UnitType::SPLASHER)
            hasSplasher = true;
    }
    for (const MapInfo& loc : rc.senseNearbyMapInfos(-1)) {
        if (isEnemy(loc.getPaint())) {
            noEnemyPaint++;
        }
    }
    if (!hasMopper && !hasSplasher && noEnemyPaint > 0) {
        Actions::spawn(rc, UnitType::MOPPER, MapLocation(61, 61));
    }
    // add new spawn stuff
    if (RobotPlayer::aliveTurns == 1 && rc.getRoundNum() < 50) {
 //           if(rc.getMapHeight()*rc.getMapWidth()<=1500 && rc.getType()==UnitType.LEVEL_TWO_MONEY_TOWER)
   //             toSpawn.add(Map.entry(UnitType.SPLASHER, new MapLocation(61, 61)));
     //       else
        toSpawn.push_back(std::pair<UnitType, MapLocation>(UnitType::SOLDIER, MapLocation(61, 61)));
        toSpawn.push_back(std::pair<UnitType, MapLocation>(UnitType::SOLDIER, MapLocation(61, 61)));
    }
    if (rc.getRoundNum() - targetRound > 100) {
        target = MapLocation::NONE;
    }
    Comms::getMsg(rc);
    Comms::sendMsg(rc);
    if (!target.isNull()) { rc.setIndicatorLine(rc.getLocation(), target, 0, 0, 0); }

    if (!target.isNull()) {
        for (const RobotInfo& loc : rc.senseNearbyRobots(-1, rc.getTeam())) {
            if (rc.canSendMessage(loc.location)) {
                rc.sendMessage(loc.location, Comms::encodeLocation(target));
            }
        }
    }
    // get spawn rates of current round
    SpawnRateChange s;
    if (rc.getRoundNum() < 30)
        s = SpawnRateChange(1, 0, 0);
    else if (rc.getRoundNum() < 60)
        s = SpawnRateChange(1, 0, 1);
    else if (rc.getRoundNum() < (rc.getMapWidth() + rc.getMapWidth()))
        s = SpawnRateChange(3, 0, 2);
    else if (rc.getRoundNum() < 3 * (rc.getMapWidth() + rc.getMapWidth()))
        s = SpawnRateChange(3, 0, 1);
    else
        s = SpawnRateChange(2, 3, 2);
    rc.setIndicatorString("Spawning with priorities: " + std::to_string(s.soldierPrty) + ", " +
                          std::to_string(s.splasherPrty) + ", " + std::to_string(s.mopperPrty));
    if (rc.getMoney() > 1100 && rc.getPaint() > 300 && toSpawn.empty()) {  // extra spawn
        int r = RobotPlayer::rng.nextInt(s.soldierPrty + s.splasherPrty + s.mopperPrty);
        if (r < s.soldierPrty)
            toSpawn.push_back(std::pair<UnitType, MapLocation>(UnitType::SOLDIER, MapLocation(61, 61)));
        else if (r < s.splasherPrty + s.soldierPrty)
            toSpawn.push_back(std::pair<UnitType, MapLocation>(UnitType::SPLASHER, MapLocation(61, 61)));
        else
            toSpawn.push_back(std::pair<UnitType, MapLocation>(UnitType::MOPPER, MapLocation(61, 61)));
    }
    // spawn stuff
    while (!toSpawn.empty() && Actions::spawn(rc, toSpawn.front().first, toSpawn.front().second)) {
        toSpawn.pop_front();
    }
    // upgrade self
    if (((rc.getType() == UnitType::LEVEL_ONE_PAINT_TOWER) ||
         (rc.getMoney() > 6000 && rc.getType() == UnitType::LEVEL_TWO_PAINT_TOWER)) &&
        rc.canUpgradeTower(rc.getLocation()) &&
        (rc.getMoney() > 4000 || ((int)rc.senseNearbyRobots(-1, rc.getTeam()).size() >= 4))) {
        rc.upgradeTower(rc.getLocation());
    }
    if ((int)rc.senseNearbyRobots(-1, opponent(rc.getTeam())).size() > 3) {
        if (getBaseType(rc.getType()) == UnitType::LEVEL_ONE_DEFENSE_TOWER &&
            rc.canUpgradeTower(rc.getLocation()) && rc.getMoney() > 2000) {
            rc.upgradeTower(rc.getLocation());
        }
    }
    if (rc.getMoney() > 6000 && rc.canUpgradeTower(rc.getLocation())) {
        rc.upgradeTower(rc.getLocation());
    }
    // Attack enemies
    int damage = 0;
    int snipe = 0;
    MapLocation todo;  // Java: null
    vector<RobotInfo> locs = rc.senseNearbyRobots(9);
    for (const RobotInfo& loc : locs) if (loc.getTeam() != rc.getTeam() && rc.canAttack(loc.getLocation())) {
        // Single shot
        damage += std::min(loc.getHealth(), aoeAttackStrength(rc.getType()));
        if (std::min(loc.getHealth(), attackStrength(rc.getType())) > snipe) {
            snipe = std::min(loc.getHealth(), attackStrength(rc.getType()));
            todo = loc.getLocation();
        }
    }
    (void)damage;  // Java: accumulated but unused
    if (!todo.isNull() && rc.canAttack(todo)) rc.attack(todo);
    if (rc.canAttack(MapLocation::NONE)) rc.attack(MapLocation::NONE);  // Java: rc.canAttack(null)
}

}  // namespace roles
}  // namespace philip_06
