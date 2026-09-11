#include "RobotPlayer.hpp"

#include <iostream>

#include "Baby.hpp"
#include "King.hpp"
#include "Utils/Globals.hpp"

void RobotPlayer::run(RobotController rc) {
    Utils::Globals::init(rc);

    while (true) {
        try {
            Utils::Globals::startTurn();

            switch (rc.getType()) {
                case UnitType::BABY_RAT:
                    Baby::run();
                    break;

                case UnitType::RAT_KING:
                    King::run();
                    break;

                default:
                    break;
            }

            Utils::Globals::endTurn();

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
