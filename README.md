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
pip install -e .[dev]
```

We recommend you install [pre-commit](https://pre-commit.com/) and install the pre-commit hooks using:

```
pre-commit install
```


## Releasing to PyPI

Releases are handled through GitHub Actions by tagging a revision in GitHub. To release version 0.13.37:

```
# Obviously adjust the version number to the version you're releasing, but it must be of the form vX.Y or vX.Y.Z
git tag -a v0.13.37 -m "Releasing v0.13.37"
git push origin --tags
```
