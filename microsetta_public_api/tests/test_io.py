from qiime2 import Artifact
from skbio import DistanceMatrix
import pandas as pd
import pandas.testing as pdt
from microsetta_public_api.utils.testing import TempfileTestCase
from microsetta_public_api._io import (_dict_of_paths_to_beta_data,
                                       _closest_k_from_distance_matrix)


class TestResourceIO(TempfileTestCase):

    def test_load_beta_data(self):
        self.dm = DistanceMatrix(
            [
                [0, 2, 1, 4],
                [2, 0, 3, 5],
                [1, 3, 0, 4.1],
                [4, 5, 4.1, 0]
            ], ids=['s1', 's2', 's3', 's4'],
        )

        exp = pd.DataFrame([['s3', 's2', 's4'],
                            ['s1', 's3', 's4'],
                            ['s1', 's2', 's4'],
                            ['s1', 's3', 's2']],
                           index=['s1', 's2', 's3', 's4'],
                           columns=['k0', 'k1', 'k2'])
        exp.index.name = 'sample_id'
        self.dm_fh = self.create_tempfile(suffix='.qza')
        self.dm_path = self.dm_fh.name

        q2_dm = Artifact.import_data(
            "DistanceMatrix",
            self.dm,
        )
        q2_dm.save(self.dm_path)
        self.dm_fh.flush()

        obs_dm = _dict_of_paths_to_beta_data({
            'beta1': self.dm_path,
        }, '__beta__')['beta1']

        pdt.assert_frame_equal(obs_dm, exp)

    def test_closest_k_from_distance_matrix(self):
        dm = DistanceMatrix(
            [
                [0, 1, 2, 4, 5, 6],
                [1, 0, 3, 4, 5, 6],
                [2, 3, 0, 1, 1, 1],
                [4, 4, 1, 0, 2, 1],
                [5, 5, 1, 2, 0, 3],
                [6, 6, 1, 1, 3, 0],
            ], ids=['s1', 's2', 's3', 's4', 's5', 's6'],
        )
        exp = pd.DataFrame([['s2', 's3'],
                            ['s1', 's3'],
                            ['s4', 's5'],
                            ['s3', 's6'],
                            ['s3', 's4'],
                            ['s3', 's4']],
                           index=['s1', 's2', 's3', 's4', 's5', 's6'],
                           columns=['k0', 'k1'])
        exp.index.name = 'sample_id'
        obs = _closest_k_from_distance_matrix(dm, 2)
        pdt.assert_frame_equal(obs, exp)
