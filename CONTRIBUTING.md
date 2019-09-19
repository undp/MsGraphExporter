# Contributing

This projects follows the [Gitflow workflow][WorkflowRef]. When contributing, please discuss the change you wish to make via [Issues][IssuesRef], email, or any other method with the maintainers of this repository before raising a [Pull Request](#pull-request-process).

[WorkflowRef]: https://www.atlassian.com/git/tutorials/comparing-workflows/gitflow-workflow
[IssuesRef]: https://github.com/undp/MsGraphExporter/issues

## Dev Environment

To ensure version consistency with all required dependencies, you would need to use `poetry`. See the [Dependencies](#dependencies) section below on how to install it.

To start with the project:

```sh
git clone https://github.com/undp/msgraphexporter.git MsGraphExporter
cd MsGraphExporter
poetry install
pre-commit install
```

### Dependencies

We build our project into a package and distribute it through the PyPI with `poetry`. We also use it to manage code dependencies. You would need to have `poetry` installed with the following command:

```sh
curl -sSL https://raw.githubusercontent.com/sdispater/poetry/master/get-poetry.py | python
```

### Formatting

To make our development more efficient and our code more consistent, we cede control over code formatting to `black`. As explained on [black's GitHub page][BlackGitHub]:

[BlackGitHub]: https://github.com/python/black

> Black is the uncompromising Python code formatter. [...] Blackened code looks the same regardless of the project you're reading. Formatting becomes transparent after a while and you can focus on the content instead.

Code examples from Python `docstrings` (documentation embedded into the code) are also formatted using `black` conventions with the help of `blacken-docs` tool.

Also, some IDEs like [Visual Studio Code][VSCodeGitHub] allow `black` formatting action to be performed on each file saving operation, if configured. To have `black` and `blacken-docs` tools for manual usage from the command-line or by your IDE, install them with the following command in your virtual environment:

```sh
poetry install -v --no-dev --extras=code-format
```

[VSCodeGitHub]: https://github.com/Microsoft/vscode

`black` formatter is automatically executed prior to committing changes to this repository with the help of `pre-commit` tool.

### Linting

This project relies on the `flake8` linter with the following plugins installed:

* `flake8-import-order` - checks the ordering of imports
    > Note: this project uses `cryptography` ordering style
* `flake8-bandit` - checks for common security issues with `bandit`
* `flake8-blind-except` - checks for blind `except:` statements
* `flake8-bugbear` - finds likely bugs and design problems
* `flake8-builtins` - validates that names of variables or parameters do not match Python builtins
* `flake8-docstrings` - checks [PEP 257][PEP-257] docstring conventions with `pydocstyle`
* `flake8-logging-format` - checks logging format strings
* `flake8-mypy` - performs type checking with `mypy`
* `pep8-naming` - checks [PEP 8][PEP-8] naming conventions

[PEP-257]: https://www.python.org/dev/peps/pep-0008/

Similarly to the `black` formatting, linting with `flake8` is executed at every commit by `pre-commit` tool.

If you want to install `flake8` for manual usage or IDE integration, run the following command in your virtual environment:

```sh
poetry install -v --no-dev --extras=code-lint
```

### Testing

This project uses `pytest` framework to outline unit, functional and performance tests and `tox` to manage test environments and the workflow.

Since our functional tests expect some Redis infrastructure to be available, you would need to have one available in your dev environment (see `docker/docker-compose.yaml` for an example on how to deploy local Redis instance with `docker`).

Our tests rely on the following `pytest` plugins:

* `pytest-benchmark` - to run performance benchmarks
* `pytest-cov` - to ensure adequate test coverage
* `pytest-dockerc` - to deploy `docker-compose.yaml` into the test environment
* `pytest-instafail` - to report failures while the test run is happening
* `pytest-lazy-fixture` - to use test fixtures in `pytest.mark.parametrize` decorator
* `pytest-random-order` - to randomize the order in which tests are run

> **NOTE:** We expect 90% or more of the code in this project to be covered with tests, otherwise testing is configured to fail. We try to maintain this test coverage level and would ask you to cover features or bug fixes you introduce with enough test code.

In order to get just the packages to facilitate testing, run:

```sh
poetry install -v --extras=test
```

#### Sensitive Credentials

In order to provide credentials for functional tests following ENV variables have to be defined:

* `GRAPH_CLIENT_ID` - `ClientId` of the Service Principal with access to MS Graph API.
* `GRAPH_CLIENT_SECRET` - `ClientSecret` of the Service Principal with access to MS Graph API.
* `GRAPH_TENANT` - Azure AD `tenant` where the Service Principal with access rights to call the MS Graph API resides.

#### Limitations

All tests marked as `@pytest.mark.functional` are functional in nature and would require some live service to test against (e.g. MS Graph API). To exclude these tests run `pytest` with `-m "not functional"` option. By default, all test environments defined in `tox.ini` except `ms_graph` would exclude functional tests.

Also, `instance/data/data_benchmark.json` is expected to contain some data for performance testing. For benchmarks to be representative, it is highly recommended to use **10k records or more**  for benchmarking against the **remote Redis instance** accessible over the real-life network and not local Redis available through loopback interface.

#### Execute

To run all tests for all available versions of Python and generate HTML docs as well as test coverage reports, execute:

```sh
tox
```

If you want to execute a specific test environment mentioned in the `envlist` variable under `[tox]` section of the `tox.ini` file, run:

```sh
tox -e <env-name>
```

For example, you could just run linting with:

```sh
tox -e linting
```

Or, test the MS Graph API functionality on Python3.6 with:

```sh
tox -e py36-functional
```

### Commit messages

This project uses `gitchangelog` to automatically generate the content of [CHANGELOG.md](CHANGELOG.md). So, it is important to follow a convention on how to format your `git commit` messages. In general, all commit messages should follow the structure below:

```sh
<subject>
<BLANK LINE>
<body>
```

`<subject>` should follow the standard `gitchangelog` convention below. See  `gitchangelog.rc` [example][GitHubGitchangelog] on GitHub for more information.

[GitHubGitchangelog]: https://github.com/vaab/gitchangelog/blob/master/.gitchangelog.rc

* `ACTION: [AUDIENCE:] SUBJ_MSG [!TAG ...]`

* `ACTION` indicates **WHAT** the change is about.
  * `chg` is for refactor, small improvement, cosmetic changes, etc
  * `fix` is for bug fixes
  * `new` is for new features, big improvement

* `AUDIENCE` indicates **WHO** is concerned by the change.
  * `dev`  is for developers (API changes, refactoring...)
  * `user`  is for final users (UI changes)
  * `pkg`  is for packagers (packaging changes)
  * `test` is for testers (test only related changes)
  * `doc`  is for tech writers (doc only changes)

* `SUBJ_MSG` is the subject itself.

* `TAGs` are for commit filtering and are preceded with `!`. Commonly used tags are:
  * `refactor` is obviously for refactoring code only
  * `minor` is for a very meaningless change (a typo, adding a comment)
  * `cosmetic` is for cosmetic driven change (re-indentation, etc)
  * `wip` is for partial functionality.

* `EXAMPLES`:
  * `new: usr: support of bazaar implemented.`
  * `chg: re-indent some lines. !cosmetic`
  * `new: dev: update code to be compatible with killer lib ver1.2.3.`
  * `fix: pkg: update year of license coverage.`
  * `new: test: add tests around usability of feature Foo.`
  * `fix: typo in spelling. !minor`

### Documentation

We strive to keep our code well documented with Python [docstrings][PEP-257-docstring]. This approach streamlines documentation maintenance by keeping it in one place with the code. Our project follows [NumPy Style][NumPyDocstrings] convention for `docstrings` to make them easy to read.

[PEP-257-docstring]: https://www.python.org/dev/peps/pep-0257/#what-is-a-docstring
[NumPyDocstrings]: https://numpydoc.readthedocs.io/en/latest/format.html#docstring-standard

Also, we generate well-structured HTML documentation out of docstrings with `sphinx` using `ReadTheDocs` theme. Here are the packages required for that:

```sh
poetry install -v --no-dev --extras=docs
```

You could generate local version of the HTML documentation (placed in `docs/_build/`) for this project with the following command:

```sh
tox -e docs
```

[RealPythonDocs]: https://realpython.com/documenting-python-code/

### Debugging

To debug and troubleshoot you could increase logging level in Celery worker with `--loglevel DEBUG`.Also, You could enable log output while running tests by editing `[pytest]` section of `tox.ini` and having `log_cli = true` there. This would allow you to have more details on how tests are executed and address possible issues.

## Pull Request Process

1. Clone the repo to your workstation:

    ```sh
    git clone https://github.com/undp/msgraphexporter.git MsGraphExporter
    ```

1. Switch to the `develop` branch:

    ```sh
    git checkout develop
    ```

1. Create a new feature branch named `feature/fooBar` from the `develop` branch:

    ```sh
    git checkout -b feature/fooBar
    ```

1. Introduce your modifications locally. Don't forget about corresponding tests!

1. Commit your changes. Ensure your commit message follows the formatting convention [described above](#commit-messages).

    ```sh
    git commit -am "new: usr: add fooBar feature. (close #123)"
    ```

1. Push the `feature/fooBar` branch to the remote origin

    ```sh
    git push origin feature/fooBar
    ```

1. Create a new Pull Request for the repo.

1. You may merge the Pull Request in once you have the sign-off from a repo owner. Or, if you do not have permission to merge, you may request the reviewer to merge it for you.
