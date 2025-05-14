# PriceCypher Python SDK

Python wrapper around the different PriceCypher APIs.

## Usage
### Installation
Simply execute `pip install pricecypher-sdk`

### Dataset SDK
```python
from pricecypher import Datasets

datasets = Datasets(BEARER_TOKEN)

datasets.index()
datasets.get_meta(DATASET_ID)
datasets.get_scopes(DATASET_ID)
datasets.get_scope_values(DATASET_ID, SCOPE_ID)
datasets.get_transaction_summary(DATASET_ID)

columns = [
    {'name_dataset': 'cust_group', 'filter': ['Big', 'Small'], 'key': 'group'},
    {'representation': 'cost_price', 'aggregate': 'sum', 'key': 'cost_price'}
]
datasets.get_transactions(DATASET_ID, AGGREGATE, columns)
```

### Config SDK
```python
from pricecypher import ConfigSections

config = ConfigSections(BEARER_TOKEN, DATASET_ID)

# Print available config sections
print(config.index())
# Print config key-value pairs for `monitoring` section.
print(config.get_parsed_section('monitoring'))
# Non-existent config section returns empty dict.
print(config.get_parsed_section('nonexistent'))
```

### Contracts
The `Script`, `ScopeScript`, and `QualityTestScript` abstract classes can be extended with their abstract methods
implemented to create scripts usable in other services.

The `ScopeScript` in particular is intended for scripts that calculate values of certain scopes for transactions.

The `QualityTestScript` is intended for scripts that check the quality of a data intake and produce a standardized
output that can be visualized and/or used by other services.

See the documentation on the abstract functions for further specifics.

### Environment variables

| Variable          | Description                                                                |
|-------------------|----------------------------------------------------------------------------|
| CUSTOM_DNS_DOMAIN | Use for custom domain resolution of (wildcard) domain to `$CUSTOM_DNS_IP`. |
| CUSTOM_DNS_IP     | IP address the `CUSTOM_DNS_DOMAIN` should resolve to.                      |
| SSL_VERIFY        | Boolean value to specify whether SSL certificates should be verified.      |


## Development

These instructions will get you a copy of the project up and running on your local machine for development and testing
purposes.

### Prerequisites

* Python >= 3.10

### Setup
The `endpoints` module models the different PriceCypher API endpoints. Each file represents a different API and the
contents of each file are structured into the different endpoints that are provided by the API.
Similarly, each file in the `models` module defines the models that are provided by the different APIs.

The SDK that this package provides is contained in the top-level package contents.

## Deployment
1. Execute `python3 -m build` to build the source archive and a built distribution.
2. Execute `python3 -m twine upload dist/*` to upload the package to PyPi.

## Authors

* **Marijn van der Horst** - *Initial work*
* **Pieter Voors** - *Contracts for Script and ScopeScript*

See also the list of [contributors](https://github.com/marketredesign/pricecypher_python_sdk/contributors) who participated in this project.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details
