# MsGraphExporter

[![Python 3.6+](https://img.shields.io/badge/Python-3.6+-blue.svg)][PythonRef] [![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)][BlackRef] [![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)][MITRef]
[![ReadTheDocs](https://readthedocs.org/projects/msgraphexporter/badge/?version=latest)][DocsRef]

[PythonRef]: https://docs.python.org/3.6/
[BlackRef]: https://github.com/ambv/black
[MITRef]: https://opensource.org/licenses/MIT
[DocsRef]: https://msgraphexporter.readthedocs.io/en/latest/

`MsGraphExporter` is an application that performs periodic export of time-domain data like Azure AD user signins from [Microsoft Graph API][MsGraphApiDoc] into a buffer key-value store (currently supports [Redis][RedisRef]) for subsequent processing. It uses [Celery][CeleryProjectRef] task queue for parallel processing, [gevent][GeventRef] greenlets for concurrent uploads, relies on the [Graph API pagination][MsGraphApiPage] to control memory footprint and respects [Graph API throttling][MsGraphApiThrottle]. The application could be deployed as a single-container worker or as a set of multiple queue-specific workers for high reliability and throughput.

[MsGraphApiDoc]: https://docs.microsoft.com/en-us/graph/overview
[MsGraphApiPage]: https://docs.microsoft.com/en-us/graph/paging
[MsGraphApiThrottle]: https://docs.microsoft.com/en-us/graph/throttling

## Getting Started

Follow these instructions to use the application.

### Installing

`MsGraphExporter` is distributed through the [Python Package Index][PyPIRef]. Run the following command to:

[PyPIRef]: https://pypi.org

* install a specific version

    ```sh
    pip install "ms-graph-exporter==0.1"
    ```

* install the latest version

    ```sh
    pip install "ms-graph-exporter"
    ```

* upgrade to the latest version

    ```sh
    pip install --upgrade "ms-graph-exporter"
    ```

* install optional DEV dependencies like `pytest` framework and plugins necessary for performance and functional testing

    ```sh
    pip install "ms-graph-exporter[test]"
    ```

### Requirements

* Python >= 3.6

## Built using

* [Celery][CeleryProjectRef] - Distributed task queue
* [gevent][GeventRef] - concurrent data upload to [Redis][RedisRef]
* [redis-py][RedisPyGithub] - Python interface to [Redis][RedisRef]

[RedisRef]: https://redis.io/
[CeleryProjectRef]:http://www.celeryproject.org/
[GeventRef]: http://www.gevent.org
[RedisPyGithub]: https://github.com/andymccurdy/redis-py

## Versioning

We use [Semantic Versioning Specification][SemVer] as a version numbering convention.

[SemVer]: http://semver.org/

## Release History

For the available versions, see the [tags on this repository][RepoTags]. Specific changes for each version are documented in [CHANGELOG.md][ChangelogRef].

Also, conventions for `git commit` messages are documented in [CONTRIBUTING.md][ContribRef].

[RepoTags]: https://github.com/undp/MsGraphExporter/tags
[ChangelogRef]: CHANGELOG.md
[ContribRef]: CONTRIBUTING.md

## Authors

* **Oleksiy Kuzmenko** - [OK-UNDP@GitHub][OK-UNDP@GitHub] - *Initial design and implementation*

[OK-UNDP@GitHub]: https://github.com/OK-UNDP

## Acknowledgments

* Hat tip to all individuals shaping design of this project by sharing their knowledge in articles, blogs and forums.

## License

Unless otherwise stated, all authors (see commit logs) release their work under the [MIT License][MITRef]. See [LICENSE.md][LicenseRef] for details.

[LicenseRef]: LICENSE.md

## Contributing

There are plenty of ways you could contribute to this project. Feel free to:

* submit bug reports and feature requests
* outline, fix and expand documentation
* peer-review bug reports and pull requests
* implement new features or fix bugs

See [CONTRIBUTING.md][ContribRef] for details on code formatting, linting and testing frameworks used by this project.
