# microsetta-public-api
A public microservice to support The Microsetta Initiative

## Installation
Create a new `conda` environment:

`conda create -n microsetta-public-api python=3.7 flask`

Once the conda environment is created, activate it:

`conda activate microsetta-public-api`

Install QIIME 2 dependencies:

`conda install -c qiime2 qiime2 q2-types`

Install connexion version 2.0 (which supports the OpenAPI Specification 3.0) as well as the Swagger UI:

`pip install "connexion[swagger-ui]" pyyaml`

Then install the microsetta-public-api in editable mode:

`pip install -e .`

## Test Usage

In the activated conda environment, start the microservice using flask's built-in server by running, e.g., 

`python ./microsetta_public_api/server.py`

which will start the server on http://localhost:8083 . Note that this usage is suitable for 
**development ONLY**--real use of the service would require a production-level server. 

The Swagger UI should now be available at http://localhost:8083/api/ui .

## Configuring data sources

You can use a JSON file to configure data resources for the server.

### Alpha Diversity
The Microsetta Public Server can be configured to serve [QIIME2](https://qiime2.org/)
artifacts (`.qza` files) for artifacts by including an `"alpha_resources"` key
in a configuration `JSON`. The value is expected to be a dictionary of `"<metric>": "</file/path/name.qza>"` pairs,
where `"<metric>"` is the name of the metric stored by the QZA and `"</file/path/name.qza>"` is a path to the QZA
on the host server.

### Features tables (with taxonomy)
The server can also be configured to serve information from feature tables with corresponding taxonomic
feature data. Tables can either be QZA `FeatureTable`'s or biom tables. If a `biom` table is supplied,
the `"table-format": "biom"` option must be specified. Taxonomy data is accepted with the
`"feature-data-taxonomy"` keyword, which should correspond to the filepath to a QIIME2 `FeatureData[Taxonomy]`.

For large datasets, creating a Taxonomy model can be slow. You can cache the model on server startup by adding the
`"cache-taxonomy": true` keyword to your specific table. This should speed up the time for API calls.

### Metadata
The server can be configured to contain metadata, by adding a  `"metadata"` keyword to the config,
that gives a path to a QIIME2 formatted metadata file.

`sample_config.json`:
```json
{
  "alpha_resources": {
    "faith_pd": "/path/to/faith_pd.qza",
    "observed_otus": "/path/to/observed/otus/metric.qza",
    "chao1": "/some/other/path/values.qza"
  },
  "table_resources": {
    "taxonomy": {
      "table": "/path/to/table.biom",
      "table-format": "biom",
      "feature-data-taxonomy": "/path/to/a/taxonomy-data.qza",
      "cache-model": true
    }
  },
  "metadata": "/path/to/some/metadata.txt"
}
```

This can then be provided to `microsetta_public_api.server.build_app`, e.g.,:

```python
from microsetta_public_api.server import build_app
app = build_app(resources_config_json='sample_config.json')
app.run(port=8083, debug=True)
```
