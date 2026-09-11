#include "Pathfind.hpp"
#include "RobotPlayer.hpp"

int Pathfind::turnDir = -1;
Direction Pathfind::exploreDirection = Direction::all[Direction::NORTH];
const Direction Pathfind::directions[8] = {
    Direction::all[Direction::NORTH],     Direction::all[Direction::NORTHEAST],
    Direction::all[Direction::EAST],      Direction::all[Direction::SOUTHEAST],
    Direction::all[Direction::SOUTH],     Direction::all[Direction::SOUTHWEST],
    Direction::all[Direction::WEST],      Direction::all[Direction::NORTHWEST],
};

int Pathfind::bugState = 0;
MapLocation Pathfind::closestObstacle;
int Pathfind::closestObstacleDist = 99999;
Direction Pathfind::pathDir;
MapLocation Pathfind::prevDest;
std::unordered_set<MapLocation> Pathfind::destLine;
int Pathfind::obstacleStartDist = 0;

void Pathfind::resetVar() {
    bugState = 0;
    closestObstacle = MapLocation::NONE;
    closestObstacleDist = 99999;
    pathDir = Direction::all[Direction::CENTER];
}

std::unordered_set<MapLocation> Pathfind::createLine(MapLocation a, MapLocation b) {
    std::unordered_set<MapLocation> locs;
    int x = a.x, y = a.y;
    int dx = b.x - a.x;
    int dy = b.y - a.y;
    int sx = signum(dx);
    int sy = signum(dy);
    dx = std::abs(dx);
    dy = std::abs(dy);
    int d = std::max(dx, dy);
    int r = d / 2;
    if (dx > dy) {
        for (int i = 0; i < d; i++) {
            locs.insert(MapLocation(x, y));
            x += sx;
            r += dy;
            if (r >= dx) {
                locs.insert(MapLocation(x, y));
                y += sy;
                r -= dx;
            }
        }
    } else {
        for (int i = 0; i < d; i++) {
            locs.insert(MapLocation(x, y));
            y += sy;
            r += dx;
            if (r >= dy) {
                locs.insert(MapLocation(x, y));
                x += sx;
                r -= dy;
            }
        }
    }
    locs.insert(MapLocation(x, y));
    return locs;
}

void Pathfind::moveTowardsV1(RobotController& rc, MapLocation loc) {
    if (turnDir < 0) turnDir = RobotPlayer::rng.nextInt(2);
    Direction dir = rc.getLocation().directionTo(loc);
    if (turnDir == 1) {
        int attempts = 0;
        while (attempts < 8) {
            attempts++;
            MapLocation ahead = rc.getLocation().add(dir);
            if (rc.canFill(ahead)) rc.fill(ahead);
            if (rc.canMove(dir)) {
                rc.move(dir);
                break;
            }
            dir = dir.rotateLeft();
        }
    } else {
        int attempts = 0;
        while (attempts < 8) {
            attempts++;
            MapLocation ahead = rc.getLocation().add(dir);
            if (rc.canFill(ahead)) rc.fill(ahead);
            if (rc.canMove(dir)) {
                rc.move(dir);
                break;
            }
            dir = dir.rotateRight();
        }
    }
}

void Pathfind::moveTowardsV2(RobotController& rc, MapLocation loc) {
    if (bugState == 0) {
        pathDir = rc.getLocation().directionTo(loc);
        MapLocation ahead = rc.getLocation().add(pathDir);
        if (rc.canFill(ahead)) rc.fill(ahead);
        if (rc.canMove(pathDir)) {
            rc.move(pathDir);
        } else {
            bugState = 1;
            closestObstacle = MapLocation::NONE;
            closestObstacleDist = 99999;
        }
    } else {
        if (rc.getLocation() == closestObstacle) bugState = 0;
        if (rc.getLocation().distanceSquaredTo(loc) < closestObstacleDist) {
            closestObstacleDist = rc.getLocation().distanceSquaredTo(loc);
            closestObstacle = rc.getLocation();
        }
        for (int i = 0; i < 8; i++) {
            MapLocation ahead = rc.getLocation().add(pathDir);
            if (rc.canFill(ahead)) rc.fill(ahead);
            if (rc.canMove(pathDir)) {
                rc.move(pathDir);
                pathDir = pathDir.rotateLeft();
                pathDir = pathDir.rotateLeft();
                break;
            } else {
                pathDir = pathDir.rotateRight();
            }
        }
    }
}

void Pathfind::moveTowards(RobotController& rc, MapLocation loc) {
    if (loc != prevDest) {
        prevDest = loc;
        destLine = createLine(rc.getLocation(), loc);
    }

    for (const MapLocation& point : destLine) {
        rc.setIndicatorDot(point, 255, 0, 0);
    }

    if (bugState == 0) {
        pathDir = rc.getLocation().directionTo(loc);
        MapLocation ahead = rc.getLocation().add(pathDir);
        MapInfo toMove = rc.senseMapInfo(ahead);
        if (rc.canFill(ahead)) rc.fill(ahead);
        if (rc.canMove(pathDir)) {
            rc.move(pathDir);
        } else if (!toMove.isWater()) {
            bugState = 1;
            obstacleStartDist = rc.getLocation().distanceSquaredTo(loc);
        }
    } else {
        if (destLine.count(rc.getLocation()) &&
            rc.getLocation().distanceSquaredTo(loc) < obstacleStartDist) {
            bugState = 0;
            return;
        }
        for (int i = 0; i < 8; i++) {
            MapLocation ahead = rc.getLocation().add(pathDir);
            if (rc.canFill(ahead)) rc.fill(ahead);
            if (rc.canMove(pathDir)) {
                rc.move(pathDir);
                pathDir = pathDir.rotateLeft();
                break;
            } else {
                pathDir = pathDir.rotateRight();
            }
        }
    }
}

void Pathfind::explore(RobotController& rc) {
    vector<MapLocation> crumbs = rc.senseNearbyCrumbs(-1);
    MapLocation target;
    int bestDist = 99999;

    for (const MapLocation& crumb : crumbs) {
        if (rc.getLocation().distanceSquaredTo(crumb) < bestDist) {
            target = crumb;
            bestDist = rc.getLocation().distanceSquaredTo(crumb);
        }
    }

    if (!target.isNull()) {
        moveTowards(rc, target);
    } else {
        if (rc.isMovementReady()) {
            MapLocation ahead = rc.getLocation().add(exploreDirection);
            if (rc.canFill(ahead)) rc.fill(ahead);
            if (rc.canMove(exploreDirection) && RobotPlayer::rng.nextInt(50) != 0) {
                rc.move(exploreDirection);
            } else {
                exploreDirection = Direction::all[RobotPlayer::rng.nextInt(8)];
            }
        }
    }
}
