# Copyright 2016, 2022 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Lines API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
  codecov --token=$CODECOV_TOKEN

  While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_service.py:TestLinesService
"""

import os
import logging
from unittest import TestCase

# from unittest.mock import MagicMock, patch
from service import app
from service.common import status
from service.models import db, Lines, Status
from tests.factories import LinesFactory

# Disable all but critical errors during normal test run
# uncomment for debugging failing tests
# logging.disable(logging.CRITICAL)

# DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite:///../db/test.db')
DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/testdb"
)
BASE_URL = "/lines"


######################################################################
#  T E S T   Lines   S E R V I C E
######################################################################
class TestLinesService(TestCase):
    """Wishlist Server Tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        # Set up the test database
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        Lines.init_db(app)

    @classmethod
    def tearDownClass(cls):
        """Run once after all tests"""
        db.session.close()

    def setUp(self):
        """Runs before each test"""
        self.client = app.test_client()
        db.session.query(Lines).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        db.session.remove()

    def _create_lines(self, count):
        """Factory method to create lines in bulk"""
        lines = []
        for _ in range(count):
            test_lines = LinesFactory()
            response = self.client.post(BASE_URL, json=test_lines.serialize())
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
                "Could not create test line",
            )
            new_line = response.get_json()
            test_lines.id = new_line["id"]
            lines.append(new_line)
        return lines

    def _create_lines_by_customer(self, count, customer_id):
        """Factory method to create lines in bulk"""
        lines = []
        for _ in range(count):
            test_lines = LinesFactory()
            json_req = test_lines.serialize()
            json_req["customer_id"] = customer_id
            response = self.client.post(BASE_URL, json=json_req)
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
                "Could not create test line",
            )
            new_line = response.get_json()
            test_lines.id = new_line["id"]
            lines.append(new_line)
        return lines

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_index(self):
        """It should call the Home Page"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data["name"], "lines Demo REST API Service")

    def test_health(self):
        """It should be healthy"""
        response = self.client.get("/healthcheck")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data["status"], 200)
        self.assertEqual(data["message"], "Healthy")

    def test_create_line(self):
        """It should Create a new line"""
        test_line = LinesFactory()
        logging.debug("Test Wishlist: %s", test_line.serialize())
        response = self.client.post(BASE_URL, json=test_line.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        new_line = response.get_json()
        self.assertEqual(new_line["name"], test_line.name)
        self.assertEqual(new_line["customer_id"], test_line.customer_id)

        # Check that the location header was correct
        response = self.client.get(location)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        new_line = response.get_json()
        self.assertEqual(new_line["name"], test_line.name)
        self.assertEqual(new_line["customer_id"], test_line.customer_id)

    def test_create_lines_no_data(self):
        "should not create a line"
        response = self.client.post(BASE_URL, json={})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_lines_no_content_type(self):
        "should not create a line"
        response = self.client.post(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_create_lines_bad_content_type(self):
        "should not create a line"
        response = self.client.post(
            BASE_URL, headers={"Content-Type": "application/octet-stream"}
        )
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_delete_line(self):
        """It should Delete a Wishlist"""
        test_line = self._create_lines(1)[0]
        response = self.client.delete(f"{BASE_URL}/{test_line['id']}")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(len(response.data), 0)
        # make sure they are deleted
        response = self.client.get(f"{BASE_URL}/{test_line['id']}")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_rename_line(self):
        """It should rename the line."""
        test_line = self._create_lines(1)[0]
        response = self.client.put(
            f"{BASE_URL}/{test_line['id']}", json={"name": "Test Rename"}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        renamed_line = response.get_json()
        self.assertEqual(renamed_line["name"], "Test Rename")

        response = self.client.get(f"{BASE_URL}/{test_line['id']}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        line = response.get_json()
        self.assertEqual(line["name"], "Test Rename")

    def test_list_all_lines(self):
        "It should display all the lines when present."
        
        response = self.client.get(f"{BASE_URL}")
        self.assertEqual(response.get_json()["message"], "No lines found")

        test_lines = self._create_lines(5)
        ids = [w["id"] for w in test_lines]
        response = self.client.get(f"{BASE_URL}")

        resp_lines = response.get_json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp_lines["lines"]), len(test_lines))
        for r in resp_lines["lines"]:
            self.assertIn(r["id"], ids)

    def test_list_line(self):
        "It should display the lines for a particular customer"
        customer_id = 5678
        test_lines = self._create_lines_by_customer(5, customer_id)

        ids = [w["id"] for w in test_lines]
        response = self.client.get(
            f"{BASE_URL}", query_string="customer_id=" + str(customer_id)
        )

        resp_lines = response.get_json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp_lines["lines"]), len(test_lines))
        for r in resp_lines["lines"]:
            self.assertEqual(r["customer_id"], customer_id)
            self.assertIn(r["id"], ids)
        cid = 789
        response = self.client.get(
            f"{BASE_URL}", query_string="customer_id=" + str(cid)
        )
        self.assertEqual(
            response.get_json()["message"],
            "No lines found for the customer id - " + str(cid),
        )
