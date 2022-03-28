#! /bin/bash

# Load and check environment variables
eval "$(shdotenv)"

# Script to launch app in development mode
source venv/bin/activate
export FLASK_APP=srdp.py
export FLASK_ENV=development

# Ensure env variables set for development
if [ ! -z ${DATABASE_URL} ] || [ ! -z ${ES_URL+x} ];
then
    echo ".env file contains production variables DATABASE_URL or ES_URL, but FLASK_ENV set to 'development'."
    echo "Please comment out DATABASE_URL or ES_URL in the .env file."
    echo "Launch aborted!"
    exit 1
fi

# Upgrade db and run
printf "Running database updates...\n\n"
flask db upgrade

printf "Launching website...\n"
flask run
