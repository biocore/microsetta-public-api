import json
from pkg_resources import resource_filename
from microsetta_public_api import config
from microsetta_public_api.resources import resources

import connexion
from flask import render_template


def build_app(resources_config_json=None):
    app = connexion.FlaskApp(__name__)

    # default configuration for resources is provided in
    # microsetta.config.resources, this config can be updated by a json file
    # passed to `build_app`.
    if resources_config_json is not None:
        with open(resources_config_json) as fp:
            resource_updates = json.load(fp)
        config.resources.update(resource_updates)

        resources.update(config.resources)

    app_file = resource_filename('microsetta_public_api.api',
                                 'microsetta_public_api.yml')
    app.add_api(app_file, validate_responses=True)

    @app.route('/demos/percentiles-plot/')
    def percentiles_plot():
        return render_template('percentiles-plot.html')

    return app


if __name__ == "__main__":
    import sys
    import tempfile
    import pandas as pd
    import numpy as np
    from qiime2 import Metadata, Artifact

    class TestDB:
        n_samples = 20000
        np.random.seed(724)
        sample_set = [f'sample-{i + 1}' for i in range(n_samples)]
        age_categories = np.array(['30s', '40s', '50s'])
        bmi_categories = np.array(['Normal', 'Overweight', 'Underweight'])

        faith_pd_data = pd.Series(np.random.normal(6, 1.5, n_samples),
                                  index=sample_set, name='faith_pd')

        metadata_table = pd.DataFrame(
            {
                'age_cat': np.random.choice(age_categories,
                                            len(sample_set)),
                'bmi_cat': np.random.choice(bmi_categories,
                                            len(sample_set)),
            }, index=pd.Series(sample_set,
                               name='#SampleID')
        )

        def __init__(self):
            self._tempfiles = []

        def create_tempfile(self, **named_temporary_file_kwargs):
             new_tempfile = tempfile.NamedTemporaryFile(
                 **named_temporary_file_kwargs)
             self._tempfiles = []
             return new_tempfile

        def __enter__(self):
            metadata_file = self.create_tempfile(suffix='.txt')
            metadata_path = metadata_file.name
            Metadata(self.metadata_table).save(metadata_path)

            faith_pd_file = self.create_tempfile(suffix='.qza')
            faith_pd_path = faith_pd_file.name
            faith_pd_artifact = Artifact.import_data(
                "SampleData[AlphaDiversity]", self.faith_pd_data,
            )
            faith_pd_artifact.save(faith_pd_path)

            # this does not do encapsulation (e.g, changing config and
            # resources back to what they were before using), but would need
            # if using this test database running in test cases...
            config.resources.update({'metadata': metadata_path,
                                     'alpha_resources': {
                                        'faith-pd': faith_pd_path,
                                     }
                                     })
            resources.update(config.resources)

        def __exit__(self, exc_type, exc_val, exc_tb):
            for file_ in self._tempfiles:
                file_.close()
            config.resources.clear()
            resources.clear()
            return True

    config_fp = sys.argv[1] if len(sys.argv) > 1 else None
    if config_fp:
        app = build_app(resources_config_json=config_fp)
        app.run(port=8083, debug=True)

    else:
        with TestDB():
            app = build_app()
            app.run(port=8083, debug=True)
