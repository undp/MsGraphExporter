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

### Deployment

While it is possible to run the application with `./run_exporter.sh`, `docker` deployment is the recommended approach. The project has an example `docker/docker-compose.yaml` that could be deployed with:

```sh
docker-compose --file docker/docker-compose.yaml up
```

By default, no configuration file is expected by the app. All options are taken either from the command-line interface (CLI) or the execution environment (ENV).

CLI options are the same as the config file directives. For example, config file directive `timelag: 120` corresponds to CLI option `--timelag=120`. Corresponding ENV options are upper-case names of config file directives prefixed with `GRAPH_` (e.g. `GRAPH_TIMELAG=120`). Config file takes precedence over the CLI, which in turn takes precedence over ENV.

Below is the default config file `docker/app_config.yaml` with all the default values and corresponding ENV variables mentioned in comments:

```yaml
---
# Azure AD tenant where the Service Principal with access rights
# to call the MS Graph API resides.
# (GRAPH_TENANT)
#
tenant: ""

# ClientId of the Service Principal with access to MS Graph API.
# (GRAPH_CLIENT_ID)
#
client_id: ""

# ClientSecret of the Service Principal with access to MS Graph API.
# (GRAPH_CLIENT_SECRET)
#
client_secret: ""

# Seconds to shift back the query time-frame for each of the periodic
# invocations of the parallelized extraction process.
# (GRAPH_TIMELAG)
#
timelag: 120

# Number of parallel streams to fetch time-domain data.
# (GRAPH_STREAMS)
#
streams: 2

# Time-domain size of the data request for each stream (seconds).
# (GRAPH_STREAM_FRAME)
#
stream_frame: 30

# Number of records to request from the MS Graph API in a single response.
# (GRAPH_PAGE_SIZE)
#
page_size: 50

# Backend type to store exported data. Accepts either `redis` or `log`.
# If set to `redis`, expects `queue_type`, `queue_key` and `redis_url`
# to be defined to store data in Redis. If set to `log`, outputs received
# records to Celery Worker log under severity INFO.
# (GRAPH_QUEUE_BACKEND)
#
queue_backend: redis

# Storage queue implementation type. Accepts either `list` or `channel`.
# If set to `list`, all records are accumulated for further processing.
# If set to `channel`, all records are pushed to a PUB/SUB channel for
# automatic relaying to all subscribers.
# (GRAPH_QUEUE_TYPE)
#
queue_type: list

# Name of the CHANNEL or LIST where extracted data is pushed.
# (GRAPH_QUEUE_KEY)
#
queue_key: ms_graph_exporter

# Connection string for Redis client. Follows `reids-py` URL schema with
# `redis://` for regular Redis instance and `rediss://` for TLS. In case
# authentication is required, use `redis://:<password>@redis.host.org:<port>`
# where `<password>` is URL-encoded.
# (GRAPH_REDIS_URL)
#
redis_url: redis://localhost:6379?db=0

# Maximum number of Greenlets to spawn for each data upload task. Storage
# task splits list of records into the appropriate amount of chunks not
# greater than `greenlets_count + 1` (byproduct of int-based modulo calc)
# and spawns each chunk upload as a Greenlet co-routine.
# (GRAPH_GREENLETS_COUNT)
#
greenlets_count: 10

# Enable/disable threat-safe blocking in Redis connection pool.
# (GRAPH_REDIS_POOL_BLOCK)
#
redis_pool_block: True

# Enable/disable `gevent.queue.LifoQueue` usage in Redis connection pool.
# (GRAPH_REDIS_POOL_GEVENT_QUEUE)
#
redis_pool_gevent_queue: True

# Maximum number of reusable connections maintained by the connection pool
# of the Redis client.
# (GRAPH_REDIS_POOL_MAX_CONNECTIONS)
#
redis_pool_max_connections: 15

# Time that blocking-enabled Redis client waits for connection to become
# available from the exhausted connection pool (seconds). Afterwards, raises
# Redis ConnectionError exception.
# (GRAPH_REDIS_POOL_TIMEOUT)
#
redis_pool_timeout: 1
```

Here is also the output of the app worker `--help` option:

```sh
$ celery worker --app=ms_graph_exporter.celery.app --help
[...snip...]
User Options:
  --app_config GRAPH_APP_CONFIG
                        YAML-based configuration file. By default, no config
                        file is expected by the app. All options are taken
                        either from the command-line interface (CLI) or the
                        execution environment (ENV). Config file directives
                        are the same as the CLI options listed below.
                        Corresponding ENV options are upper-case names of CLI
                        options prefixed with 'GRAPH_'. Config file takes
                        precedence over the CLI, which in turn takes
                        precedence over ENV.
  --client_id GRAPH_CLIENT_ID
                        ClientId of the Service Principal with access to MS
                        Graph API.
  --client_secret GRAPH_CLIENT_SECRET
                        ClientSecret of the Service Principal with access to
                        MS Graph API.
  --greenlets_count GRAPH_GREENLETS_COUNT
                        Maximum number of Greenlets to spawn for each data
                        upload task.
  --page_size GRAPH_PAGE_SIZE
                        Number of records to request from the MS Graph API in
                        a single response.
  --queue_backend {redis,log}
                        Backend type to store exported data.
  --queue_type {list,channel}
                        Storage queue implementation type.
  --queue_key GRAPH_QUEUE_KEY
                        Name of the CHANNEL or LIST where extracted data is
                        pushed.
  --redis_url GRAPH_REDIS_URL
                        Connection string for Redis client.
  --redis_pool_block    Enable threat-safe blocking in Redis connection pool.
  --no-redis_pool_block
                        Disable threat-safe blocking blocking in Redis
                        connection pool.
  --redis_pool_gevent_queue
                        Enable `gevent.queue.LifoQueue` usage in Redis
                        connection pool.
  --no-redis_pool_gevent_queue
                        Disable `gevent.queue.LifoQueue` usage in Redis
                        connection pool.
  --redis_pool_max_connections GRAPH_REDIS_POOL_MAX_CONNECTIONS
                        Maximum number of reusable connections maintained by
                        the connection pool of the Redis client.
  --redis_pool_timeout GRAPH_REDIS_POOL_TIMEOUT
                        Time that blocking-enabled Redis client waits for
                        connection to become available from the exhausted
                        connection pool (seconds). Afterwards, raises Redis
                        ConnectionError exception.
  --streams GRAPH_STREAMS
                        Number of parallel streams to fetch time-domain data.
  --stream_frame GRAPH_STREAM_FRAME
                        Time-domain size of the data request for each stream
                        (seconds).
  --tenant GRAPH_TENANT
                        Azure AD tenant where the Service Principal with
                        access rights to call the MS Graph API resides.
  --timelag GRAPH_TIMELAG
                        Seconds to shift back the query time-frame for each of
                        the periodic invocations of the parallelized
                        extraction process.
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
