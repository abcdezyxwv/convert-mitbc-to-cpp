# Port of bestsofar/Utils/AdditionalClasses/Thrown.java. See py/CONVENTIONS.md.
from api import *


class Thrown:
    def __init__(self, m, d):
        self.loc = m
        self.dir = d

    def isSafe(self, check):
        if check == self.loc:
            return False
        check = check.subtract(self.dir)
        if check == self.loc:
            return False
        check = check.subtract(self.dir)
        if check == self.loc:
            return False
        return True
