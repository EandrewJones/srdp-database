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

`docker-compose.yml` spins up two containers. The first is an image of a MySQL database version 5.7 and uses
two volumnes: the config settings in `db/custom.cnf` and `/var/lib/mysql` which is where the database is mounted
on the local machine so that data can persist beyond sessions (in case the container is stopped, the data will still exist
when it is spun back up). The second is a containerized version of the Flask API web app which is launched by
calling `Dockerfile` in the parent directory. This custom docker file configures the container environment
(OS flavor, pre-installed dependencies, etc.) and finishes by calling `boot.sh` which actually launches the web app.
Both containers live inside a private networks entitled 'dbnet'. This means that only they can see and communicate with
each other apart from a single port, 5000, which is mapped to port 5000 on the localhost. All requests to the API occur through this gateway.

Docker provides great `documentation <https://docs.docker.com/compose/>`_ on Docker Compose for learning how to write
(and understand) orchestration files for different services.

.. _database:

Database
--------

There are handful pieces that make the database tick. The first is the database itself which is a virtual instance running in a docker container.
As noted above, this container is linked with a volume on the local device so that data persists across launch and tear down (whenever the app is updated).
The second piece is the .env file which specifies configuration variables for the database, including the database name, the user, the password,
the root password, and the connection URI that points to the containerized database. This information is read into `config.py`, which stores all
configruation parameters for the Flask app, and then passed to Flask-SQLAlchemy on app launch to create the actual connection between the app and database.
The final piece is Flask-SQLAlchemy which is a wrapper around the SQLAlchemy a python ORM module.

There is *zero* SQL involved in creating and defining the database and tables. All of this is handled via SQLAlchemy in `app/models.py`.
Each class in the file corresponds to a table in the database and each class variable corresponds to a field in that table.
Classes may also have methods for performing CRUD actions on the table, but these are pure python functions and are completely
independent of the database itself.  All new tables or modifications to existing tables happen in `app/models.py`.


.. _flaskLogic:

Flask Logic
-----------

The remainder of the codebase consists flask app logic. The flask application follows an `"application factory" <https://flask.palletsprojects.com/en/2.1.x/patterns/appfactories/>`_ approach.
An app factory approach relies on modular design, where multiple versions of the app can be instantiated with varying configuration parameters. In addition,
the application is broken down into modular parts called "blueprints" which groups together similar logic.

The application factory design can be seen in `app/__init__.py`. Each of the flask extensions are first created and then initialized
with the app in the `create_app()` function. Thereafter, each blueprint is registered with the app, creating a unique namespace for all the routes
within that blueprint. Finally, logging is set up to write to a local log files or a mail server if one is set up (see `here <https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-x-email-support/page/4>`_`).
The appliation can easily work with a gmail account with SMTP and third-party app access enabled. This email address is set in `.env` and the functions
for sending emails are located in `app/email.py`.

Finally, we turn to the API routes and specs, the meat and potatoes of the app. The specification for the API is located in `app/api_specs.py`.
This file calls the `apispec <https://apispec.readthedocs.io/en/latest/>`_ library with `marshmallow <https://marshmallow.readthedocs.io/en/stable/>`_
and flask plugins to generate the website's `Swagger docs <https://swagger.io/docs/>`_ `page <https://srdp.ea-jones.com/api/docs/>`_ for
the api routes and database table schemas.

The `api/` directory contains a file for each of the database tables as well as a few utility files for things such authentication/authorization
and error handling. Each of these files contains routes for CRUD (create, retrieve, update, delete) actions via their respective HTTP methods
(POST, GET, PUT, DELETE). Whenever a new table is added to the database, a new file should be added with the appropriate routes/methods. A new schemas
will also need to be defined in `app/apispec.py`

You will notice there are other blueprint directories such as auth, administrator and main. These are currently unused but contain some initial logic
if a future developer wants to add a full-fledged front-end UI to the website. Administrator stores logic for an flask-admin administrator portal.
Auth contains routes for user authentication, and main serves as a catch all for all other front-end routes.
