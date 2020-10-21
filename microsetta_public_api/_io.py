from typing import Dict
from q2_types.distance_matrix import DistanceMatrix as DistanceMatrixType
from skbio.stats.distance import DistanceMatrix
from microsetta_public_api.resources import (
    _validate_dict_of_paths,
    _replace_paths_with_qza,
)


def _dict_of_paths_to_beta_data(dict_of_qza_paths, resource_name) -> \
        Dict[str, DistanceMatrix]:
    _validate_dict_of_paths(dict_of_qza_paths,
                            resource_name)
    new_resource = _replace_paths_with_qza(dict_of_qza_paths,
                                           DistanceMatrixType,
                                           view_type=DistanceMatrix,
                                           )
    return new_resource
