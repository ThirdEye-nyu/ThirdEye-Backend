# Copyright 2016, 2021 John J. Rofrano. All Rights Reserved.
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
Test cases for lines Models

Test cases can be run with:
    nosetests
    coverage report -m

While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_lines.py:TestlineModel

"""
import os
import logging
import unittest
from werkzeug.exceptions import NotFound
from service.models import Lines, DataValidationError, db, Status
from service import app
from tests.factories import LinesFactory
import datetime

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/testdb"
)


######################################################################
#  lineS   M O D E L   T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestlinesModel(unittest.TestCase):
    """Test Cases for line Model"""

    @classmethod
    def setUpClass(cls):
        """This runs once before the entire test suite"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        Lines.init_db(app)

    @classmethod
    def tearDownClass(cls):
        """This runs once after the entire test suite"""
        db.session.close()

    def setUp(self):
        """This runs before each test"""
        db.session.query(Lines).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_create_a_line(self):
        """It should Create a line and assert that it exists"""
        current_time = datetime.datetime.now()
        line = Lines(name="line-1", customer_id=1, created_on=current_time)
        self.assertEqual(str(line), "<Line 'line-1' id=[None]>")
        self.assertTrue(line is not None)
        self.assertEqual(line.id, None)
        self.assertEqual(line.name, "line-1")
        self.assertEqual(line.customer_id, 1)
        self.assertEqual(line.created_on, current_time)

    def test_add_a_line(self):
        """It should Create a line and add it to the database"""
        lines = Lines.all()
        self.assertEqual(lines, [])
        current_time = datetime.datetime.now()
        line = Lines(name="line-1", customer_id=1, created_on=current_time)
        self.assertTrue(line is not None)
        self.assertEqual(line.id, None)
        line.create()
        # Assert that it was assigned an id and shows up in the database
        self.assertIsNotNone(line.id)
        lines = Lines.all()
        self.assertEqual(len(lines), 1)

    def test_read_a_line(self):
        """It should Read a line"""
        line = LinesFactory()
        logging.debug(line)
        line.id = None
        line.create()
        self.assertIsNotNone(line.id)
        # Fetch it back
        found_line = Lines.find(line.id)
        self.assertEqual(found_line.id, line.id)
        self.assertEqual(found_line.name, line.name)
        self.assertEqual(found_line.customer_id, line.customer_id)
        self.assertEqual(found_line.created_on, line.created_on)

    def test_update_a_line(self):
        """It should Update a line"""
        line = LinesFactory()
        logging.debug(line)
        line.id = None
        line.create()
        logging.debug(line)
        self.assertIsNotNone(line.id)
        # Change it an save it
        line.customer_id = 2
        original_id = line.id
        line.update()
        self.assertEqual(line.id, original_id)
        self.assertEqual(line.customer_id, 2)
        # Fetch it back and make sure the id hasn't changed
        # but the data did change
        lines = Lines.all()
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0].id, original_id)
        self.assertEqual(lines[0].customer_id, 2)

    def test_update_no_id(self):
        """It should not Update a line with no id"""
        line = LinesFactory()
        logging.debug(line)
        line.id = None
        self.assertRaises(DataValidationError, line.update)

    def test_delete_a_line(self):
        """It should Delete a line"""
        line = LinesFactory()
        line.create()
        self.assertEqual(len(Lines.all()), 1)
        # delete the line and make sure it isn't in the database
        line.delete()
        self.assertEqual(len(Lines.all()), 0)

    def test_list_all_lines(self):
        """It should List all lines in the database"""
        lines = Lines.all()
        self.assertEqual(lines, [])
        # Create 5 lines
        for _ in range(5):
            line = LinesFactory()
            line.create()
        # See if we get back 5 lines
        lines = Lines.all()
        self.assertEqual(len(lines), 5)

    def test_serialize_a_line(self):
        """It should serialize a line"""
        line = LinesFactory()
        data = line.serialize()
        self.assertNotEqual(data, None)
        self.assertIn("id", data)
        self.assertEqual(data["id"], line.id)
        self.assertIn("name", data)
        self.assertEqual(data["name"], line.name)
        self.assertIn("customer_id", data)
        self.assertEqual(data["customer_id"], line.customer_id)
        self.assertIn("created_on", data)
        self.assertEqual(data["created_on"], line.created_on)

    def test_deserialize_a_line(self):
        """It should de-serialize a line"""
        data = LinesFactory().serialize()
        line = Lines()
        line.deserialize(data)
        self.assertNotEqual(line, None)
        self.assertEqual(line.id, None)
        self.assertEqual(line.name, data["name"])
        self.assertEqual(line.customer_id, data["customer_id"])

    def test_deserialize_missing_data(self):
        """It should not deserialize a line with missing data"""
        data = {"id": 1, "name": "Kitty"}
        line = Lines()
        self.assertRaises(DataValidationError, line.deserialize, data)

    def test_deserialize_bad_data(self):
        """It should not deserialize bad data"""
        data = "this is not a dictionary"
        line = Lines()
        self.assertRaises(DataValidationError, line.deserialize, data)

    def test_deserialize_bad_customer_id(self):
        """It should not deserialize a bad customer_id attribute"""
        test_line = LinesFactory()
        data = test_line.serialize()
        data["customer_id"] = "1"
        line = Lines()
        self.assertRaises(DataValidationError, line.deserialize, data)

    def test_find_line(self):
        """It should Find a line by ID"""
        lines = LinesFactory.create_batch(5)
        for line in lines:
            line.create()
        logging.debug(lines)
        # make sure they got saved
        self.assertEqual(len(Lines.all()), 5)
        # find the 2nd line in the list
        line = Lines.find(lines[1].id)
        self.assertIsNot(line, None)
        self.assertEqual(line.id, lines[1].id)
        self.assertEqual(line.name, lines[1].name)
        self.assertEqual(line.customer_id, lines[1].customer_id)
        self.assertEqual(line.created_on, lines[1].created_on)

    def test_find_by_customer_id(self):
        """It should Find lines by Category"""
        lines = LinesFactory.create_batch(10)
        for line in lines:
            line.create()
        customer_id = lines[0].customer_id
        count = len(
            [line for line in lines if line.customer_id == customer_id]
        )
        found = Lines.find_by_customer_id(customer_id)
        self.assertEqual(found.count(), count)
        for line in found:
            self.assertEqual(line.customer_id, customer_id)

    def test_find_by_name(self):
        """It should Find a line by Name"""
        lines = LinesFactory.create_batch(5)
        for line in lines:
            line.create()
        name = lines[0].name
        found = Lines.find_by_name(name)
        self.assertEqual(found.count(), 1)
        self.assertEqual(found[0].customer_id, lines[0].customer_id)
        self.assertEqual(found[0].created_on, lines[0].created_on)

    def test_find_or_404_found(self):
        """It should Find or return 404 not found"""
        lines = LinesFactory.create_batch(3)
        for line in lines:
            line.create()

        line = Lines.find_or_404(lines[1].id)
        self.assertIsNot(line, None)
        self.assertEqual(line.id, lines[1].id)
        self.assertEqual(line.name, lines[1].name)
        self.assertEqual(line.customer_id, lines[1].customer_id)
        self.assertEqual(line.created_on, lines[1].created_on)

    def test_find_or_404_not_found(self):
        """It should return 404 not found"""
        self.assertRaises(NotFound, Lines.find_or_404, 0)
