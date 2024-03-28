"""This class implements a mechanism with which values can be sampled from a finite
set of options with specified frequency. The class is initialized with a dictionary
mapping objects to weights. These weights are non-zero numerical values indicating the
relative frequency with which objects in the set will be sampled.

For example, suppose you wished to sample a day of the week but you wanted Monday to 
be much more common than the other days. You could implement this as follows:

```
weekday_sampler = WeightedDiscrete(
    {
        "Monday": 20, 
        "Tuesday": 1,
        "Wednesday": 1, 
        "Thursday": 1, 
        "Friday": 1, 
        "Saturday": 1, 
        "Sunday": 1
    }
)

sampled_days = weekday_sampler.generate_samples(size=1000)
```

The `sampled_days` array above will contain approximately 20 Mondays per 26 samples.

It is also possible to pass the population argument as a list. The items in the list
are interpreted as the elements within the population. A weight of 1 is automatically
assigned to each element internally.
"""

import random
from numbers import Number
from typing import Dict, Hashable, List, Union

from mock_data.backends import AbstractBackendInterface
from mock_data.backends.Correlation import Correlation

class WeightedDiscrete(AbstractBackendInterface):
    def __init__(
        self, population: Union[List[Hashable], Dict[Hashable, Number]],
        correlation: str = Correlation.INDEPENDENT.name,
        dep_field: str = None,
        dep_values: List[str] = None,
    ) -> None:
        """Enables sampling from the supplied population dict or list. If a list is
        supplied, each entry is given a weight of 1. Otherwise, the supplied dictionary
        is validated to ensure the weights are non-negative, numerical values. The keys
        of the population are interpreted as the elements of the population and the
        values are the relative frequency with which they will be sampled.

        Args:
            population (Dict[Hashable, Number]): This is a mapping of objects to
                sampling weights. For example population={"A": 10, "B": 1} will
                sample from the set {A, B} with A being sampled 10 times more often than
                B. The magnitude of the values is arbitrary. e.g. {"A": 10, "B":1} is
                the same as {"A": 1, "B":0.1}. Keys will typically be strings but any
                hashable type is valid.
            population (List[Hashable]): A list of items from which the samples
                should be drawn. Each element is equally likely to be drawn.
        """

        super().__init__(correlation, dep_field, dep_values)
        if isinstance(population, list):
            # change to a dictionary representation with weights of 1
            population = {element: 1 for element in population}

        self._validate_frequency_dist(frequency_dist=population)

    def _validate_frequency_dist(self, frequency_dist: Dict[Hashable, Number]) -> None:
        """Performs validation on the entries within the supplied frequency distribution
        mapping. Ensures that all frequencies are non negative, numerical values.
        0 is valid and results in the corresponding key having no possibility of being
        sampled. This is useful for retaining existing entries with a yaml file, but
        excluding them from the generation of the mock dataset.

        After validation is performed, self.frequency_dist is set to the supplied dict.
        Additionally, self._population is set to the keys within the frequency dict and
        self._weights is set to the values.

        Args:
            frequency_dist (Dict[Hashable, Number]): Frequency distribution fed from
                the constructor.

        Raises:
            TypeError: If any value is not numeric in nature.
            ValueError: If any value is negative.
        """
        for value in frequency_dist.values():
            if not isinstance(value, Number):
                raise TypeError(
                    "For each (key: value) mapping, value must be a number."
                )
            elif value < 0:
                raise ValueError(
                    "For each (key: value) mapping, value must be a positive number."
                )

        # The supplied frequency distribution dictionary is not used directly
        self._population = list(frequency_dist.keys())
        self._weights = list(frequency_dist.values())

    def __repr__(self) -> str:
        frequency_distribution = dict(zip(self._population, self._weights))
        return f"WeightedDiscrete with sampling distribution {frequency_distribution}"

    def generate_samples(self, size: int, directive: List = None) -> List[Hashable]:
        """Uses random.choices to select `size` samples from self._population with
        weights specified by self._weights. random.choices utilizes sampling with
        replacement so this method can be repeated an arbitrary number of times as
        indendent samples.

        Args:
            size (int): Number of samples to draw from self._population.

        Returns:
            List[Hashable]: A list of size `size` containing one or more keys from
                self._population.
        """
        return self.blanks_where_directed(random.choices(
            population=self._population, weights=self._weights, k=size),
            directive)
