#! /bin/bash

# Load and check environment variables
eval "$(shdotenv)"

# Set up flask env
source ../venv/bin/activate
export FLASK_APP=srdp.py
export FLASK_ENV=testing

# Initialize and migrate db
printf "Intializing database...\n\n"
flask db init

printf "Migrating database...\n\n"
flask db migrate

# Upgrade db and run
printf "Running database updates...\n\n"
flask db upgrade

printf "Launching website...\n"
flask run > test.log 2>&1
