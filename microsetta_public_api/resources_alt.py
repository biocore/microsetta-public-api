from microsetta_public_api.config import (
    ConfigElementVisitor,
    DictElement,
    SchemaBase,
)
from microsetta_public_api.resources import (
    _dict_of_paths_to_alpha_data,
    _transform_dict_of_table,
    _dict_of_dict_of_paths_to_pcoa,
    _load_q2_metadata,
)
from microsetta_public_api._io import (
    _dict_of_paths_to_beta_data,
)


class Q2Visitor(ConfigElementVisitor):

    def __init__(self, schema=None):
        if schema is None:
            schema = SchemaBase()
        self.schema = schema

    def visit_alpha(self, element):
        element.data = _dict_of_paths_to_alpha_data(element,
                                                    self.schema.alpha_kw)

    def visit_taxonomy(self, element):
        element.data = _transform_dict_of_table(element,
                                                self.schema.taxonomy_kw)

    def visit_pcoa(self, element):
        element.data = _dict_of_dict_of_paths_to_pcoa(element,
                                                      self.schema.pcoa_kw)

    def visit_metadata(self, element):
        element.data = _load_q2_metadata(element, self.schema.metadata_kw)

    def visit_beta(self, element):
        element.data = _dict_of_paths_to_beta_data(element,
                                                   self.schema.beta_kw)


resources_alt = DictElement()


def get_resources():
    return resources_alt
