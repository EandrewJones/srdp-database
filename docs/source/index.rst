Welcome to SRDP Database and API's Developer Documentation!
===========================================================

What is SRDP?
-------------

**Strategies of Resistance Data Project** (SRDP) is a global dataset on organizational behavior in self-determination disputes.
It is actor-focused and spans periods of relative peace and violence in self-determination conflicts. By linking tactics to specific
actors in broader campaigns for political change, we can better understand how these struggles unfold over time, and the conditions
under which organizations use conventional politics, violent tactics, nonviolent tactics, or some combination of these.

The previous SRDP comprises 1,124 organizations participating in movements for greater national self-determination around the world, from 1960 to 2005.
An update of the dataset is currently underway and will bring all data up to 2020 as well as expand the type of colletions available.

Why Do We Provide a Database API?
---------------------------------

The goal of storing the project data in a relational database and providing an application programming interface (API) on top of that database is threefold:

- Create a single source of truth for all data - previously data has been stored across various providers (dropbox, googlesheets, local devices) and updated in multiple places, leading to increased prevalance of errors and conflicting versions.
- Make it easier for project maintainers and end users to retrieve the data they need, in the desired format and scope, in a programming language of their choice.
- Provide a service layer for project developers to build additional tools on top of (e.g. web UI for labeling, data ingestion pipelines, user-facing website, etc.)

The first version of this API provides just enough functionality such as basic Create, Retrieve, Update, Delete (CRUD) actions to achieve
all three of these, but certainly is not a full-fledged API. For example, most endpoints do not accept query parameters to customize
requests.

The hope is that these documents serve as a jumping off point for future developers to further expand the service.

Check out the :doc:`directory` section for information on the project file structure.
Information on configuring, launching, administrating, and updating source code is available in the :doc:`manual` section.

How are the Database and API implemented?
-----------------------------------------

**Tech Stack**

The relational database uses an MySQL 5.7 image and is containerized. The API app is also containerized and built using Python Flask \
for routing plus `Flask-SQLAlchemy` to build the database models.  The API endpoints are fully documented in a Swagger UI according to OpenAPI
specification with the help of the `flask-apispec`. Docker Compose handles container orchestration and deployment. The database itself
is persisted to volume (data persists even after starting and stopping of the container)

.. list-table:: Tech Stack
   :widths: 25 25 50
   :header-rows: 1

   * - Purpose
     - Tool
     - Documentation
   * - Containerization
     - Docker
     - https://docs.docker.com/_
   * - Container Orchestration and Deployment
     - Docker Compose
     - https://docs.docker.com/compose/
   * - RDBMS
     - MySQL 5.7
     - https://dev.mysql.com/doc/refman/5.7/en/
   * - Web Dev
     - Flask
     - https://flask.palletsprojects.com/en/2.1.x/
   * - ORM
     - Flask-SQLAlchemy, SQLAlchemy
     - https://flask-sqlalchemy.palletsprojects.com/en/2.x/
   * - SQLAlchemy Database Migrations
     - flask-migrate
     - https://flask-migrate.readthedocs.io/en/latest/
   * - API Schema
     - flask-marshmallow
     - https://flask-marshmallow.readthedocs.io/en/latest/
   * - API Docs
     - flask-apispec
     - https://flask-apispec.readthedocs.io/en/latest/usage.html
   * - API Schema
     - flask-marshmallow
     - https://flask-marshmallow.readthedocs.io/en/latest/
   * - Server Hosting
     - Linode
     - https://www.linode.com/


To gain a better sense of web development in flask and many of the frameworks/modules used in this project, I highly recommend either read or
working through in its entirety the `Flask Mega Tutorial <https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world>`_
by Miguel Grinberg. It is highly informative. Much of this project close resembles the code in that tutorial.
In particular, chapters 1-4, 17-19, and 23 are must reads.

**What is a REST API?**

To steal language from Redhat linux's `documentation <https://www.redhat.com/en/topics/api/what-is-a-rest-api>`_:

    A REST API (also known as RESTful API) is an application programming interface (API or web API) that conforms to the
    constraints of REST architectural style and allows for interaction with RESTful web services. REST stands for
    representational state transfer and was created by computer scientist Roy Fielding.

    An API is a set of definitions and protocols for building and integrating application software. It's sometimes referred
    to as a contract between an information provider and an information user—establishing the content required from the consumer
    (the call) and the content required by the producer (the response). For example, the API design for a weather service could
    specify that the user supply a zip code and that the producer reply with a 2-part answer, the first being the high temperature,
    and the second being the low.

    In other words, if you want to interact with a computer or system to retrieve information or perform a function, an API helps
    you communicate what you want to that system so it can understand and fulfill the request.

    You can think of an API as a mediator between the users or clients and the resources or web services they want to get.
    It's also a way for an organization to share resources and information while maintaining security, control, and authentication—determining who gets access to what.

So what the hell does that mean in layman's terms? This `blog <https://idratherbewriting.com/learnapidoc/docapis_what_is_a_rest_api.html>`_ provides a nice explanation.

In this project, the API is a web service that relies on HTTP protocol to send and receive requests and data. However, an API need to necessarily be a web service.

.. note::

   This project is under active development.


Contents
--------

.. toctree::

   directory
   manual
   api