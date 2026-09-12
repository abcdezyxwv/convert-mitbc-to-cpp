# Port of bestsofar/Utils/FastSet.java. See py/CONVENTIONS.md.
from api import *


class FastSet:
    def __init__(self):
        self.values = ""  # Java: private StringBuilder values

    # Java: two overloads, add(char) and add(MapLocation) - the MapLocation
    # one encodes the location and delegates to the char one.
    def add(self, value):
        if isinstance(value, MapLocation):
            return self._addChar(self.encodeLocation(value))
        return self._addChar(value)

    def _addChar(self, value):
        s = chr(value)  # Java: String str = String.valueOf(value)
        if self.values.find(s) == -1:
            self.values += s
            return True

        return False

    # Java: contains(char) / contains(MapLocation) overloads, same dispatch.
    def contains(self, value):
        if isinstance(value, MapLocation):
            value = self.encodeLocation(value)
        return self.values.find(chr(value)) > -1

    def encodeLocation(self, location):
        # Java: (char) cast truncates to 16 bits
        return ((location.x << 6) | location.y) & 0xFFFF
