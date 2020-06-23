from operator import eq, ge
from functools import partial
import pandas as pd
from microsetta_public_api.resources import resources

ops = {
    'equal': eq,
    'greater_or_equal': ge,
}

conditions = {
    "AND": partial(pd.DataFrame.all, axis=1),
    "OR": partial(pd.DataFrame.any, axis=1)
}


def _is_rule(node):
    rule_fields = ["id", "operator", "value"]
    for field in rule_fields:
        if field not in node:
            return False

    op = node["operator"]
    if op not in ops:
        raise ValueError(f"Only operators in {ops} are supported. "
                         f"Got {op}")

    return True


class MetadataRepo:

    def __init__(self):
        self._metadata = resources.get('metadata', pd.DataFrame())

    @property
    def metadata(self):
        return self._metadata

    @property
    def categories(self):
        return list(self._metadata.columns)

    def category_values(self, category, exclude_na=True):
        """
        Parameters
        ----------
        category : str
            Metadata category to return the values of

        exclude_na : bool
            If True, not a number (na) values will be dropped from the
            category values

        Returns
        -------
        list
            Contains the unique values in the metadata category

        Raises
        ------
        ValueError
            If `category` is not an existing category in the metadata

        """
        if category not in self._metadata.columns:
            raise ValueError(f'No category with name `{category}`')
        category_values = self._metadata[category].unique()
        if exclude_na:
            category_values = category_values[~pd.isnull(category_values)]
        return list(category_values)

    def sample_id_matches(self, query):
        """

        Parameters
        ----------
        query : dict
            Expects a jquerybuilder formatted query

        Returns
        -------
        list
            The sample IDs that match the given `query`

        """
        slice_ = self._process_query(query)
        return list(self._metadata.index[slice_])

    def _process_query(self, query):
        group_fields = ["condition", "rules"]

        if _is_rule(query):
            category, op, value = query['id'], query['operator'], \
                                  query['value']
            return ops[op](self._metadata[category], value)
        else:
            for field in group_fields:
                if field not in query:
                    raise ValueError(f"query=`{query}` does not appear to be "
                                     f"a rule or a group.")
            if query['condition'] not in conditions:
                raise ValueError(f"Only conditions in {conditions} are "
                                 f"supported. Got {query['condition']}.")
            else:
                condition = conditions[query['condition']]

            return condition(self._safe_concat([self._process_query(rule) for
                                                rule in query['rules']],
                                               axis=1))

    def _safe_concat(self, list_of_df, **concat_kwargs):
        if len(list_of_df) > 0:
            return pd.concat(list_of_df, **concat_kwargs)
        return pd.DataFrame(pd.Series(True, index=self._metadata.index))
