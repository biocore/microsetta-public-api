from microsetta_public_api.models._alpha import Alpha
from microsetta_public_api.repo._alpha_repo import AlphaRepo
from microsetta_public_api.repo._metadata_repo import MetadataRepo
from microsetta_public_api.utils import jsonify
from microsetta_public_api.utils._utils import (validate_resource_alt,
                                                check_missing_ids_alt,
                                                )
from microsetta_public_api.resources_alt import get_resources
from functools import partial
from microsetta_public_api.exceptions import (
    UnknownID,
    UnknownResource,
    IncompatibleOptions,
)
from microsetta_public_api.config import schema


def get_alpha_alt(dataset, sample_id, alpha_metric):
    alpha_resource = _validate_dataset_alpha(dataset, get_resources)

    alpha_repo = AlphaRepo(alpha_resource.data)
    alpha_value = _get_alpha(alpha_repo, alpha_metric, sample_id)

    return jsonify(alpha_value), 200


def _validate_dataset_alpha(dataset, resource_getter):
    try:
        dataset_resource = resource_getter().gets('datasets', dataset)
    except KeyError:
        raise UnknownResource(f"Unknown dataset: '{dataset}'")
    try:
        alpha_resource = dataset_resource.gets(schema.alpha_kw)
    except KeyError:
        raise UnknownResource(f"No alpha data (kw: '{schema.alpha_kw}') for "
                              f"dataset='{dataset}'.")
    return alpha_resource


def get_alpha(sample_id, alpha_metric):
    alpha_repo = AlphaRepo()
    ret_val = _get_alpha(alpha_repo, alpha_metric, sample_id)

    return jsonify(ret_val), 200


def _get_alpha(alpha_repo, alpha_metric, sample_id):
    if not all(alpha_repo.exists([sample_id], alpha_metric)):
        raise UnknownID(f"Sample ID not found. Got: {sample_id}")
    alpha_series = alpha_repo.get_alpha_diversity([sample_id],
                                                  alpha_metric)
    alpha_ = Alpha(alpha_series)
    alpha_data = alpha_.get_group_raw().to_dict()
    ret_val = {
        'sample_id': sample_id,
        'alpha_metric': alpha_data['alpha_metric'],
        'data': alpha_data['alpha_diversity'][sample_id],
    }
    return ret_val


def alpha_group_alt(body, dataset, alpha_metric, summary_statistics=True,
                    percentiles=None, return_raw=False):
    alpha_resource = _validate_dataset_alpha(dataset, get_resources)
    alpha_repo = AlphaRepo(alpha_resource.data)
    getter = partial(_metadata_repo_getter_alt, dataset=dataset)
    alpha_data = _alpha_group(body, alpha_repo, getter,
                              alpha_metric, percentiles,
                              return_raw, summary_statistics)

    return jsonify(alpha_data), 200


def alpha_group(body, alpha_metric, summary_statistics=True,
                percentiles=None, return_raw=False):
    alpha_repo = AlphaRepo()
    alpha_data = _alpha_group(body, alpha_repo, _metadata_repo_getter,
                              alpha_metric, percentiles,
                              return_raw, summary_statistics)

    response = jsonify(alpha_data)
    return response, 200


def _metadata_repo_getter():
    return MetadataRepo()


def _metadata_repo_getter_alt(dataset=None):
    if dataset is not None:
        metadata_path = ('datasets', dataset, schema.metadata_kw)
    else:
        metadata_path = ('datasets', schema.metadata_kw)

    try:
        return MetadataRepo(get_resources().gets(*metadata_path).data)
    except KeyError:
        raise UnknownResource(f"No metadata (kw: '{schema.metadata_kw}')")


def _alpha_group(body, alpha_repo, metadata_repo_getter, alpha_metric,
                 percentiles, return_raw, summary_statistics):
    if not (summary_statistics or return_raw):
        # swagger does not account for parameter dependencies, so we should
        #  give a bad request error here
        raise IncompatibleOptions('Either `summary_statistics`, '
                                  '`return_raw`, or both are required to be '
                                  'true.')
    sample_ids = []
    # do the common checks
    available_metrics = alpha_repo.available_metrics()
    type_ = 'metric'
    validate_resource_alt(available_metrics, alpha_metric,
                          type_)
    if 'sample_ids' in body:
        sample_ids = body['sample_ids']

        # figure out if the user asked for a metric we have data on
        # make sure all of the data the samples the user asked for have values
        # for the given metric
        missing_ids = [id_ for id_ in sample_ids if
                       not alpha_repo.exists(id_, alpha_metric)]
        check_missing_ids_alt(missing_ids, alpha_metric,
                              type_)
    # find sample IDs matching the metadata query
    if 'metadata_query' in body:
        query = body['metadata_query']
        metadata_repo = metadata_repo_getter()
        matching_ids = metadata_repo.sample_id_matches(query)
        matching_ids = [id_ for id_ in matching_ids if
                        alpha_repo.exists(id_, alpha_metric)
                        ]
        if 'sample_ids' not in body:
            sample_ids = matching_ids
        elif body['condition'] == 'OR':
            sample_ids = list(set(sample_ids) | set(matching_ids))
        elif body['condition'] == 'AND':
            sample_ids = list(set(sample_ids) & set(matching_ids))
    # retrieve the alpha diversity for each sample
    alpha_series = alpha_repo.get_alpha_diversity(sample_ids,
                                                  alpha_metric,
                                                  )
    alpha_ = Alpha(alpha_series, percentiles=percentiles)
    alpha_data = dict()
    if return_raw:
        # not using name right now, so give it a placeholder name
        alpha_values = alpha_.get_group_raw(name='').to_dict()
        del alpha_values['name']
        alpha_data.update(alpha_values)
    if summary_statistics:
        # not using name right now, so give it a placeholder name
        alpha_summary = alpha_.get_group(name='').to_dict()
        del alpha_summary['name']
        alpha_data.update({'alpha_metric': alpha_summary.pop('alpha_metric')})
        alpha_data.update({'group_summary': alpha_summary})
    return alpha_data


def available_metrics_alpha_alt(dataset):
    alpha_resource = _validate_dataset_alpha(dataset, get_resources)
    alpha_repo = AlphaRepo(alpha_resource.data)
    return jsonify(_available_metrics(alpha_repo)), 200


def available_metrics_alpha():
    alpha_repo = AlphaRepo()
    ret_val = _available_metrics(alpha_repo)

    return jsonify(ret_val), 200


def _available_metrics(alpha_repo):
    ret_val = {
        'alpha_metrics': alpha_repo.available_metrics(),
    }
    return ret_val


def exists_single_alt(dataset, alpha_metric, sample_id):
    alpha_resource = _validate_dataset_alpha(dataset, get_resources)
    alpha_repo = AlphaRepo(alpha_resource.data)
    return _exists(alpha_repo, alpha_metric, sample_id)


def exists_single(alpha_metric, sample_id):
    alpha_repo = AlphaRepo()
    return _exists(alpha_repo, alpha_metric, sample_id)


def exists_group_alt(body, dataset, alpha_metric):
    alpha_resource = _validate_dataset_alpha(dataset, get_resources)
    alpha_repo = AlphaRepo(alpha_resource.data)
    return _exists(alpha_repo, alpha_metric, body)


def exists_group(body, alpha_metric):
    alpha_repo = AlphaRepo()
    return _exists(alpha_repo, alpha_metric, body)


def _exists(alpha_repo, alpha_metric, samples):
    # figure out if the user asked for a metric we have data on
    available_metrics = alpha_repo.available_metrics()
    type_ = 'metric'
    validate_resource_alt(available_metrics, alpha_metric,
                          type_)

    return jsonify(alpha_repo.exists(samples, alpha_metric)), 200
