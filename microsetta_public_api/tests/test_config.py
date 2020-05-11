from microsetta_public_api.utils.testing import TempfileTestCase
from microsetta_public_api.config import ResourcesConfig
from microsetta_public_api.exceptions import ConfigurationError


class TestConfig(TempfileTestCase):

    def test_validate_resource_locations_non_dict(self):
        config = ResourcesConfig()
        resource_locations = ['alpha', 'beta']
        with self.assertRaisesRegex(ConfigurationError, 'dictionary'):
            config._validate_resource_locations(resource_locations)

    def test_validate_resource_locations_non_string_resource_key(self):
        resource_locations = {9: '/some/file/path'}
        config = ResourcesConfig()
        with self.assertRaisesRegex(ConfigurationError, 'keys must be '
                                                        'strings'):
            config._validate_resource_locations(resource_locations)

    def test_validate_resource_locations_non_existing_resource_value(self):
        file_ = self.create_tempfile()
        # closing the file removes it from the filesystem
        file_.close()

        resource_locations = {'some-metric': file_.name}
        config = ResourcesConfig()
        with self.assertRaisesRegex(ConfigurationError, 'must be '
                                                        'existing '
                                                        'file paths'):
            config._validate_resource_locations(resource_locations)
