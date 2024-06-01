#!/bin/bash

heroku login

while read line; do
  if [[ $line != \#* && $line == *=* ]]; then
    heroku config:set $line --app awebot
  fi
done < dotenv/.env.local