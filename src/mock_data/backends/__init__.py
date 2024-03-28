# See the following for a discussion on the redundant import used for the interface
# https://github.com/microsoft/pylance-release/issues/856#issuecomment-763793949
from .AbstractBackendInterface import (
    AbstractBackendInterface as AbstractBackendInterface,
)
from .BoundedDatetime import BoundedDatetime
from .BoundedNumerical import BoundedNumerical
from .FileRandom import FileRandom
from .LoremIpsumText import LoremIpsumText
from .MultipleResponse import MultipleResponse
from .WeightedDiscrete import WeightedDiscrete

# used by the MockDataset class as a registry of backend names to classes
_CORE_BACKENDS = {
    BoundedNumerical.__name__: BoundedNumerical,
    BoundedDatetime.__name__: BoundedDatetime,
    WeightedDiscrete.__name__: WeightedDiscrete,
    LoremIpsumText.__name__: LoremIpsumText,
    FileRandom.__name__: FileRandom,
    MultipleResponse.__name__: MultipleResponse,
}
