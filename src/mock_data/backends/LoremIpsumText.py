"""Used to generate random text strings with Lorem Ipsum. Uses the flat file in 
resources/loremipsum.txt to create a list of unique Lorem Ipsum words. There are 
approximately 170 of them in the file. These are randomly sampled and stitched together
to generate text with specified lengths."""


from importlib.resources import files
import os
from numbers import Number
from random import choices
from typing import List

import numpy as np
from numpy import random

from mock_data.backends import BoundedNumerical
from mock_data.backends.Correlation import Correlation

# read from resources/loremipsum.txt and create a list of ipsum words
with open(files('mock_data.backends.resources').joinpath('loremipsum.txt'), "r") as f:
    LOREM_IPSUM_TEXT_CORPUS = list(set(f.read().split(" ")))


class LoremIpsumText(BoundedNumerical):
    """A class for generating lorem ipsum text with data length sampled from a
    continuous distribution of specified bounds."""

    # this is a list of lorem ipsum words we'll randomly sample to
    # generate strings of text. Shared across all class instances
    TEXT_CORPUS = LOREM_IPSUM_TEXT_CORPUS

    def __init__(
        self,
        distribution: str = "uniform",
        lower_bound: Number = 5,
        upper_bound: Number = 100,
        blank_probability: float = 0,
        correlation: str = Correlation.INDEPENDENT.name,
        dep_field: str = None,
        dep_values: List[str] = None,
        **distribution_kwargs,
    ) -> None:
        """Supplies all arguments to the constructor of ContinousRandom with the
        exception of blank_probability, which controls the probability of sampling a
        blank string. This value must be between 0 and 1. See the docstring for
        BoundedNumerical.__init__ for a description of the remaining arguments.

        Args:
            distribution (str, optional): Name of the scipy.stats distribution from
                which lengths are sampled from. Defaults to uniform.
            lower_bound (Number, optional): Lower bound of sampled text length.
                Defaults to 5.
            upper_bound (Number, optional): Upper bound of sampled text length.
                Defaults to 100.
            blank_probability (float, optional): Proportion of sampled text strings
                equal to a blank string (""). This proportion will converge as the
                sample size grows. Defaults to 0.

        Raises:
            ValueError: If blank_probability is outside the interval [0,1].
        """
        if not 0 <= blank_probability <= 1:
            raise ValueError(
                "The blank_probability arg must be between 0 and 1, inclusive."
            )
        self.blank_probability = blank_probability
        super().__init__(distribution, lower_bound, upper_bound, **distribution_kwargs,
                         correlation=correlation, dep_field=dep_field, dep_values=dep_values)

    def generate_samples(self, size: int = 1, directive: List = None) -> List[str]:
        """Generates a list of `size` elements containing Lorem Ipsum text.

        The length of the text is sampled from super().generate_samples. There is a
        self.blank_probability chance that any given element will be a blank string.

        Args:
            size (int, optional): Number of random text strings to generate.
                Defaults to 1.

        Returns:
            List[str]: A list of Lorem Ipsum text strings containing `size` elements.
        """

        # makes call to ContinousRandom.generate_samples to generate lengths
        sample_lengths = super().generate_samples(size=size).astype(int)

        samples = []

        for c in range(len(sample_lengths)):
            length = sample_lengths[c]
            if ((directive and not self.directive_requires_value(directive[c])) or
                (random.uniform() < self.blank_probability)):
                samples.append("")
            else:
                samples.append(
                    LoremIpsumText._generate_lorem_ipsum_text_of_given_length(
                        length=length
                    )
                )
        return samples


    @classmethod
    def _generate_lorem_ipsum_text_of_given_length(cls, length: int) -> str:
        """Samples text of length `length` from cls.TEXT_CORPUS.

        This mechanism is a bit jenky because it is difficult to sample a collection
        of words with a pre specified cumulative character count. Instead, it is
        estimated how many words we'll need, these are joined together (with a space
        between them), and the resultant string is cropped to length `length`. The
        string may end with a space and it's probable that the last Lorem Ipsum word
        is chopped.

        Args:
            length (int): Length of the lorem ipsum text to generate.

        Returns:
            str: A Lorem Ipsum text string of length `length`.
        """
        # going to double the number of words we probably need for a buffer
        # Not going to choose fewer than 5 or it will likely not be enough
        word_count = np.max([np.ceil(length / 7 * 2), 5]).astype(int)

        return " ".join(choices(cls.TEXT_CORPUS, k=word_count))[:length]
