#pragma once
#include "api.hpp"

namespace philip_06 {
namespace utils {

struct Settings {
    static int defendRounds;             // 100
    static int defendAfterRound;         // 500
    static int startingSoldiers;         // 2  (per tower)
    static int startingSplashers;        // 0  (per tower)
    static int startingMoppers;          // 0  (per tower)
    static int lowPaint;                 // 30
    static int minTowerPaintToTransfer;  // 100
    static int rushDistanceSquared;      // 100
};

}  // namespace utils
}  // namespace philip_06
