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
(apart from setting up a :ref:`reverse proxy`). Each is treated as an independent microservice and their
network topology is defined in `docker-compose.yml`. This should be a first point of reference to gain a sense of how
the pieces of the application work together at a high-level.

.. _database:

Database
--------

.. _flaskLogic:

Flask Logic
-----------



