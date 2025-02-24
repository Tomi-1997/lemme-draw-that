#!/bin/ash

gunicorn --proxy-protocol --bind 0.0.0.0:$PORT \
	   --capture-output --timeout 60 --limit-request-line 8190 \
	   --worker-class eventlet -w 1 app:app
	   