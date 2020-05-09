import os
import pandas as pd
from copy import deepcopy
from microsetta_public_api.exceptions import ConfigurationError
from qiime2 import Artifact
from q2_types.sample_data import AlphaDiversity, SampleData


class ResourceManager(dict):

    dict_of_qza_resources = {'alpha_resources': SampleData[AlphaDiversity]}

    def update(self, other, **kwargs):
        """
        Updates the resources this manager has. If the resource field

        Parameters
        ----------
        other : dict
            Resource identifier to resource mapping. 'alpha_resources' is
            reserved for a dictionary. The values in 'alpha_resources' must be
            existing file paths with a .qza extension, they will be read
            into a python QZA.
        kwargs : dict
            kwargs for dict.update. Similar to `other`, but can be passed as
            keywords.

        Returns
        -------
        NoneType

        Examples
        --------
        >>> resources = ResourceManager(alpha_resources={
        ...     {'faith_pd': '/path/to/some.qza',
        ...      'chao1': '/another/path/to/a.qza',
        ...     }}, some_other_resource='here is a string resource')


        """
        for resource_name, type_ in self.dict_of_qza_resources.items():
            if resource_name in other:
                other = self._replace_paths_with_qza(other, resource_name,
                                                     type_)
            if resource_name in kwargs:
                kwargs = self._replace_paths_with_qza(kwargs, resource_name,
                                                      type_)

        return super().update(other, **kwargs)

    def _replace_paths_with_qza(self, resource, name, semantic_type):
        dict_of_qza_paths = resource[name]
        if not isinstance(dict_of_qza_paths, dict):
            raise ValueError(f"Expected '{name}' field to contain a dict. "
                             f"Got {type(resource[name]).__name__}")
        new_resource = deepcopy(resource)
        for key, value in dict_of_qza_paths.items():
            value_is_existing_qza_path = isinstance(value, str) and \
                (value[-4:] == '.qza') and os.path.exists(value)
            if value_is_existing_qza_path:
                new_resource[name][key] = self._parse_q2_data(value,
                                                              semantic_type)
            else:
                raise ValueError(f'Expected existing path with .qza '
                                 f'extension. Got: {value}')
        return new_resource

    @staticmethod
    def _parse_q2_data(filepath, semantic_type):
        try:
            data = Artifact.load(filepath)
        except ValueError as e:
            raise ConfigurationError(*e.args)

        if data.type != semantic_type:
            raise ConfigurationError(f"Expected QZA '{filepath}' to have type "
                                     f"'{semantic_type}'. "
                                     f"Received '{data.type}'.")

        return data.view(pd.Series)


resources = ResourceManager()
