#! /bin/bash

##
#
# Test api
#   A script for quick testing of different API functions
#
##
shopt -s extglob

# Load and check environment variables
eval "$(shdotenv -e ../.env)"

# Check that it's up
# CHECK_URL='http://localhost:5000'
# while IFS=':' read key value; do
#     # Time whitespace in "value"
#     value=${value##+([[:space:]])}; value=${value%%+([[:space:]])}

#     case "$key" in
#         Server) SERVER="$value"
#                 ;;
#         Content-Type) CT="$value"
#                 ;;
#         HTTP*) read PROTO STATUS MSG <<< "$key{$value:+:$value}"
#                 ;;
#     esac
# done < <(curl -sI $CHECK_URL)

# if [ $STATUS -eq 302 ];
# then
#     printf "Website running; API live."
#     FLASK_PID=$(pgrep -f "flask run")
# else
#     printf "Wesbite not found...\nExiting"
#     exit 1

# Set base url
BASE_URL='http://localhost:5000/api'

# Get flask instance pid
FLASK_PID=$(pgrep -f "flask run")

# ================================== #
# Create admin user and authenticate #
# ================================== #

# Fetch first admin email
ADMIN_EMAIL="$(echo $ADMIN_EMAILS | jq -r '.[0]')"

# Create a new users
create_user () {
    http POST $BASE_URL/users \
    username="$1" \
    name="$2"\
    email="$3" \
    password="$4"
}

admin=(admin Evan\ Jones $ADMIN_EMAIL $ADMIN_PASSWORD)

create_user "${admin[@]}"

# Get tokens
tok="$(http -a $ADMIN_USERNAME:$ADMIN_PASSWORD POST $BASE_URL/tokens | jq -r '.token')"

# ==================== #
# Testing Users Routes #
# ==================== #

# Create test user
test=(test Test test@gmail.com aa)

create_user "${test[@]}"

# Get users
http GET $BASE_URL/users \
"Authorization: Bearer $tok"

# Get user
http GET $BASE_URL/users/2 \
"Authorization: Bearer $tok"

# Update user
http PUT $BASE_URL/users/2 \
name="newName" \
"Authorization: Bearer $tok"

# Delete user
http DELETE $BASE_URL/users/2 \
"Authorization: Bearer $tok"

# ==================== #
# Testing group routes #
# ==================== #

# Create single group
http POST $BASE_URL/groups \
kgcId=101 \
groupName="Group101" \
country="Country101" \
startYear=1999 \
endYear=2000 \
"Authorization: Bearer $tok"

# Update single group
http PUT $BASE_URL/groups/101 \
country="newCountry" \
"Authorization: Bearer $tok"

# Create multiple groups
http POST $BASE_URL/groups \
"Authorization: Bearer $tok" \
< test_groups.json

# Get group
http GET $BASE_URL/groups/101 \
"Authorization: Bearer $tok"

# Get groups
http GET $BASE_URL/groups \
"Authorization: Bearer $tok"

# Delete group
http DELETE $BASE_URL/groups/101 \
"Authorization: Bearer $tok"

# =========================== #
# Testing organization routes #
# =========================== #

# Create single org
http POST $BASE_URL/organizations \
facId=1003 \
kgcId=1 \
facName="TestOrganizationA" \
startYear=1999 \
endYear=2000 \
"Authorization: Bearer $tok"

# update single group
http PUT $BASE_URL/organizations/1003 \
facName="TestOrganizationChanged" \
"Authorization: Bearer $tok"

# create multiple orgs
http POST $BASE_URL/organizations \
"Authorization: Bearer $tok" \
< test_orgs.json

# Get org
http GET $BASE_URL/organizations/1003 \
"Authorization: Bearer $tok"

# Get orgs
http GET $BASE_URL/organizations \
"Authorization: Bearer $tok"

# Delete org
http DELETE $BASE_URL/organizations/1003 \
"Authorization: Bearer $tok"

# Get organization group
http GET $BASE_URL/organizations/1001/group \
"Authorization: Bearer $tok"

# Get group organizations
http GET $BASE_URL/groups/1/organizations \
"Authorization: Bearer $tok"

# ================================== #
# Testing non-violent actions routes #
# ================================== #

# Create non-violent action
http POST $BASE_URL/nonviolent_tactics \
facId=1001 \
year=1999 \
economicNoncooperation=1 \
protestDemonstration=1 \
nonviolentIntervention=1 \
socialNoncooperation=0 \
insititutionalAction=0 \
politicalNoncooperation=0 \
"Authorization: Bearer $tok"

# Update single non-violent tactic
http PUT $BASE_URL/nonviolent_tactics/1 \
economicNoncooperation=0 \
"Authorization: Bearer $tok"

# Create multiple non-violent actions
http POST $BASE_URL/nonviolent_tactics \
"Authorization: Bearer $tok" \
< test_nv_tactics.json

# Get nonviolent tactic
http GET $BASE_URL/nonviolent_tactics/1 \
"Authorization: Bearer $tok"

# Get nonviolent tactics
http GET $BASE_URL/nonviolent_tactics \
"Authorization: Bearer $tok"

# Delete nonviolent tactic
http DELETE $BASE_URL/nonviolent_tactics/1 \
"Authorization: Bearer $tok"

# Get organization non-violent tactics
http GET $BASE_URL/organizations/1001/nonviolent_tactics \
"Authorization: Bearer $tok"

# ================================== #
# Testing violent actions routes #
# ================================== #

# Create violent action
http POST $BASE_URL/violent_tactics \
facId=1001 \
year=1999 \
economicNoncooperation=1 \
protestDemonstration=1 \
nonviolentIntervention=1 \
socialNoncooperation=0 \
insititutionalAction=0 \
politicalNoncooperation=0 \
"Authorization: Bearer $tok"

# Update single violent tactic
http PUT $BASE_URL/violent_tactics/1 \
economicNoncooperation=0 \
"Authorization: Bearer $tok"

# Create multiple violent actions
http POST $BASE_URL/violent_tactics \
"Authorization: Bearer $tok" \
< test_nv_tactics.json

# Get violent tactic
http GET $BASE_URL/violent_tactics/1 \
"Authorization: Bearer $tok"

# Get violent tactics
http GET $BASE_URL/violent_tactics \
"Authorization: Bearer $tok"

# Delete violent tactic
http DELETE $BASE_URL/violent_tactics/1 \
"Authorization: Bearer $tok"

# Get organization violent tactics
http GET $BASE_URL/organizations/1001/violent_tactics \
"Authorization: Bearer $tok"


# ========= #
# Tear down #
# ========= #

# Kill test instance
kill -9 $FLASK_PID

# Remove files and folders
rm -rf migrations/
rm -rf logs/
rm ../srdp.db

