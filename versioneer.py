from pkg_resources import resource_stream

import yaml


def get_version():
    api_yml_stream = resource_stream('microsetta_public_api.api',
                                     'microsetta_public_api.yml')
    yml_contents = yaml.safe_load(api_yml_stream)
    return yml_contents['info']['version']
