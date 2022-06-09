"""OpenAPI v3 Specification"""

from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from apispec_webframeworks.flask import FlaskPlugin
from marshmallow import Schema, fields, pre_dump
from flask import url_for
from config import Config
from app import ma
from app.models import (
    User,
    ViolentTactics,
    NonviolentTactics,
    Organizations,
    Organizations,
)


# Create an APISpec
spec = APISpec(
    title=Config.COVER_NAME,
    version="0.1.0",
    openapi_version="3.0.3",
    plugins=[FlaskPlugin(), MarshmallowPlugin()],
    info=dict(
        description=f"An API for the Strategies of Resistance Data Project.\
            \n\nWhen passing new data to the model, the order of creation must be `Groups` >\
            `Organizations` > (`NonviolentTactics` | `ViolentTactics` ), where the pipe '|' \
            indicates order indifference at the step. Users must be token-authorized to \
            POST, PUT, or DELETE content. All paths are token protected and only an Admin may \
            interact with endpoints for the user collection.\
            \n\nAny model may be retrieved by any user so long as they are token-authorized.\
            User tokens change every 30 minutes and can be retrieved using various utilities. For example:\
            \n\ncommand-line with Curl:\
            \n\n\t\t$ curl --user <username>:<password> -X POST https://{Config.HOST_NAME}/api/tokens\
            \n\ncommand-line with HTTPie:\
            \n\n\t\t$ http -a <username>:<password> POST https://{Config.HOST_NAME}/api/tokens.\
            \n\nin Python with requests:\
            \n\n\t\t>>> import requests\
            \n\n\t\t>>> r = requests.post('https://{Config.HOST_NAME}/api/tokens', auth=('<user>', '<pass>'))\
            \n\n\t\t>>> token = r.json()['token']\
            \n\nin R with httr:\
            \n\n\t\t> library('httr')\
            \n\n\t\t> response <- POST('https://{Config.HOST_NAME}/api/tokens', authenticate('<user>'', '<passwd>'))\
            \n\n\t\t> token = content(response)$token\
            \n\nYou may also authorize below using the authorization endpoint, fetch the returned token\
            and pass that to the authorize form BearerAuth to begin a session on this page. From there,\
            you may perform example requests to generate the endpoint for those resources, see results, \
            and examine model input and output schemas."
    ),
)

# security schema
http_basic_scheme = {"type": "http", "scheme": "basic"}
http_bearer_scheme = {"type": "http", "scheme": "bearer"}
spec.components.security_scheme("BasicAuth", http_basic_scheme)
spec.components.security_scheme("BearerAuth", http_bearer_scheme)

# Null handler mix in
class BasicSchema(Schema):
    SKIP_VALUES = set([None])

    @pre_dump
    def remove_skip_values(self, data, **kwargs):
        return {key: value for key, value in data.items() if value is not None}


# Define Schemas
class TokenSchema(Schema):
    token = fields.Str(
        description="User's authorization bearer token for further requests."
    )
    expiration = fields.Int(
        description="Time when token expires in Unix Epoch time (ms)."
    )


class ViolentTacticsSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        type_ = "results"
        model = ViolentTactics
        include_fk = True
        fields = (
            "id",
            "facId",
            "year",
            "againstState",
            "againstStateFatal",
            "againstOrg",
            "againstOrgFatal",
            "againstIngroup",
            "againstIngroupFatal",
            "againstOutgroup",
            "againstOutgroupFatal",
            "created_at",
            "modified_at",
            "_links",
        )

    # Links
    _links = ma.Hyperlinks(
        {
            "self": ma.URLFor("api.get_violent_tactics", values=dict(id="<id>")),
            "collection": ma.URLFor("api.get_violent_tactics"),
            "organizaation": ma.URLFor(
                "api.get_organization", values=dict(facId="<facId>")
            ),
        }
    )


class ViolentTacticsInputSchema(Schema):
    # Required fields
    facId = fields.Int(description="Organizations faction ID (facId)", required=True)
    year = fields.Int(description="Violent activity year", required=True)

    # Optional fields
    againstState = fields.Int(description="Violent action taken against the state.")
    againstStateFatal = fields.Int(
        description="Fatally violent action taken against the state."
    )
    againstOrg = fields.Int(
        description="Violent action taken against another organization."
    )
    againstOrgViolent = fields.Int(
        description="Fatally violent action taken against another organization."
    )
    againstIngroup = fields.Int(
        description="Violent action taken against the ethnolinguistic in-group."
    )
    againstIngroupFatal = fields.Int(
        description="Fatally violent action taken against the ethnolinguistic in-group."
    )
    againstOutgroup = fields.Int(
        description="Violent action taken against an ethnolinguistic out-group."
    )
    againstOutgroupFatal = fields.Int(
        description="Fatally violent action taken against an ethnolinguistic out-group."
    )

    created_at = fields.DateTime(description="Time of row creation.")
    modified_at = fields.DateTime(description="Time of most recent modification.")


class NonviolentTacticsSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        type_ = "results"
        model = NonviolentTactics
        include_fk = True
        fields = (
            "id",
            "facId",
            "year",
            "economicNoncooperation",
            "protestDemonstration",
            "nonviolentIntervention",
            "socialNoncooperation",
            "institutionalAction",
            "politicalNoncooperation",
            "created_at",
            "modified_at",
            "_links",
        )

    _links = ma.Hyperlinks(
        {
            "self": ma.URLFor("api.get_nonviolent_tactic", values=dict(id="<id>")),
            "collection": ma.URLFor("api.get_nonviolent_tactics"),
            "organization": ma.URLFor(
                "api.get_organization", values=dict(facId="<facId>")
            ),
        }
    )


class NonviolentTacticsInputSchema(Schema):
    # Required fields
    facId = fields.Int(description="Organizations faction ID (facId)", required=True)
    year = fields.Int(description="Violent activity year", required=True)

    # Optional fields
    economicNoncooperation = fields.Int(description="Economic non-cooperation.")
    protestDemonstration = fields.Int(description="Protest or demonstration.")
    nonviolentIntervention = fields.Int(description="Nonviolent Intervention.")
    socialNoncooperation = fields.Int(description="Social non-cooperation.")
    institutionalAction = fields.Int(description="Institutional action.")
    politicalNoncooperation = fields.Int(description="Political non-cooperation.")

    created_at = fields.DateTime(description="Time of row creation.")
    modified_at = fields.DateTime(description="Time of most recent modification.")


class OrganizationSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        type_ = "results"
        model = Organizations
        includes_fk = True
        fields = (
            "facId",
            "kgcId",
            "facName",
            "startYear",
            "endYear",
            "created_at",
            "modified_at",
            "_links",
        )

    # Links
    _links = ma.Hyperlinks(
        {
            "self": ma.URLFor("api.get_organization", values=dict(facId="<facId>")),
            "collection": ma.URLFor("api.get_organizations"),
            "group": ma.URLFor("api.get_group", values=dict(kgcId="<kgcId>")),
            "violentTactics": ma.URLFor(
                "api.get_org_violent_tactics", values=dict(facId="<facId>")
            ),
            "nonviolentTactics": ma.URLFor(
                "api.get_org_nonviolent_tactics", values=dict(facId="<facId>")
            ),
        }
    )


class OrganizationInputSchema(Schema):
    # Required fields
    facId = fields.Int(description="Organizations faction ID (facId)", required=True)
    kgcId = fields.Int(
        description="Separatist ethnolinguistic group ID (kgcId).", required=True
    )
    facName = fields.String(description="Faction/organization name", required=True)
    startYear = fields.Int(
        description="First year of organization's documented demands.", required=False
    )
    endYear = fields.Int(
        description="Final year of organization's documented demands.", required=False
    )

    # Optional fields
    created_at = fields.DateTime(description="Time of row creation.")
    modified_at = fields.DateTime(description="Time of most recent modification.")


class GroupSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        type_ = "results"
        model = Organizations
        includes_fk = True
        fields = (
            "kgcId",
            "groupName",
            "country",
            "startYear",
            "endYear",
            "created_at",
            "modified_at",
            "_links",
        )

    # Links
    _links = ma.Hyperlinks(
        {
            "self": ma.URLFor("api.get_group", values=dict(kgcId="<kgcId>")),
            "collection": ma.URLFor("api.get_groups"),
            "organizations": ma.URLFor(
                "api.get_group_organizations", values=dict(kgcId="<kgcId>")
            ),
        }
    )


class GroupInputSchema(Schema):
    # Required fields
    kgcId = fields.Int(
        description="Separatist ethnolinguistic group ID (kgcId).", required=True
    )
    groupName = fields.String(description="Ethnolinguistic group name.", required=True)
    country = fields.String(
        description="Country where ethnolinguistic group resides.", required=True
    )
    startYear = fields.Int(
        description="First year that an organization from the ethnolinguistic group made claims for greater autonomy.",
        required=False,
    )
    endYear = fields.Int(
        description="Final year that an organization from the ethnolinguistic group made claims for greater autonomy.",
        required=False,
    )

    # Optional fields
    created_at = fields.DateTime(description="Time of row creation.")
    modified_at = fields.DateTime(description="Time of most recent modification.")


class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        type_ = "results"
        model = User
        include_fk = True
        fields = (
            "username",
            "name",
            "about_me",
            "email",
            "id",
            "is_admin",
            "created_at",
            "modified_at",
            "_links",
        )

    # Links
    _links = ma.Hyperlinks(
        {
            "self": ma.URLFor("api.get_user", values=dict(id="<id>")),
            "collection": ma.URLFor("api.get_users"),
        }
    )


class UserInputSchema(Schema):
    # required fields
    username = fields.String(description="User's profile name.", required=True)
    email = fields.String(description="User's email.", required=True)
    password = fields.String(description="User's password.", required=True)
    name = fields.String(description="User's name.", required=True)


# register schemas with spec
names = [
    "NonviolentTactics",
    "NonviolentTacticsInput",
    "ViolentTactics",
    "ViolentTacticsInput",
    "Groups",
    "GroupsInput",
    "Organizations",
    "OrganizationsInput",
    "User",
    "UserInput",
]
schemas = [
    NonviolentTacticsSchema,
    NonviolentTacticsInputSchema,
    ViolentTacticsSchema,
    ViolentTacticsInputSchema,
    GroupSchema,
    GroupInputSchema,
    OrganizationSchema,
    OrganizationInputSchema,
    UserSchema,
    UserInputSchema,
]
for name, schema in zip(names, schemas):
    spec.components.schema(name, schema=schema)


# add swagger tags for endpoint annotation
tags = [
    {"name": name, "description": f"routes for {name} model I/O"}
    for name in names
    if not name.endswith("Input")
]
for tag in tags:
    print(f"Adding tag: {tag['name']}")
    spec.tag(tag)
