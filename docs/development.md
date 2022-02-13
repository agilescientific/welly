# Development

If you'd like to develop `welly`, this page should help you get started.


## Installation

You can install this package with `pip`. The `dev` option will install the packages you need for testing and building the documentation.

    pip install welly[dev]


## Contributing

If you'd like to contribute pull requests back to the main `welly ` project, please see [`CONTRIBUTING.md`](https://github.com/agile-geoscience/welly/blob/main/CONTRIBUTING.md).


## Testing

You can run the tests (requires `pytest` and `pytest-cov`) with

    python run_tests.py

Most of the tests are `doctest` tests, which are contained in the docstrings of this package's functions. It is also possible to add test files to the `tests` folder in the normal way.


## Building the package

This repo uses PEP 517-style packaging. [Read more about this](https://setuptools.pypa.io/en/latest/build_meta.html) and [about Python packaging in general](https://packaging.python.org/en/latest/tutorials/packaging-projects/).

Building the project requires `build`, so first:

    python -m pip install build

Then to build `welly` locally:

    python -m build

This builds both `.tar.gz` and `.whl` files, either of which you can install with `pip`.


## Building the docs

You can build the docs with the following command in the root directory:

    sphinx-build -E -b html docs docs/_build/html

You can also run `make html` from the `docs` directory.

There is a continuous integration script to update welly's docs on all published releases.


## Continuous integration

This repo has two GitHub 'workflows' or 'actions':

- Push to `main`: Run all tests on all version of Python. This is the **Build and test** workflow.
- Publish a new release: Build and upload to PyPI. This is the **Publish to PyPI** workflow. Publish using the GitHub interface, for example ([read more](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository)).
