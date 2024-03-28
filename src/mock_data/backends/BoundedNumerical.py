"""This class is used to sample data from a continuous distribution. This class has
the functionality to sample from a distribution and appropriately shift and scale the
data to a particular range. For example, this class can be used to sample data from a 
normal distribution but place the data on the interval of [0, 100]. Scaling and shifting
is handled automatically. Any continuous distribution from scipy.stats can be used. See
Scipy's list of continuous distributions at:
https://docs.scipy.org/doc/scipy/reference/stats.html#continuous-distributions

Only the name of the distribution should be supplied. Not the class itself. For example,
to use scipy.stats.norm as the underlying distribution, just pass distribution="norm"
and the class will utilize importlib to load the appropriate class. This approach is
taken becuase it simplifies generation of backends from properties listed within a 
yaml file. Otherwise, `distribution: norm` within a yaml file would need to be mapped
to the appropriate scipy class prior to calling the constructor for the backend class.
"""


import importlib
import logging
from numbers import Number
from typing import Iterable, List

import numpy as np
from scipy.stats.distributions import rv_continuous

from .AbstractBackendInterface import AbstractBackendInterface
from mock_data.backends.Correlation import Correlation

logger = logging.getLogger(__name__)


class BoundedNumerical(AbstractBackendInterface):
    """A sampling class facilitating the generation of random values following a
    specified distribution appropriately scaled and shifted to the given range."""

    def __init__(
        self,
        distribution: str = "uniform",
        lower_bound: Number = 0,
        upper_bound: Number = 1,
        coerce_to_int: bool = False,
        correlation: str = Correlation.INDEPENDENT.name,
        dep_field: str = None,
        dep_values: List[str] = None,
        **distribution_kwargs,
    ) -> None:
        """Samples will be drawn from `distribution` and placed on the interval of
        [`lower_bound`, `upper_bound`]. For distributions with infinite support, this
        sampling may be cropped. See self._calculate_distribution_lower_bound_and_width
        for a detailed explanation.

        Args:
            distribution (str, optional): The NAME of one of scipy's continuous
                distributions. Defaults to uniform.
            lower_bound (Number, optional): Lower bound of scaled and shifted samples.
                Defaults to 0.
            upper_bound (Number, optional): Upper bound of scaled and shifted samples.
                Defaults to 1.
            coerce_to_int (bool, optional): Indicates whether the output from generate
                samples should be returned as an integer array rather than as floats.
            distribution_kwargs: These are key word arguments supplied to the
                distribution's constructor method. For example, if distribution=chi2 a
                degrees of freedom kwarg must be supplied.

        Raises:
            ValueError: Raised if lower bound is greater than or equal to upper bound.
            ValueError: Raised if the supplied distribution is not one of the continuous
                distributions available within scipy.stats.
        """

        super().__init__(correlation, dep_field, dep_values)
        if not isinstance(distribution, str):
            raise TypeError(
                "The supplied value of dist should be a string specifying the name."
            )

        # create a "frozen" random variable. Uses _get_scipy_dist to retrieve the
        # constructor associated with the supplied distribution name. The distribution
        # keywords are supplied to this output to generate a frozen random variable
        self.distribution = self._get_scipy_dist(distribution)(**distribution_kwargs)

        if lower_bound >= upper_bound:
            raise ValueError("Lower bound cannot be greater than upper bound")

        self._lower_bound = lower_bound
        self._upper_bound = upper_bound

        self._coerce_to_int = coerce_to_int

        # calculate self._dist_lower_sampling_bound and self._dist_width
        self._calculate_distribution_lower_bound_and_width()

    def __repr__(self) -> str:
        return (
            f"Backend with scipy distribution '{self.distribution.dist.name}'"
            f" and value range [{self._lower_bound}, {self._upper_bound}]"
        )

    @classmethod
    def _get_scipy_dist(cls, distribution: str) -> rv_continuous:
        """Utilizes the importlib.import_module function to return the constructor of
        scipy.stats.{name}. Set as a static method to indicate that this functionality
        is tied to MockDataSet, but does not depend on the state of any particular
        instance of the class. Used when parsing yaml spec.

        Args:
            distribution (str): Name of distribution from scipy.stats

        Raises:
            KeyError: if the supplied name does not exist within the scipy.stats
            ValueError: if the supplied name deos not correspond to a subclass of
                rv_continuous.

        Returns:
            rv_continuous: The class associated with scipy.stats.<distribution>
        """

        try:
            dist = importlib.import_module("scipy.stats").__dict__[distribution]
        except KeyError:
            raise KeyError(
                f"The supplied distribution name `{distribution}` does not exist."
            )

        if not isinstance(dist, rv_continuous):
            raise ValueError(f"Invalid distribution `{distribution}`.")

        return dist

    def _calculate_distribution_lower_bound_and_width(self) -> None:
        """Calculates the [approximate] "width" and lower sampling bound of
        self.distribution. This is used to calculate the location and scaling factors
        required to sample from self.distribution and coerce the range between
        `lower_bound` and `upper_bound`. Populates self._dist_lower_sampling_bound and
        self._dist_width.

        If the supplied distribution has finite support, this width is calculated as the
        upper range of the domain minus the lower range of the domain. e.g. a uniform
        random variable only has support on [0, 1] and thus has a width of 1.

        For distributions that tail off towards -inf and/or +inf, an approximation is
        used. The width is estimated using a cropped distribution. Mathematically, this
        cropped distribution will integrate to 0.9998 or 0.9999 over the cropped range,
        depending on whether the distribution tails in one direction or two. A
        normal(0,1) distribution will be truncated approximately to [-3.7, 3.7]
        resulting in a width of 7.4.
        """

        # rv_continuous objects have `a` and `b` attributes speicyfing
        # support on [a, b].
        left_bound = self.distribution.a

        # approximate bound if the distribution tails to negative infinity
        if left_bound == -np.inf:
            left_bound = self.distribution.isf(0.9999)

        self._dist_lower_sampling_bound = left_bound

        right_bound = self.distribution.b

        # approximate bound if the distribution tails to positive infinity
        if right_bound == np.inf:
            right_bound = self.distribution.isf(0.0001)

        self._dist_width = right_bound - left_bound

    def generate_samples(self, size: int, directive: List = None) -> Iterable[Number]:
        """Samples `size` samples from self.distribution. Each sample is scaled and
        shifted to ensure that samples fall within the range
        [self.lower_bound, self.upper_bound]. Any sample generated from
        self.distribution.rvs that falls outside of this range is cropped. This should
        occur less than once per thousand samples on average.

        Args:
            size (int): Number of samples to generate.

        Returns:
            Iterable[Number]: An array of length `size` containing scaled and shifted
                values sampled from self.distribution. If self._coerce_to_int is True,
                this will be an array of integers. Otherwise, floats.
        """

        # sample from distribution and subtract the distributions
        # (possibly approximated) lower sampling bound. Crop any samples
        # falling outside the range of [0, self._dist_width]
        shifted_samples = (
            self.distribution.rvs(size=size) - self._dist_lower_sampling_bound
        )

        # crop as needed
        shifted_samples[shifted_samples < 0] = 0
        shifted_samples[shifted_samples > self._dist_width] = self._dist_width

        # divide shifted_samples above by the width of the dist to
        # place all values on the range of [0, 1]. Then multiply
        # by the desired width (computed as upper bound - lower bound).
        # Then add lower_bound to place values on the scale of
        # [lower_bound, upper_bound].
        output = np.round((
            shifted_samples / self._dist_width * (self._upper_bound - self._lower_bound)
        ) + self._lower_bound, decimals=3)

        if self._coerce_to_int:
            output = output.astype(int)

        return self.blanks_where_directed(output, directive)
