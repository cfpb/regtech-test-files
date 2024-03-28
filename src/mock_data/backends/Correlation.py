
from enum import Enum

class Correlation(Enum):
    INDEPENDENT = 0,
    DIRECTIVE = 1,
    CASCADING_L1 = 2,
    CASCADING_L2 = 3,
    DEPENDENT = 4
