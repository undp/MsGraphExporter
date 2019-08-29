#!/bin/sh

celery beat \
    --app=ms_graph_exporter.celery.app \
    --loglevel=INFO \
& celery worker \
    --app=ms_graph_exporter.celery.app \
    --concurrency=10 \
    --hostname='combo_worker@ms_graph_exporter' \
    --loglevel=INFO \
    --pool=gevent \
    --purge \
    --queues=graph.map,graph.fetch,graph.store \
&& fg