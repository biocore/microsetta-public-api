from unittest import TestCase
import jsonschema
from jsonschema.exceptions import ValidationError
from microsetta_public_api.config import (
    general_schema,
    validate,
)


class TestConfigSchema(TestCase):
    def test_valdiate_schema(self):
        simple_test_schema = {
            'datasets': {
                'components': {
                    'another_comp': {
                        'construct': 'TrivialLoader',
                    }
                },
                'construct': 'TrivialLoader',
                'config': {
                    'some': 'arg'
                },
            }
        }
        # will throw an exception if its wrong
        jsonschema.validate(instance=simple_test_schema, schema=general_schema)

    def test_valdiate_schema_fails(self):
        simple_test_schema = {
            'datasets': {
                'components': {
                    'another_comp': {
                        'construct': 'TrivialLoader',
                    }
                },
                'construct': 8.25,
                'config': {
                    'some': 'arg'
                },
            }
        }
        # will throw an exception if its wrong
        with self.assertRaises(ValidationError):
            validate(simple_test_schema)

        simple_test_schema = {
            'datasets': {
                'components': {
                    'another_comp': {
                        'construct': 'TrivialLoader',
                        'components': {
                            'not_alpha_diversity': {}
                        }
                    },
                },
                'construct': 'TrivialLoader',
                'config': {
                    'some': 'arg'
                },
            }
        }
        # will throw an exception if its wrong
        with self.assertRaises(ValidationError):
            validate(simple_test_schema)
