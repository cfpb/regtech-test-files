"""This is an SBL specific backend for generating samples of type "Multiple Response."
These are strings of numbers separated by semicolons. 

For example, the Credit Purpose field in the SBL Fig can take the values 1 through 11, 
977, 988, or 999. Three selections from this list could be represented as "1;5;6". Such
samples can be generated with this backend.
"""

# TODO: THIS NEEDS TO BE TESTED

import random
from typing import List

from mock_data.backends import AbstractBackendInterface, BoundedNumerical
from mock_data.backends.Correlation import Correlation

class MultipleResponse(AbstractBackendInterface):
    def __init__(
        self,
        codes: List[int],
        min_selections: int = 1,
        max_selections: int = 5,
        distribution: str = "uniform",
        duplicates_allowed: bool = False,
        single_selection_codes: List[int] = [],
        single_selection_probability: float = 0,
        correlation: str = Correlation.INDEPENDENT.name,
        dep_field: str = None,
        dep_values: List[str] = None,
        **distribution_kwargs,
    ) -> None:
        """Facilitates generation of multiple response fields. These are fields within
        the SBL Fig denoted "Field type: Multiple response." The set of codes to sample
        from, per sample length distribution, and whether duplicates are allowed must
        all be set. The only one that does not contain default values is the list of
        codes. Depending on the use case of the mock data, these codes could be valid,
        invalid, or a combination thereof.

        For example, `MultipleResponse(codes=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10])` will
        create an engine that returns duplicate-free concatenations with 1 through
        5 elements. The default uniform distribution will cause each of these lengths
        to occur with approximately equal frequency. To make single selections more
        common than 4 and 5 selections, the distribution could be changed to a
        "right tail" distribution such as an exponential distribution.

        In order to generate records where certain values cannot be combined with any
        other record, supply codes to `single_selection_codes`. For example, if this is
        set to [977], 977 will not appear in a sample with other records. The frequency
        with which single selection codes appear is controled by the probability keyword
        `single_selection_probability`. This value should be between 0 and 1 and
        controls the proportion of samples that are single selections.

        Args:
            codes (List[int]): List of codes to sample from. These are all integers
                within SBL Multiple Response fields, but could theoretically be any
                object that is serializable. Do not include single selection codes in
                this list. Supply these to `single_selection_codes`.
            min_selections (int, optional): Minimum number of codes that will be sampled
                when generating mock data. Defaults to 1.
            max_selections (int, optional): Maximum number of codes that will be sampled
                when generating mock data. Defaults to 5.
            distribution (str, optional): Name of the scipy.stat's distribution from
                which the number of codes to sample is drawn. Defaults to "uniform".
            duplicates_allowed (bool, optional): If True, the generated samples may
                contain duplicate values. e.g. 1;1;2. Defaults to False.
            single_selection_codes (List[str], optional): A set of codes that can only
                appear by themselves.
            single_selection_probability (float, optional): Controls the proportion of
                generated samples that are drawn from the list of single selection
                codes. If set to 0.1, approximately 10% of generated samples will be
                one of the codes in `single_selection_codes`.
            **distribution_kwargs: These are fed to the constructor of BoundedNumerical.

        Raises:
            ValueError: if max_selections is greater than
        """

        super().__init__(correlation, dep_field, dep_values)

        # TODO: perform validation on input arguments

        # casting codes to strings to facilitate string concatenation
        self.codes = [str(code) for code in codes]
        self.single_selection_codes = [str(code) for code in single_selection_codes]
        self.single_selection_probability = single_selection_probability

        self.duplicates_allowed = duplicates_allowed

        # This instance of BoundedNumerical will be used to sample the
        # count of how many codes to sample. The MultipleResponse class
        # has an instance of BoundedNumerical. This is an example of the
        # 'has a' design pattern, rather than 'is a'
        self._length_sampling_dist = BoundedNumerical(
            distribution=distribution,
            lower_bound=min_selections,
            upper_bound=max_selections,
            coerce_to_int=True,
            **distribution_kwargs,
        )


    # TODO: go over this docstring and make it clearer
    def generate_samples(self, size: int, directive: List = None) -> List[str]:
        """Generates a list of semicolon delimited strings with `size` elements. If
        self.duplicates_allowed == True, the elements may contain duplicates. Otherwise,
        they will not. If the set of codes is [1,2,3], outputs would look something
        like "1;2", "3;977", etc. They will not contain a trailing semicolon.

        If single selection codes are present, roughly single_selection_probability
        percent of the samples will be single elements drawn from the list of single
        selection codes.

        The sampling logic is deferred to random.choices and random.sample depending
        on whether the set is being sampled with or without replacement.

        Args:
            size (int): Number of samples to generate.

        Returns:
            List[str]: Generated samples.
        """

        sample_holder = []

        # The ith sample will contain lengths[i] codes unless selected
        # as a single response sample
        lengths = self._length_sampling_dist.generate_samples(size=size)

        for length in lengths:
            # try sampling a single selection code
            if random.uniform(0, 1) < self.single_selection_probability:
                sample_holder.append(
                    random.choices(self.single_selection_codes, k=1)[0]
                )
            # otherwise sample length elements either via sampling with
            # replacement or not
            else:
                if self.duplicates_allowed:
                    # sample length elements from self.codes with replacement
                    # https://docs.python.org/3/library/random.html#random.choices
                    sample_holder.append(";".join(random.choices(self.codes, k=length)))
                else:
                    # sample length elements from self.codes without replacement
                    # https://docs.python.org/3/library/random.html#random.sample
                    sample_holder.append(";".join(random.sample(self.codes, k=length)))

        return self.blanks_where_directed(sample_holder, directive)
