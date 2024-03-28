import logging
from typing import Dict

import pandas as pd
import yaml
import os

from .backends import _CORE_BACKENDS, AbstractBackendInterface
from mock_data.backends.Correlation import Correlation

logger = logging.getLogger(__name__)


class MockDataset:
    BACKENDS = _CORE_BACKENDS

    def __init__(self, spec: Dict) -> None:
        """WARNING: this method should not be used directly. It is advised to make use
        of the read_yaml_spec method of this class to generate a class instances rather
        than supply a dictionary spec to the constructor. The reason for this is that
        `read_yaml_spec` validates the supplied backend. You're on your own if
        leveraging __init__ directly. You've been warned :)

        The specification (spec) is a mapping of field names to backends and backends
        to kwargs. The top level keys are the names of the fields present within the
        dataset. The secondary key corresponds to the name of the backend that should
        be used for said field. All lower level keys are supplied to the constructor of
        the backend. For example, an `income` field could be defined as follows via
        yaml.

        income:
            BoundedNumerical:
                distribution: norm
                lower_bound: 10000
                upper_bound: 100000

        Args:
            spec (Dict): Dictionary representing the processing specification.
        """

        self.spec = spec

    def generate_mock_data(self, nrows: int) -> pd.DataFrame:
        holder = {}

        dependent_fields = []

        for field, backend in self.spec.items():
            if backend.correlation == Correlation.DEPENDENT:
                dependent_fields.append((field, backend))
                continue
            holder[field] = backend.generate_samples(size=nrows)
            logger.debug(f'generate_mock_data: {field}: {holder[field]}')

        for field, backend in dependent_fields:
            holder[field] = backend.generate_samples(nrows, holder[backend.dep_field])
            logger.debug(f'generate_mock_data: {field}: {holder[field]}')

        return pd.DataFrame(holder)

    @classmethod
    def register_backend(cls, backend) -> None:
        """Register additional backends for use in mock data generation. Without this
        process, the yaml parser would not know how to process custom data backends.

        Custom data backends must inherit from AbstractBackendInterface. The class must
        then be registered via MockDataset.register_backend(MyCustomBackendClass).

        Args:
            backend (_type_): A subclass of AbstractBackendInterface representing a
                custom data backend.

        Raises:
            TypeError: If the supplied backend is not a subclass of the interface class.
        """
        if issubclass(backend, AbstractBackendInterface):
            if backend.__name__ not in cls.BACKENDS:
                cls.BACKENDS[backend.__name__] = backend
                logger.info(f"Registered backend {backend.__name__}")
            else:
                logger.warning(f"Backend {backend.__name__} is already registered.")
        else:
            raise TypeError(
                "Invalid backend. Must be a subclass of AbstractBackendInterface."
            )

    @classmethod
    def read_yaml_spec(cls, path: str) -> "MockDataset":
        """Factory method for generating MockDataset instances by reading specification
        from the yaml file at the supplied path. This is the preferred way of creating
        instances of this class. Field validation does not occur when calling __init__
        directly.

        Args:
            path (str): Path to the yaml file.

        Raises:
            RuntimeError: If more than one backend is supplied for a given field.
            ValueError: If an unknown backend is listed.

        Returns:
            MockDataset: A class instance ready for creating mock data.
        """

        with open(path, "r") as f:
            raw_spec = yaml.safe_load(f)

        logger.info(f"Dataset will have the following ields: {list(raw_spec.keys())}")

        # this will be populated as the yaml is parsed. Maps field to Backend object
        spec_dict = {}
        for field, field_spec in raw_spec.items():
            logger.debug(f'read_yaml_spec: {field}')
            for _, (backend, backend_kwargs) in enumerate(field_spec.items()):
                # make sure only one backend has been supplied per field
                if _ > 0:
                    raise RuntimeError(f"More than one backend supplied for {field}.")

                # get the class
                try:
                    _backend = cls.BACKENDS[backend]
                except KeyError:
                    raise ValueError(
                        f"Unknown backend {backend}. Call `register_backend` first."
                    )
                spec_dict[field] = _backend(**backend_kwargs)

        return MockDataset(spec=spec_dict)
