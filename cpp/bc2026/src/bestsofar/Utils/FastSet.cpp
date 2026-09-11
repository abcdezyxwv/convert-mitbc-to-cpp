#include "Utils/FastSet.hpp"

namespace Utils {

bool FastSet::add(char16_t value) {
    std::u16string str(1, value);
    if (values.find(str) == std::u16string::npos) {
        values.append(str);
        return true;
    }

    return false;
}

bool FastSet::contains(char16_t value) {
    return values.find(std::u16string(1, value)) != std::u16string::npos;
}

bool FastSet::add(MapLocation location) {
    return add(encodeLocation(location));
}

bool FastSet::contains(MapLocation location) {
    return contains(encodeLocation(location));
}

char16_t FastSet::encodeLocation(MapLocation location) {
    return (char16_t)((location.x << 6) | location.y);
}

}  // namespace Utils
