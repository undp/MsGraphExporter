#!/bin/sh
set -e

BEAT="false"
HOSTNAME=""
QUEUES=""
WORKER="false"

parse_args()
{
  while [[ $# -gt 0 ]]; do
    key="$1"
    case "$key" in
        # Celery Beat scheduler
        --beat)
        BEAT="true"
        ;;
        # Celery Worker subscribed for `graph.fetch` queue
        --fetch)
        WORKER="true"
        QUEUES="${QUEUES},graph.fetch"
        HOSTNAME="${HOSTNAME}_stream"
        ;;
        # Celery Worker subscribed for `graph.map` queue
        --map)
        WORKER="true"
        QUEUES="${QUEUES},graph.map"
        HOSTNAME="${HOSTNAME}_map"
        ;;
        # Celery Worker subscribed for `graph.store` queue
        --store)
        WORKER="true"
        QUEUES="${QUEUES},graph.store"
        HOSTNAME="${HOSTNAME}_store"
        ;;
        *)
        # Unknown option
        echo "Unknown option '$key'"
        exit 1
        ;;
    esac

    shift
  done
}


if [ "$1" = 'msgraphexporter' ]; then
    shift
    parse_args $@

    export SUPERVISORD_ENABLE_BEAT=${BEAT}
    export SUPERVISORD_ENABLE_WORKER=${WORKER}

    export CELERY_WORKER_HOSTNAME="worker${HOSTNAME}@ms_graph_exporter.%h"
    export CELERY_WORKER_QUEUES="${QUEUES}"

    supervisord -c supervisord.conf
else
    exec "$@"
fi
