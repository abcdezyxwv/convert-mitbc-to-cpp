#pragma once
#include "api.hpp"

namespace philip_06 {
namespace utils {

// philip_06.utils.Random - a custom xorshift RNG, NOT java.util.Random.
// Instantiated (non-static) class; Constants::rng holds one by value.
struct Random {
    int64_t seed;

    explicit Random(int64_t seed) : seed(seed) {}

    int nextInt() {
        seed ^= (int64_t)((uint64_t)seed << 21);
        seed ^= (int64_t)((uint64_t)seed >> 35);  // Java >>> (logical shift)
        seed ^= (int64_t)((uint64_t)seed << 4);
        return (int)(seed & 0x7FFFFFFF);
    }

    bool nextBoolean() { return nextInt() % 2 == 0; }
};

}  // namespace utils
}  // namespace philip_06
