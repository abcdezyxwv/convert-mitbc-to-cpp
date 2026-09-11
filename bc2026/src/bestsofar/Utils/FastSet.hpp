#pragma once
#include <string>
#include "api.hpp"

namespace Utils {

// Java `char` is an unsigned 16-bit code unit and encodeLocation() produces
// values up to (60<<6)|60 ~ 4092, so `char16_t`/`std::u16string` are used
// instead of `char`/`std::string` to keep the StringBuilder semantics faithful
// (a signed 8-bit char would truncate and corrupt contains() checks).
struct FastSet {
private:
    std::u16string values;  // Java: private StringBuilder values

    char16_t encodeLocation(MapLocation location);  // Java: private char

public:
    bool add(char16_t value);
    bool contains(char16_t value);
    bool add(MapLocation location);
    bool contains(MapLocation location);
};

}  // namespace Utils
