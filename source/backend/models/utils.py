""" Utility that is useful for other python modules in backend/models """
import enum

CASCADING_DELETE = "all, delete"

class WinningReasonEnum(enum.Enum):
    experimentEnded = "Experiment ended"
    manualChoice = "Manual choice by human expert"


class Version(enum.Enum):
    a = 'a'
    b = 'b'