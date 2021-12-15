# Woodchipper

A library to support contextual structured logging with related observability metrics.

Woodchipper was written during an internal hackathon at [tackle.io](https://tackle.io/).

## Installing

```
pip install woodchipper
```

## Creating a developer environment

After cloning the repository, setting up a virtual environment, and activating it...

```
pip install -e .
pip install -r requirements-dev.txt
```

We recommend you install [pre-commit](https://pre-commit.com/) and install the pre-commit hooks using:

```
pre-commit install
```

If you add new dependencies to the project, put them in the `setup.cfg` file and regenerate the `requirements.txt`
file using:

```
pip-compile --output-file=requirements.txt setup.cfg
```

Any dependencies for development or testing should go in the appropriate `requirements-(dev|test).in` file, before
running `pip-compile` against that file.

## Releasing to PyPI

```
python -m build
# Test your upload first
twine upload -r testpypi dist/*
# If everything looks good, upload for real
twine upload dist/*
```
