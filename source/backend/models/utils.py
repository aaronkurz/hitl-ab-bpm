""" Utility that is useful for other python modules in backend/models """
import enum

CASCADING_DELETE = "all, delete"


class WinningReasonEnum(enum.Enum):
    """ Enum defining possible reasons for how the winning version was determined """
    EXPERIMENT_ENDED = "Experiment ended normally"
    MANUAL_CHOICE = "Manual choice by human expert"


class Version(enum.Enum):
    """ Possible process version shorthands """
    a = 'a'
    b = 'b'
