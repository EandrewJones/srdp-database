Codebase Overview
==================

.. _codebase:

Here you will find a high-level overview of the codebase, the directory structure, and each of the constituent pieces here.
Even if you do not understand everything at first, I encourage you to keep reading. At minimum you will gain a sense of what
each part of the codebase is functionally responsible for and how they pieces fit together. This is the essential for proper
debugging.

.. _directoryStructure:

Directory Structure
-------------------

The project has the directory structure shown below.

| srdp-database
| ├── app
|     ├── administrator
|     ├── api
|     ├── auth
|     ├── errors
|     ├── main
|     └── template_filters
|     ├── __init__.py
|     ├── api_spec.py
|     ├── email.py
|     └── models.py
| ├── db
| ├── deployment
| ├── docs
|     └── source
| ├── examples
|     └── api
| ├── migrations
|     └── versions
| ├── tests
| └── venv
|     ├── bin
|     ├── include
|     ├── lib
|     └── lib64 -> lib
| ├── .env.example
| ├── babel.cfg
| ├── boot.sh
| ├── config.py
| ├── docker-compose.yml
| ├── Dockerfile
| ├── launch.sh
| ├── LICENSE
| ├── Procfile
| ├── pyproject.toml
| ├── README.rst
| ├── requirements.txt
| ├── runtime.txt
| ├── srdp.py
| └── Vagrantfile

.. _docker:

Docker
------

The codebase relies on docker to containerize the web app and MySQL database. Containerizing each componenet allows for
painless deployment across a broad array of servers / cloud providers with minimal server-side configuration
(apart from setting up a reverse proxy). Each is treated as an independent microservice and their
network topology is defined in `docker-compose.yml`. This should be a first point of reference to gain a sense of how
the pieces of the application work together at a high-level.

`docker-compose.yml` spins up two containers. The first is an image of a MySQL database version 5.7 and uses two volumnes: the config settings in `db/custom.cnf` and
`/var/lib/mysql` which is where the database is mounted on the local machine so that data can persist beyond sessions (in case the container is stopped, the data will still exist
when it is spun back up). The second is a containerized version of the Flask API web app which is launched by calling `Dockerfile`in the parent directory. This custom docker file
configures the container environment (OS flavor, pre-installed dependencies, etc.) and finishes by calling `boot.sh` which actually launches the web app. Both containers live inside
a private networks entitled 'dbnet'. This means that only they can see and communicate with eachother apart from a single port, 5000, which is mapped to port 5000 on the localhost.
All requests to the API occur through this gateway.

Docker provides great `documentation <https://docs.docker.com/compose/>`_ on Docker Compose for learning how to write (and understand) orchestration files for
different services.

.. _database:

Database
--------

.. _flaskLogic:

Flask Logic
-----------



