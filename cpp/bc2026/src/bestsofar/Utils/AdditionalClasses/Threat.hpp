#pragma once
#include "api.hpp"

namespace Utils {
namespace AdditionalClasses {

// NOTE: the Java declares these fields `static` (arguably a bug - every Threat
// shares one loc/dir/threat). Kept `static` to mirror the Java semantics
// exactly; `t.loc` / `t.dir` still work on instances.
struct Threat {
    static MapLocation loc;
    static Direction dir;
    static bool threat;

    Threat() = default;
    Threat(MapLocation m, Direction d, bool t) {
        loc = m;
        dir = d;
        threat = t;
    }
};

}  // namespace AdditionalClasses
}  // namespace Utils
