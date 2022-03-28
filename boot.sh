#!/usr/bin/env bash

# this script is used to boot a Docker container
source venv/bin/activate
while true; do
    # If dev mode, run migration
    if [ -v DEV_MODE ]; then
        flask db migrate
    fi

    # Run dp upgrade
    flask db upgrade

    if [[ "$?" == "0" ]]; then
        break
    fi
    echo Deploy command failed, retrying in 5 secs...
    sleep 5
done

# Create default admin
flask create-admin

exec gunicorn --workers 8 -b :5000 --access-logfile - --error-logfile - srdp:app
