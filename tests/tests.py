#!/usr/bin/env python
from cgi import test
from datetime import datetime, timedelta
from email import header
import unittest
import os
import json
from base64 import b64encode
from wsgiref import headers
from app import create_app, db
from app.models import User, ViolentTactics, NonviolentTactics, Groups, Organizations
from config import Config
from config import basedir

# ================ #
# Helper constants #
# ================= #
testUser = {
    "username": "testUser",
    "email": "test@gmail.com",
    "name": "test",
    "password": "weakTestingPassword",
}

orgData = {
    "facId": 123456,
    "kgcId": 123456,
    "facName": "testFac",
    "startYear": 1999,
    "endYear": 2000,
}

groupData = {
    "kgcId": 123456,
    "groupName": "testName",
    "country": "testCountry",
    "startYear": 1999,
    "endYear": 2000,
}

vtData = {
    "facId": 123456,
    "year": 1999,
    "againstState": 0,
    "againstStateFatal": 0,
    "againstOrg": 0,
    "againstOrgFatal": 0,
    "againstIngroup": 0,
    "againstIngroupFatal": 0,
    "againstOutgroup": 0,
    "againstOutgroupFatal": 0,
}

nvtData = {
    "facId": 123456,
    "year": 1999,
    "economicNoncooperation": 0,
    "protestDemonstration": 0,
    "nonviolentIntervention": 0,
    "socialNoncooperation": 0,
    "institutionalAction": 0,
    "politicalNoncooperation": 0,
}


# ================ #
# Helper functions #
# ================ #
def fetch_auth_token(testInstance):
    # Get admin user
    uname = Config.ADMIN_USERNAME
    pword = Config.ADMIN_PASSWORD
    usrPass = f"{uname}:{pword}"
    b64val = b64encode(usrPass.encode()).decode()

    # When
    return testInstance.client.post(
        "api/tokens", headers={"Authorization": f"Basic {b64val}"}
    )


def create_token_header(token):
    return {"Authorization": f"Bearer {token}"}


def prep_call(testInstance, data=None):
    token = fetch_auth_token(testInstance=testInstance).json["token"]
    header = create_token_header(token=token)
    payload = None
    if data:
        header["Content-type"] = "application/json"
        payload = json.dumps(data)

    return header, payload


# ===== #
# Tests #
# ===== #
test_db_path = os.path.join(basedir, "test.db")


class TestConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + test_db_path
    ELASTICSEARCH_URL = None
    ADMIN_EMAIL = "testadmin@gmail.com"


class UserModelCase(unittest.TestCase):
    # Context dependent tests
    def setUp(self):
        # Setup app and context
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()

        # Create request and cli clients
        self.client = self.app.test_client()
        self.runner = self.app.test_cli_runner()

        # Create all models
        db.create_all()

        # Create admin user
        u = User(username=Config.ADMIN_USERNAME, email=Config.ADMIN_EMAIL, name="admin")
        u.set_password(password=Config.ADMIN_PASSWORD)
        db.session.add(u)
        db.session.commit()

    # DB Model method tests
    def test_password_hashing(self):
        u = User(username="susan")
        u.set_password("cat")
        self.assertFalse(u.check_password("dog"))
        self.assertTrue(u.check_password("cat"))

    def test_admin_perms(self):
        u = User(username="admin", email=TestConfig.ADMIN_EMAIL)
        self.assertTrue(u.is_admin)

    def test_password_reset(self):
        # Given
        u = User(username="susan")
        u.set_password("cat")

        # When
        token = u.get_reset_password_token()
        retrieved_user = u.verify_reset_password_token(token=token)

        # Then
        self.assertIsNotNone(u, retrieved_user)

    def test_violenttactics_from_dict(self):
        # Empty violent tactic
        vt = ViolentTactics()
        vt.from_dict(data=vtData)
        self.assertEqual(vt.facId, 123456)
        self.assertEqual(vt.year, 1999)
        for field in [
            "againstState",
            "againstStateFatal",
            "againstOrg",
            "againstOrgFatal",
            "againstIngroup",
            "againstIngroupFatal",
            "againstOutgroup",
            "againstOutgroupFatal",
        ]:
            self.assertEqual(getattr(vt, field), 0)

    def test_nonviolent_tactics_from_dict(self):
        nvt = NonviolentTactics()
        nvt.from_dict(data=nvtData)
        self.assertEqual(nvt.facId, 123456)
        self.assertEqual(nvt.year, 1999)
        for field in [
            "economicNoncooperation",
            "protestDemonstration",
            "nonviolentIntervention",
            "socialNoncooperation",
            "institutionalAction",
            "politicalNoncooperation",
        ]:
            self.assertEqual(getattr(nvt, field), 0)

    def test_groups_from_dict(self):
        group = Groups()
        group.from_dict(data=groupData)
        self.assertEqual(group.kgcId, 123456)
        self.assertEqual(group.groupName, "testName")
        self.assertEqual(group.country, "testCountry")
        self.assertEqual(group.startYear, 1999)
        self.assertEqual(group.endYear, 2000)

    def test_orgs_from_dict(self):
        org = Organizations()
        org.from_dict(data=orgData)
        self.assertEqual(org.kgcId, 123456)
        self.assertEqual(org.facId, 123456)
        self.assertEqual(org.facName, "testFac")
        self.assertEqual(org.startYear, 1999)
        self.assertEqual(org.endYear, 2000)

    # API route tests
    def test_token_GET(self):
        # When
        response = fetch_auth_token(testInstance=self)

        # Then
        self.assertEqual(200, response.status_code, f"{response.data}")
        self.assertIsNotNone(response.json["token"])

    def test_user_POST(self):
        # Given
        header, payload = prep_call(self, testUser)

        # When
        response = self.client.post("api/users", headers=header, data=payload)

        # Then
        self.assertEqual(201, response.status_code, f"{response.data}")

    def test_user_GET(self):
        # Given
        header, _ = prep_call(self)

        # When
        response = self.client.get("api/users", headers=header)

        # Then
        self.assertEqual(200, response.status_code, f"{response.data}")

    def test_user_PUT(self):
        # TODO: Figure out why not working; works fine in terminal
        # Given
        header, payload = prep_call(self, {"name": "testUserChange"})

        # Then
        response = self.client.put(f"api/users/2", headers=header, data=payload)

        # Then
        self.assertEqual(200, response.status_code, f"{response.data}")
        self.assertEqual("testUserChange", response.json["name"])

    def test_user_DELETE(self):
        # TODO: Figure out why not working; works fine in terminal
        # Given
        header, _ = prep_call(self)

        # When
        response = self.client.delete("api/users/2", headers=header)

        # Then
        self.assertEqual(204, response.status_code)

    def test_group_POST(self):
        # Given
        header, payload = prep_call(self, groupData)

        # When
        response = self.client.post("api/groups", headers=header, data=payload)

        # Then
        self.assertEqual(201, response.status_code, f"{response.data}")

    def test_groups_POST(self):
        # Given
        groupsData = [
            {
                "kgcId": 1,
                "groupName": "GroupOne",
                "country": "testCountry",
                "startYear": 1999,
                "endYear": 2000,
            },
            {
                "kgcId": 2,
                "groupName": "GroupTwo",
                "country": "testCountry",
                "startYear": 1999,
                "endYear": 2000,
            },
            {
                "kgcId": 3,
                "groupName": "GroupThree",
                "country": "testCountry",
                "startYear": 1999,
                "endYear": 2000,
            },
        ]
        header, payload = prep_call(self, groupsData)

        # When
        response = self.client.post("api/groups", headers=header, data=payload)

        # Then
        self.assertEqual(201, response.status_code, f"{response.data}")

    def test_groups_PUT(self):
        # Given
        header, payload = prep_call(self, {"country": "newCountry"})

        # When
        response = self.client.put("api/groups/1", headers=header, data=payload)

        # Then
        self.assertEqual(200, response.status_code, f"{response.data}")

    def test_groups_DELETE(self):
        # Given
        header, _ = prep_call(self)

        # When
        response = self.client.delete("api/groups/1", headers=header)

        # Then
        self.assertEqual(204, response.status_code, f"{response.data}")

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        os.remove(test_db_path)


if __name__ == "__main__":
    unittest.main(verbosity=2)
