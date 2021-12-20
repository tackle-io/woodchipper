#!/usr/bin/env bash

FLASK_ENV=development FLASK_APP=app:app flask run &
FLASK_PID=$!
sleep 2s
curl -v http://localhost:5000/
kill $FLASK_PID
