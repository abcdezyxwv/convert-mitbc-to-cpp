# Port of reechee/Bit.java. See py/CONVENTIONS.md.


class Bit:
    @staticmethod
    def get(intRepresentation, position):
        return (intRepresentation & (1 << position)) != 0

    @staticmethod
    def write(intRepresentation, position, value):
        # Same result as the Java version but O(1) instead of looping all 16 bits.
        return (intRepresentation & ~(1 << position)) | (int(value) << position)
