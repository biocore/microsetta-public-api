from qiime2 import Artifact
from skbio import DistanceMatrix
from microsetta_public_api.utils.testing import TempfileTestCase
from microsetta_public_api._io import _dict_of_paths_to_beta_data


class TestResourceIO(TempfileTestCase):

    def test_load_beta_data(self):
        self.dm = DistanceMatrix(
            [
                [0, 1, 2],
                [1, 0, 3],
                [2, 3, 0],
            ], ids=['s1', 's2', 's3'],
        )

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
        }, '__beta__')

        self.assertDictEqual(
            {'beta1': self.dm},
            obs_dm)
