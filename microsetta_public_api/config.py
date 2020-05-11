import os
from microsetta_public_api.exceptions import ConfigurationError


class ResourcesConfig(dict):

    resource_fields = ['alpha_resources']

    def update(self, _m, **kwargs):

        for resource_field in self.resource_fields:
            if resource_field in self:
                self._validate_resource_locations(self[resource_field])

        return super().update(_m, **kwargs)

    @staticmethod
    def _validate_resource_locations(resource_locations):
        if not isinstance(resource_locations, dict):
            raise ConfigurationError('resource_locations must be '
                                     'able to be parsed into a python '
                                     'dictionary.')
        all_keys_str = all(isinstance(key, str) for key in
                           resource_locations)
        if not all_keys_str:
            raise ConfigurationError('All `alpha_resources` keys must be '
                                     'strings.')
        all_values_fp = all(os.path.exists(val) for val in
                            resource_locations.values())
        if not all_values_fp:
            raise ConfigurationError('All `alpha_resources` values must be '
                                     'existing file paths.')
        return True

    pass


resources = ResourcesConfig()
