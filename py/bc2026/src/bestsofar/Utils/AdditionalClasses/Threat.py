# Port of bestsofar/Utils/AdditionalClasses/Threat.java. See py/CONVENTIONS.md.
from api import *


class Threat:
    # Java: the fields are declared `static` (arguably a bug - every Threat
    # instance shares one loc/dir/threat). Preserved exactly.
    loc = None
    dir = None
    threat = False

    def __init__(self, m, d, t):
        Threat.loc = m
        Threat.dir = d
        Threat.threat = t
