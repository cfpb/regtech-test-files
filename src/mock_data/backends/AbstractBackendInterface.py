from abc import ABC, abstractmethod
from typing import Iterable, List
from mock_data.backends.Correlation import Correlation

directiveColumns = {}

class AbstractBackendInterface(ABC):
    """This class serves as an interface from which all backends should inherit.

    Each subclass must implement self.generate_samples(size)"""

    def __init__(self, correlation: str = Correlation.INDEPENDENT.name,
                 dep_field: str = None, dep_values: List[str] = None) -> None:
        self.correlation = Correlation[correlation.upper()]
        self.dep_field = dep_field
        self.dep_values = dep_values


    def directive_requires_value(self, dval: any):
        dval = dval.split(';') if type(dval) == str and ';' in dval else str(dval)
        return ((type(dval) == str and dval in self.dep_values) or
                (type(dval) == list and (set(dval) & set(self.dep_values))))


    def blanks_where_directed(self, vals, directive):
        if not directive: return vals
        return [v if self.directive_requires_value(directive[i]) else "" for i, v in enumerate(vals)]


    @abstractmethod
    def generate_samples(self, size: int, directive: List) -> Iterable:
        """This method must be implemented by each sampling engine. The method should
        accept the number of samples to generate and return a numpy array containing
        samples. These can be of any data type appropriate for the sampling engine.

        Args:
            size (int): A positive integer representing the desired number of samples.

        Returns:
            Iterable: An iterable (list, np.array, etc) of sampled values with `size`
                elements.
        """
        pass
