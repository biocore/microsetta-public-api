# microsetta-public-api
A public microservice to support The Microsetta Initiative

## Installation

Create a new `conda` environment using the continuous integration (CI) scripts.
By default, the name of the created environment will be `test-microsetta-public`.
You may edit ci/conda_requirements.yml to change the name as you see fit.

 `conda env create -f ci/conda_requirements.yml`

This will ensure that an environment can be created that satisifies all dependencies.

Once the conda environment is created, activate it:

 `conda activate test-microsetta-public`

Install additional requirements from pip:

 `pip install -r ci/pip_requirements.txt`

Then install the microsetta-public-api in editable mode:
`make dev`

Test installation by running unittests:

 `make test`

## Test Usage

In the activated conda environment, start the microservice using flask's built-in server by running, e.g., 

`python ./microsetta_public_api/server.py`

which will start the server on http://localhost:8084 . Note that this usage is suitable for 
**development ONLY**--real use of the service would require a production-level server. 

The Swagger UI should now be available at http://localhost:8084/api/ui .

## Configuring data sources

You can use a JSON file to configure data resources for the server.

### Datasets
The Microsetta Public Results API has the notion of a _dataset_. A dataset is a collection of artifacts 
(such as metadata, alpha diversity, ordinations, etc.). In terms of the configuration file, a dataset is
represented as a JSON object, with special keywords/attributes (e.g., `__metadata__`) for each of its constituent parts.
Generally, the attributes of a dataset are optional.


### Dataset attributes
#### Metadata
Attribute: `__metadata__`

This provides the path to a metadata file, which should be formatted to be compatible with QIIME2. 

#### Dataset Details
Attribute: `__dataset_detail__`

This object stores details about the dataset, including (but not limited to) a description, qiita study ID(s), and
the data type of the study/studies.

#### Features/Taxonomy
Attribute: `__taxonomy__`

This attribute contains arbitrarily-named attributes corresponding to taxonomic feature data.
Each attribute of the object, keyed by some key `<taxonomy>`, has the following structure:
* Tables can be paths to QZA `FeatureTable`. In the config, the table is keyed by `table`.
* Taxonomy data associated with the table is accepted with the `feature-data-taxonomy` keyword,
  which should correspond to the filepath to a QIIME2 `FeatureData[Taxonomy]`.


#### Alpha Diversity
Attribute: `__alpha__`

This attribute contains arbitrarily-named attributes corresonding to alpha diversity series.
Each attribute of the object, keyed by `<alpha-metric>`, contains a path that
corresponds to a `SampleData[AlphaDiveristy]` QZA.


#### Beta Diversity
Attribute: `__beta__`

Beta diversity is similar to alpha diversity, except each key/metric should correspond to a distance matrix QZA.

#### Ordination
Keyword: `__pcoa__`

This attribute contains arbitrarily-named attributes corresponding to different sample sets with ordinations.
Each sample set, keyed by `<sample-set-name>`, has an object with attributes corresponding to a beta metric, and the
value of that attribute corresponds to a file path to the ordination.

### Sample configuration file

The following shows 
`sample_config.json`:
```json
{
  "resources":{
    "datasets": {
      "16S": { 
        "__dataset_detail__": {
            "title": "Microsetta 16S",
            "qiita-study-ids": ["10317"],
            "datatype": "16S"
        },
        "__metadata__": "/Users/microsetta-public-api/metadata/ag.txt",
        "__beta__": {
          "unweighted-unifrac": "/Users/microsetta-public-api/beta/unweighted_unifrac.qza",
          "weighted-unifrac": "/Users/microsetta-public-api/beta/weighted_unifrac.qza"
        },
        "__alpha__": {
          "faith_pd": "/Users/microsetta-public-api/alpha/faith_pd.qza",
          "shannon": "/Users//microsetta-public-api/alpha/shannon.qza"
        },
        "__taxonomy__": {
          "taxonomy": {
            "table": "/Users/microsetta-public-api/feature-table/ag.biom.qza",
            "feature-data-taxonomy": "/Users/microsetta-public-api/taxa/ag.fna.taxonomy.qza"
          },
          "alternate-taxonomy": {
            "table": "/Users/microsetta-public-api/feature-table/ag.biom.alt.qza",
            "feature-data-taxonomy": "/Users/microsetta-public-api/taxa/ag.fna.alt.taxonomy.qza"
          }
        },
        "__pcoa__": {
            "fecal": {
                "unweighted-unifrac": "/Users/microsetta-public-api/pcoa/unweighted-unifrac/unweighted_unifrac.qza",
                "weighted-unifrac": "/Users/microsetta-public-api/pcoa/weighted-unifrac/weighted_unifrac.qza"
            }
        }
      },
      "MG": { 
        "__dataset_detail__": {
            "title": "Microsetta Metagenomics",
            "qiita-study-ids": ["10317"],
            "datatype": "WGS"
        },
        "__metadata__": "/Users/microsetta-public-api/metadata/ag.wgs.txt",
        "__beta__": {
          "unweighted-unifrac": "/Users/microsetta-public-api/beta/unweighted_unifrac.wgs.qza",
          "weighted-unifrac": "/Users/microsetta-public-api/beta/weighted_unifrac.wgs.qza"
        }
      }
    }
  },
  "port": 8082
}
```

This can then be provided to the API by setting the `MPUBAPI_CFG` environment variable:

```bash
export MPUBAPI_CFG=sample_config.json
```

and then started with the following python commands:
```python
from microsetta_public_api.server import build_app, run
app = build_app()
run(app)
```

Alternatively, you can simply run
```bash
python microsetta_public_api/server.py
```
