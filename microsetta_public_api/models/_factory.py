import biom
import pandas as pd
from microsetta_public_api.models._exceptions import UnknownID
from microsetta_public_api.models._taxonomy import Taxonomy


class Resources:
    def __init__(self, config):
        self._config = config
        self._biom = self._load_biom()
        self._alpha = self._load_alpha()
        self._taxonomy = self._load_taxonomy()

    def get_biom(self):
        return self._biom

    def get_alpha(self):
        return self._alpha

    def get_taxonomy(self):
        return self._taxonomy_tree, self._taxonomy_observed

    # plate holders for loading, perhaps pull from q2 qzas?
    def _load_biom(self):
        return biom.load_table(self._config.biom_path)

    def _load_alpha(self):
        df = pd.read_csv(self._config.alpha_path, sep='\t', dtype=str)
        df.set_index('sample-id', inplace=True)
        for c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='raise')
        return df

    def _load_taxonomy(self):
        taxonomy_observed = pd.read_csv(self._config.taxonomy_observed)
        variances = pd.read_csv(self._config.taxonomy_variances)
        self._taxonomy = Taxonomy(self._biom, taxonomy_observed,
                                  variances=variances)
        return self._taxonomy


class AlphaFactory:
    def __init__(self, resource):
        self._resource = resource

    def collection(self):
        """What metrics are known"""
        def f() -> list:
            return list(self._resource.get_alpha().columns)
        return f

    def samples(self):
        """Get alpha values for specific samples"""
        def f(samples: list) -> pd.DataFrame:
            dataframe = self._resource.get_alpha()

            if not set(samples).issubset(set(dataframe.index)):
                raise UnknownID(', '.join(set(samples) - set(dataframe.index)))

            return dataframe.loc[list(samples)]
        return f


# class RouteFactory:
#     _exception_to_status = {UnknownID: 404}
#
#     def __init__(self, app, config):
#         self.app = app
#         self.config = config
#
#     def construct(self, name):
#         details = self.config.routes.get(name)
#         if details is None:
#             raise KeyError("%s is not known" % name)
#
#         route = details['route']
#         actions = details['actions']
#
#         @app.route(route, methods=actions)
#         def _routeable(*args, **kwargs):
#             status = 200
#             try:
#                 result = f(*args, **kwargs)
#             except Exception as e:
#                 type_ = e.__class__
#                 status = self._exception_to_status.get(type_, 500)
#             return result
#         return _routable
