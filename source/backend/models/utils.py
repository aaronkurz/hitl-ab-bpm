""" Utility that is useful for other python modules in backend/models """
import enum

CASCADING_DELETE = "all, delete"


class WinningReasonEnum(enum.Enum):
    """ Enum defining possible reasons for how the winning version was determined """
    EXPERIMENT_ENDED = "Experiment ended normally"
    MANUAL_CHOICE = "Manual choice by human expert"


class Version(enum.Enum):
    """ Possible process version shorthands """
    A = 'a'
    B = 'b'


class ExperimentState(enum.Enum):
    """ Possible process/experiment states """
    RUNNING_BEFORE_FIRST_BATCH_POL = "Running, before first batch policy has been set"
    RUNNING_IN_BATCH = "Running, in batch"
    RUNNING_OUTSIDE_BATCH = "Running, outside batch"
    IN_COOL_OFF = "In Cool-Off"
    COOL_OFF_FIN_DEC_OUTSTANDING = "Cool-Off over, waiting for final decision"
    FINISHED = "Done"


def parse_version_str(version_str: str) -> Version:
    """Transform string 'a' or 'b' to internal enum representation

    :raises RuntimeError: When version_str is not 'a' or 'b'
    :param version_str: 'a' or 'b'
    :return: Version.A or Version.B
    """
    if version_str == 'a':
        return Version.A
    if version_str == 'b':
        return Version.B
    raise RuntimeError('Default version has to be "a" or "b"')
