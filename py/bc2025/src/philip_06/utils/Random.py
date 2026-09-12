# Port of philip_06/utils/Random.java. See py/CONVENTIONS.md.
# philip_06.utils.Random is a tiny instance class (a 3-shift xorshift on a
# 64-bit seed) - NOT java.util.Random. Constants.rng is an instance of this.
from api import *

_MASK64 = 0xFFFFFFFFFFFFFFFF


class Random:
    def __init__(self, seed):
        self.seed = seed & _MASK64  # Java long

    def nextInt(self):
        # Java: seed ^= (seed << 21);  seed ^= (seed >>> 35);  seed ^= (seed << 4)
        # Java long arithmetic wraps at 64 bits; >>> is a logical right shift
        # (Python >> on a non-negative value is the same once masked).
        self.seed = (self.seed ^ ((self.seed << 21) & _MASK64)) & _MASK64
        self.seed = (self.seed ^ (self.seed >> 35)) & _MASK64
        self.seed = (self.seed ^ ((self.seed << 4) & _MASK64)) & _MASK64
        return self.seed & 0x7FFFFFFF

    def nextBoolean(self):
        # nextInt() is always non-negative, so % 2 matches Java exactly.
        return self.nextInt() % 2 == 0
