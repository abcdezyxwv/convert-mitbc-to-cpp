#pragma once
#include "../../api.hpp"

struct Bit {
    static bool get(int intRepresentation, int position) {
        return (intRepresentation & (1 << position)) != 0;
    }

    // Same result as the Java version but O(1) instead of looping all 16 bits.
    static int16_t write(int16_t intRepresentation, int position, bool value) {
        return (int16_t)((intRepresentation & ~(1 << position)) | ((int)value << position));
    }
};
