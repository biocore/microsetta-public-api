from microsetta_public_api.config import (
    ConfigElementVisitor,
    DictElement,
    SchemaBase,
)
from microsetta_public_api.resources import (
    _dict_of_paths_to_alpha_data,
    _transform_dict_of_table,
    _dict_of_dict_of_paths_to_pcoa,
    _dict_of_literals_to_dict,
    _load_q2_metadata,
    _load_neighbors_tsv
)
from microsetta_public_api._io import (
    _dict_of_paths_to_beta_data,
)
from microsetta_public_api._logging import timeit


class Q2Visitor(ConfigElementVisitor):

    def __init__(self, schema=None):
        if schema is None:
            schema = SchemaBase()
        self.schema = schema

    @timeit('visit_alpha')
    def visit_alpha(self, element):
        element.data = _dict_of_paths_to_alpha_data(element,
                                                    self.schema.alpha_kw)

    @timeit('vist_taxonomy')
    def visit_taxonomy(self, element):
        element.data = _transform_dict_of_table(element,
                                                self.schema.taxonomy_kw)

    @timeit('visit_pcoa')
    def visit_pcoa(self, element):
        element.data = _dict_of_dict_of_paths_to_pcoa(element,
                                                      self.schema.pcoa_kw)

    @timeit('visit_metadata')
    def visit_metadata(self, element):
        element.data = _load_q2_metadata(element, self.schema.metadata_kw)

    @timeit('visit_beta')
    def visit_beta(self, element):
        element.data = _dict_of_paths_to_beta_data(element,
                                                   self.schema.beta_kw)

    @timeit('visit_dataset_detail')
    def visit_dataset_detail(self, element):
        element.data = _dict_of_literals_to_dict(element,
                                                 self.schema.detail_kw)

    @timeit('visit_neighbors')
    def visit_neighbors(self, element):
        element.data = _load_neighbors_tsv(element, self.schema.neighbors_kw)


resources_alt = DictElement()


def get_resources():
    return resources_alt
