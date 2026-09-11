#include "utils/Random.hpp"

namespace philip_06 {
namespace utils {

// philip_06.utils.Random is a tiny instance class (a 3-shift xorshift on a
// 64-bit seed). Both of its methods are one-liners that sit on the hot path
// (Constants::rng is queried every turn), so the bodies stay inline in
// Random.hpp per the performance rules in CONVENTIONS.md; this translation
// unit exists to keep the one-Java-file -> one-.hpp/.cpp-pair mapping and to
// compile-check the header on its own.
//
// Java semantics preserved in the header:
//   seed ^= (seed << 21);   ->  unsigned shift-left on the 64-bit seed
//   seed ^= (seed >>> 35);  ->  Java logical right shift, so the cast to
//                               uint64_t is required (C++ >> on a negative
//                               int64_t is arithmetic)
//   seed ^= (seed << 4);
//   return (int)(seed & 0x7FFFFFFF);  -> always non-negative, which is why
//                               nextBoolean()'s `% 2 == 0` needs no
//                               negative-remainder handling.
static_assert(sizeof(Random) == sizeof(int64_t), "Random is just its seed");

}  // namespace utils
}  // namespace philip_06
