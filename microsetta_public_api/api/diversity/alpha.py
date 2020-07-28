from microsetta_public_api.models._alpha import Alpha
from microsetta_public_api.repo._alpha_repo import AlphaRepo
from microsetta_public_api.repo._metadata_repo import MetadataRepo
from microsetta_public_api.utils import jsonify
from microsetta_public_api.utils._utils import validate_resource, \
    check_missing_ids


def get_alpha(sample_id, alpha_metric):
    alpha_repo = AlphaRepo()
    if not all(alpha_repo.exists([sample_id], alpha_metric)):
        return jsonify(error=404, text="Sample ID not found."), \
               404
    alpha_series = alpha_repo.get_alpha_diversity([sample_id],
                                                  alpha_metric)
    alpha_ = Alpha(alpha_series)
    alpha_data = alpha_.get_group_raw().to_dict()
    ret_val = {
        'sample_id': sample_id,
        'alpha_metric': alpha_data['alpha_metric'],
        'data': alpha_data['alpha_diversity'][sample_id],
    }

    return jsonify(ret_val), 200


def alpha_group(body, alpha_metric, summary_statistics=True,
                percentiles=None, return_raw=False):
    if not (summary_statistics or return_raw):
        # swagger does not account for parameter dependencies, so we should
        #  give a bad request error here
        return jsonify(
            error=400, text='Either `summary_statistics`, `return_raw`, '
                            'or both are required to be true.'
            ), 400
    if ('sample_ids' in body and 'metadata_query' in body) and \
            'condition' not in body:
        # give a bad request error here, because we need to know how to
        #  resolve the sample IDs
        return jsonify(
            error=400, text='`condition` must be specified if both '
                            '`sample_ids` and `metadata_query` are specified.'
        )

    sample_ids = []
    alpha_repo = AlphaRepo()
    # do the common checks
    available_metrics = alpha_repo.available_metrics()
    type_ = 'metric'
    missing_metric = validate_resource(available_metrics, alpha_metric,
                                       type_)
    if missing_metric:
        return missing_metric

    if 'sample_ids' in body:
        sample_ids = body['sample_ids']

        # figure out if the user asked for a metric we have data on
        # make sure all of the data the samples the user asked for have values
        # for the given metric
        missing_ids = [id_ for id_ in sample_ids if
                       not alpha_repo.exists(id_, alpha_metric)]
        missing_ids_msg = check_missing_ids(missing_ids, alpha_metric, type_)
        if missing_ids_msg:
            return missing_ids_msg

    # find sample IDs matching the metadata query
    if 'metadata_query' in body:
        query = body['metadata_query']
        metadata_repo = MetadataRepo()
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

    response = jsonify(alpha_data)
    return response, 200


def available_metrics_alpha():
    alpha_repo = AlphaRepo()
    ret_val = {
        'alpha_metrics': alpha_repo.available_metrics(),
    }

    return jsonify(ret_val), 200
