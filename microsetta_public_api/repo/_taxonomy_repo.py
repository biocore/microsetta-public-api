from microsetta_public_api.resources import resources


class TaxonomyRepo:

    tables = None

    def __init__(self):
        tables = resources.get('table_resources', dict())

        def has_taxonomy(_, resource):
            return 'feature-data-taxonomy' in resource and 'table' in resource

        self.tables = dict(filter(lambda x: has_taxonomy(*x), tables.items()))

    def _get_resource(self, name, component=None):
        if name not in self.tables:
            raise ValueError(f'No table with taxonomy available for `{name}`')
        else:
            res = self.tables[name]
            if component is not None:
                # should always give a table and data for
                #  'feature-data-taxonomy' and 'table', but may return None
                #  for 'variances
                res = res.get(component, None)
            return res

    def resources(self):
        """Return the tables that have taxonomy information accompanying them

        Returns
        -------
        list of str:
            Names of tables that this repo has configured with taxonomy

        """
        return list(self.tables.keys())

    def table(self, table_name):
        """Obtains subset of a table for a list of samples

        Parameters
        ----------
        sample_ids : str or list of str
            Ids for which to obtain taxonomy group.

        table_name : str
            Table to use

        """
        return self._get_resource(table_name, component='table')

    def feature_data_taxonomy(self, table_name):
        return self._get_resource(table_name,
                                  component='feature-data-taxonomy')

    def variances(self, table_name):
        return self._get_resource(table_name, component='variances')

    def exists(self, sample_ids, table_name):
        """Checks if sample_ids exist for the given table.

        Parameters
        ----------
        sample_ids : str or list of str
            Ids for to check database for.

        table_name : str
            Table to check

        Returns
        -------
        bool or list of bool
            If sample_ids is str, then this returns a bool corresponding to
            whether the given sample ID exists. If given a list, each entry
            `i` corresponds to whether `sample_ids[i]` exists
            in the database.

        """
        table_resource = self._get_resource(table_name)
        if isinstance(sample_ids, str):
            # table_resource['table'] will be a biom table
            return sample_ids in table_resource['table'].ids()
        else:
            existing_ids = set(table_resource['table'].ids())
            return [(id_ in existing_ids) for id_ in sample_ids]
