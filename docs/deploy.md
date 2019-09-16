# Deployment and configuration

## Deployment

While it is possible to run the application with `./run_exporter.sh`, `docker` deployment is the recommended approach. The project has an example `docker/docker-compose.yaml` that could be deployed with:

```sh
docker-compose --file docker/docker-compose.yaml up
```

## Configuration

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
