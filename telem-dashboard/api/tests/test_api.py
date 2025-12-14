"""
Unit tests for the telemetry API and utility functions.

Tests cover:
- util.py: get_db(), init_db()
- api.py: validate_iso(), validate_status(), and all routes (GET, POST, DELETE)
"""

import unittest
import json
import os
import sqlite3
import tempfile
from unittest.mock import patch, MagicMock

import api
import util


class UtilFunctionsTestCase(unittest.TestCase):
    """Test cases for util.py functions."""

    def setUp(self):
        """Set up test database."""
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp(suffix='.db')
        util.init_db(self.temp_db_path)

    def tearDown(self):
        """Clean up test database."""
        os.close(self.temp_db_fd)
        if os.path.exists(self.temp_db_path):
            os.remove(self.temp_db_path)

    def test_init_db_creates_table(self):
        """Test that init_db creates the telemetry table."""
        db = util.get_db(self.temp_db_path)
        cursor = db.cursor()
        
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='telemetry'")
        result = cursor.fetchone()
        
        self.assertIsNotNone(result, "Telemetry table should exist")
        db.close()

    def test_init_db_table_structure(self):
        """Test that telemetry table has correct columns."""
        db = util.get_db(self.temp_db_path)
        cursor = db.cursor()
        
        # Get table schema
        cursor.execute("PRAGMA table_info(telemetry)")
        columns = cursor.fetchall()
        
        column_names = [col[1] for col in columns]
        expected_columns = ['id', 'satelliteId', 'timestamp', 'altitude', 'velocity', 'status']
        
        self.assertEqual(column_names, expected_columns)
        db.close()

    def test_init_db_idempotent(self):
        """Test that init_db can be called multiple times without error."""
        # Should not raise an error
        util.init_db(self.temp_db_path)
        util.init_db(self.temp_db_path)
        
        db = util.get_db(self.temp_db_path)
        cursor = db.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='telemetry'")
        result = cursor.fetchone()
        
        self.assertIsNotNone(result)
        db.close()

    def test_get_db_returns_connection(self):
        """Test that get_db returns a valid database connection."""
        db = util.get_db(self.temp_db_path)
        
        self.assertIsNotNone(db)
        self.assertIsInstance(db, sqlite3.Connection)
        
        db.close()

    def test_get_db_row_factory(self):
        """Test that get_db sets row_factory to sqlite3.Row."""
        # Insert sample data
        db = util.get_db(self.temp_db_path)
        cursor = db.cursor()
        cursor.execute('''
            INSERT INTO telemetry (satelliteId, timestamp, altitude, velocity, status)
            VALUES (?, ?, ?, ?, ?)
        ''', ('SAT001', '2025-12-10T10:00:00Z', 400, 7.8, 'healthy'))
        db.commit()
        db.close()
        
        # Retrieve and verify row_factory works
        db = util.get_db(self.temp_db_path)
        cursor = db.cursor()
        cursor.execute('SELECT * FROM telemetry')
        row = cursor.fetchone()
        
        # Should be able to access by column name
        self.assertEqual(row['satelliteId'], 'SAT001')
        self.assertEqual(row['altitude'], 400)
        
        db.close()

    def test_get_db_creates_file(self):
        """Test that get_db creates database file if it doesn't exist."""
        new_db_path = os.path.join(tempfile.gettempdir(), 'test_new_db.db')
        
        # Ensure it doesn't exist
        if os.path.exists(new_db_path):
            os.remove(new_db_path)
        
        db = util.get_db(new_db_path)
        self.assertTrue(os.path.exists(new_db_path))
        db.close()
        
        # Cleanup
        if os.path.exists(new_db_path):
            os.remove(new_db_path)


class ValidationFunctionsTestCase(unittest.TestCase):
    """Test cases for validation functions in api.py."""

    def test_validate_iso_valid_z_format(self):
        """Test ISO 8601 validation with Z timezone."""
        self.assertTrue(api.validate_iso('2025-12-10T10:00:00Z'))

    def test_validate_iso_valid_plus_offset(self):
        """Test ISO 8601 validation with +00:00 offset."""
        self.assertTrue(api.validate_iso('2025-12-10T10:00:00+00:00'))

    def test_validate_iso_valid_with_milliseconds(self):
        """Test ISO 8601 validation with milliseconds."""
        self.assertTrue(api.validate_iso('2025-12-10T10:00:00.000Z'))

    def test_validate_iso_valid_without_timezone(self):
        """Test ISO 8601 validation without timezone."""
        self.assertTrue(api.validate_iso('2025-12-10T10:00:00'))

    def test_validate_iso_valid_negative_offset(self):
        """Test ISO 8601 validation with negative offset."""
        self.assertTrue(api.validate_iso('2025-12-10T10:00:00-05:00'))

    def test_validate_iso_invalid_format(self):
        """Test ISO 8601 validation with invalid format."""
        self.assertFalse(api.validate_iso('12-10-2025'))

    def test_validate_iso_invalid_date_slash(self):
        """Test ISO 8601 validation with slashes."""
        self.assertFalse(api.validate_iso('2025/12/10'))

    def test_validate_iso_invalid_month(self):
        """Test ISO 8601 validation with invalid month."""
        self.assertFalse(api.validate_iso('2025-13-01T00:00:00Z'))

    def test_validate_iso_invalid_day(self):
        """Test ISO 8601 validation with invalid day."""
        self.assertFalse(api.validate_iso('2025-12-32T00:00:00Z'))

    def test_validate_iso_non_string(self):
        """Test ISO 8601 validation with non-string input."""
        self.assertFalse(api.validate_iso(12345))

    def test_validate_iso_empty_string(self):
        """Test ISO 8601 validation with empty string."""
        self.assertFalse(api.validate_iso(''))

    def test_validate_iso_none(self):
        """Test ISO 8601 validation with None."""
        self.assertFalse(api.validate_iso(None))

    def test_validate_status_healthy(self):
        """Test status validation with 'healthy'."""
        self.assertTrue(api.validate_status('healthy'))

    def test_validate_status_critical(self):
        """Test status validation with 'critical'."""
        self.assertTrue(api.validate_status('critical'))

    def test_validate_status_case_sensitive(self):
        """Test status validation is case sensitive."""
        self.assertFalse(api.validate_status('Healthy'))
        self.assertFalse(api.validate_status('CRITICAL'))

    def test_validate_status_invalid(self):
        """Test status validation with invalid value."""
        self.assertFalse(api.validate_status('warning'))

    def test_validate_status_empty(self):
        """Test status validation with empty string."""
        self.assertFalse(api.validate_status(''))

    def test_validate_status_none(self):
        """Test status validation with None."""
        self.assertFalse(api.validate_status(None))


class TelemetryAPITestCase(unittest.TestCase):
    """Test cases for the Telemetry API endpoints."""

    def setUp(self):
        """Set up test client and test database."""
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp(suffix='.db')
        util.init_db(self.temp_db_path)
        
        # Patch the DATABASE constant in api module
        self.patcher = patch.object(api, 'DATABASE', self.temp_db_path)
        self.patcher.start()
        
        self.client = api.app.test_client()
        self.app = api.app

    def tearDown(self):
        """Clean up test database and patches."""
        self.patcher.stop()
        os.close(self.temp_db_fd)
        if os.path.exists(self.temp_db_path):
            os.remove(self.temp_db_path)

    def insert_sample_data(self):
        """Insert sample telemetry data for testing."""
        db = util.get_db(self.temp_db_path)
        cursor = db.cursor()
        
        sample_data = [
            ('SAT001', '2025-12-10T10:00:00Z', 400, 7.8, 'healthy'),
            ('SAT001', '2025-12-10T11:00:00Z', 410, 7.9, 'healthy'),
            ('SAT001', '2025-12-10T12:00:00Z', 350, 6.5, 'critical'),
            ('SAT002', '2025-12-10T10:30:00Z', 500, 8.0, 'healthy'),
            ('SAT002', '2025-12-10T11:30:00Z', 510, 8.1, 'healthy'),
            ('SAT003', '2025-12-10T09:00:00Z', 300, 6.0, 'critical'),
        ]
        
        for sat_id, timestamp, altitude, velocity, status in sample_data:
            cursor.execute('''
                INSERT INTO telemetry (satelliteId, timestamp, altitude, velocity, status)
                VALUES (?, ?, ?, ?, ?)
            ''', (sat_id, timestamp, altitude, velocity, status))
        
        db.commit()
        db.close()

    # ===== GET /telemetry Tests =====

    def test_get_telemetry_empty(self):
        """Test GET /telemetry with empty database."""
        response = self.client.get('/telemetry')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertEqual(data['data'], [])
        self.assertEqual(data['pagination']['page'], 1)
        self.assertEqual(data['pagination']['total'], 0)

    def test_get_telemetry_all_data(self):
        """Test GET /telemetry returns all data."""
        self.insert_sample_data()
        response = self.client.get('/telemetry?per_page=100')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertEqual(len(data['data']), 6)
        self.assertEqual(data['pagination']['total'], 6)

    def test_get_telemetry_pagination_first_page(self):
        """Test GET /telemetry pagination first page."""
        self.insert_sample_data()
        response = self.client.get('/telemetry?page=1&per_page=2')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertEqual(len(data['data']), 2)
        self.assertEqual(data['pagination']['page'], 1)
        self.assertEqual(data['pagination']['total_pages'], 3)

    def test_get_telemetry_pagination_second_page(self):
        """Test GET /telemetry pagination second page."""
        self.insert_sample_data()
        response = self.client.get('/telemetry?page=2&per_page=2')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertEqual(len(data['data']), 2)
        self.assertEqual(data['pagination']['page'], 2)

    def test_get_telemetry_pagination_last_page(self):
        """Test GET /telemetry pagination last page."""
        self.insert_sample_data()
        response = self.client.get('/telemetry?page=3&per_page=2')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertEqual(len(data['data']), 2)
        self.assertEqual(data['pagination']['page'], 3)

    def test_get_telemetry_invalid_page_zero(self):
        """Test GET /telemetry with page=0 defaults to page 1."""
        self.insert_sample_data()
        response = self.client.get('/telemetry?page=0&per_page=20')
        data = json.loads(response.data)
        self.assertEqual(data['pagination']['page'], 1)

    def test_get_telemetry_invalid_page_negative(self):
        """Test GET /telemetry with negative page defaults to page 1."""
        self.insert_sample_data()
        response = self.client.get('/telemetry?page=-5&per_page=20')
        data = json.loads(response.data)
        self.assertEqual(data['pagination']['page'], 1)

    def test_get_telemetry_per_page_cap(self):
        """Test GET /telemetry caps per_page at 100."""
        self.insert_sample_data()
        response = self.client.get('/telemetry?per_page=500')
        data = json.loads(response.data)
        self.assertEqual(data['pagination']['per_page'], 100)

    def test_get_telemetry_per_page_minimum(self):
        """Test GET /telemetry enforces minimum per_page of 1."""
        self.insert_sample_data()
        response = self.client.get('/telemetry?per_page=0')
        data = json.loads(response.data)
        self.assertEqual(data['pagination']['per_page'], 1)

    def test_get_telemetry_filter_by_satellite_id(self):
        """Test GET /telemetry filtering by satelliteId."""
        self.insert_sample_data()
        response = self.client.get('/telemetry?satelliteId=SAT001&per_page=100')
        data = json.loads(response.data)
        
        self.assertEqual(data['pagination']['total'], 3)
        self.assertTrue(all(entry['satelliteId'] == 'SAT001' for entry in data['data']))

    def test_get_telemetry_filter_by_status(self):
        """Test GET /telemetry filtering by status."""
        self.insert_sample_data()
        response = self.client.get('/telemetry?status=critical&per_page=100')
        data = json.loads(response.data)
        
        self.assertEqual(data['pagination']['total'], 2)
        self.assertTrue(all(entry['status'] == 'critical' for entry in data['data']))

    def test_get_telemetry_filter_by_both(self):
        """Test GET /telemetry with both filters."""
        self.insert_sample_data()
        response = self.client.get('/telemetry?satelliteId=SAT001&status=healthy&per_page=100')
        data = json.loads(response.data)
        
        self.assertEqual(data['pagination']['total'], 2)
        self.assertTrue(all(entry['satelliteId'] == 'SAT001' for entry in data['data']))
        self.assertTrue(all(entry['status'] == 'healthy' for entry in data['data']))

    def test_get_telemetry_filter_no_matches(self):
        """Test GET /telemetry filter with no matches."""
        self.insert_sample_data()
        response = self.client.get('/telemetry?satelliteId=NONEXISTENT&per_page=100')
        data = json.loads(response.data)
        
        self.assertEqual(data['pagination']['total'], 0)
        self.assertEqual(len(data['data']), 0)

    def test_get_telemetry_sort_by_id_asc(self):
        """Test GET /telemetry sorting by id ascending."""
        self.insert_sample_data()
        response = self.client.get('/telemetry?sort_by=id&sort_order=asc&per_page=100')
        data = json.loads(response.data)
        
        ids = [entry['id'] for entry in data['data']]
        self.assertEqual(ids, sorted(ids))
        self.assertEqual(data['sorting']['sort_by'], 'id')
        self.assertEqual(data['sorting']['sort_order'], 'asc')

    def test_get_telemetry_sort_by_id_desc(self):
        """Test GET /telemetry sorting by id descending."""
        self.insert_sample_data()
        response = self.client.get('/telemetry?sort_by=id&sort_order=desc&per_page=100')
        data = json.loads(response.data)
        
        ids = [entry['id'] for entry in data['data']]
        self.assertEqual(ids, sorted(ids, reverse=True))
        self.assertEqual(data['sorting']['sort_order'], 'desc')

    def test_get_telemetry_sort_by_altitude(self):
        """Test GET /telemetry sorting by altitude."""
        self.insert_sample_data()
        response = self.client.get('/telemetry?sort_by=altitude&sort_order=asc&per_page=100')
        data = json.loads(response.data)
        
        altitudes = [entry['altitude'] for entry in data['data']]
        self.assertEqual(altitudes, sorted(altitudes))

    def test_get_telemetry_sort_by_velocity(self):
        """Test GET /telemetry sorting by velocity."""
        self.insert_sample_data()
        response = self.client.get('/telemetry?sort_by=velocity&sort_order=desc&per_page=100')
        data = json.loads(response.data)
        
        velocities = [entry['velocity'] for entry in data['data']]
        self.assertEqual(velocities, sorted(velocities, reverse=True))

    def test_get_telemetry_sort_by_satellite_id(self):
        """Test GET /telemetry sorting by satelliteId."""
        self.insert_sample_data()
        response = self.client.get('/telemetry?sort_by=satelliteId&sort_order=asc&per_page=100')
        data = json.loads(response.data)
        
        sat_ids = [entry['satelliteId'] for entry in data['data']]
        self.assertEqual(sat_ids, sorted(sat_ids))

    def test_get_telemetry_sort_by_timestamp(self):
        """Test GET /telemetry sorting by timestamp."""
        self.insert_sample_data()
        response = self.client.get('/telemetry?sort_by=timestamp&sort_order=asc&per_page=100')
        data = json.loads(response.data)
        
        timestamps = [entry['timestamp'] for entry in data['data']]
        self.assertEqual(timestamps, sorted(timestamps))

    def test_get_telemetry_sort_by_status(self):
        """Test GET /telemetry sorting by status."""
        self.insert_sample_data()
        response = self.client.get('/telemetry?sort_by=status&sort_order=asc&per_page=100')
        data = json.loads(response.data)
        
        statuses = [entry['status'] for entry in data['data']]
        self.assertEqual(statuses, sorted(statuses))

    def test_get_telemetry_invalid_sort_column(self):
        """Test GET /telemetry with invalid sort column defaults to id."""
        self.insert_sample_data()
        response = self.client.get('/telemetry?sort_by=invalid_column&per_page=100')
        data = json.loads(response.data)
        
        self.assertEqual(data['sorting']['sort_by'], 'id')

    def test_get_telemetry_invalid_sort_order(self):
        """Test GET /telemetry with invalid sort order defaults to asc."""
        self.insert_sample_data()
        response = self.client.get('/telemetry?sort_order=invalid&per_page=100')
        data = json.loads(response.data)
        
        self.assertEqual(data['sorting']['sort_order'], 'asc')

    def test_get_telemetry_response_structure(self):
        """Test GET /telemetry response has correct structure."""
        self.insert_sample_data()
        response = self.client.get('/telemetry')
        data = json.loads(response.data)
        
        self.assertIn('data', data)
        self.assertIn('pagination', data)
        self.assertIn('sorting', data)
        
        # Check pagination structure
        self.assertIn('page', data['pagination'])
        self.assertIn('per_page', data['pagination'])
        self.assertIn('total', data['pagination'])
        self.assertIn('total_pages', data['pagination'])
        
        # Check sorting structure
        self.assertIn('sort_by', data['sorting'])
        self.assertIn('sort_order', data['sorting'])

    # ===== GET /telemetry/<id> Tests =====

    def test_get_telemetry_by_id_success(self):
        """Test GET /telemetry/<id> with valid id."""
        self.insert_sample_data()
        response = self.client.get('/telemetry/1')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertEqual(data['id'], 1)
        self.assertEqual(data['satelliteId'], 'SAT001')

    def test_get_telemetry_by_id_different_entries(self):
        """Test GET /telemetry/<id> retrieves correct entry."""
        self.insert_sample_data()
        
        response1 = self.client.get('/telemetry/1')
        data1 = json.loads(response1.data)
        
        response2 = self.client.get('/telemetry/3')
        data2 = json.loads(response2.data)
        
        self.assertNotEqual(data1['id'], data2['id'])
        self.assertEqual(data1['satelliteId'], data2['satelliteId'])

    def test_get_telemetry_by_id_not_found(self):
        """Test GET /telemetry/<id> with non-existent id."""
        response = self.client.get('/telemetry/999')
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Telemetry entry not found')

    def test_get_telemetry_by_id_empty_database(self):
        """Test GET /telemetry/<id> on empty database."""
        response = self.client.get('/telemetry/1')
        self.assertEqual(response.status_code, 404)

    # ===== POST /telemetry Tests =====

    def test_post_telemetry_success(self):
        """Test POST /telemetry with valid data."""
        payload = {
            'satelliteId': 'SAT001',
            'timestamp': '2025-12-10T10:00:00Z',
            'altitude': 400,
            'velocity': 7.8,
            'status': 'healthy'
        }
        response = self.client.post(
            '/telemetry',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertIn('id', data)
        self.assertEqual(data['message'], 'Telemetry entry added')

    def test_post_telemetry_missing_satellite_id(self):
        """Test POST /telemetry missing satelliteId."""
        payload = {
            'timestamp': '2025-12-10T10:00:00Z',
            'altitude': 400,
            'velocity': 7.8,
            'status': 'healthy'
        }
        response = self.client.post(
            '/telemetry',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('satelliteId', data['error'])

    def test_post_telemetry_missing_timestamp(self):
        """Test POST /telemetry missing timestamp."""
        payload = {
            'satelliteId': 'SAT001',
            'altitude': 400,
            'velocity': 7.8,
            'status': 'healthy'
        }
        response = self.client.post(
            '/telemetry',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('timestamp', data['error'])

    def test_post_telemetry_missing_altitude(self):
        """Test POST /telemetry missing altitude."""
        payload = {
            'satelliteId': 'SAT001',
            'timestamp': '2025-12-10T10:00:00Z',
            'velocity': 7.8,
            'status': 'healthy'
        }
        response = self.client.post(
            '/telemetry',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('altitude', data['error'])

    def test_post_telemetry_missing_velocity(self):
        """Test POST /telemetry missing velocity."""
        payload = {
            'satelliteId': 'SAT001',
            'timestamp': '2025-12-10T10:00:00Z',
            'altitude': 400,
            'status': 'healthy'
        }
        response = self.client.post(
            '/telemetry',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('velocity', data['error'])

    def test_post_telemetry_missing_status(self):
        """Test POST /telemetry missing status."""
        payload = {
            'satelliteId': 'SAT001',
            'timestamp': '2025-12-10T10:00:00Z',
            'altitude': 400,
            'velocity': 7.8
        }
        response = self.client.post(
            '/telemetry',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('status', data['error'])

    def test_post_telemetry_invalid_timestamp(self):
        """Test POST /telemetry with invalid timestamp."""
        payload = {
            'satelliteId': 'SAT001',
            'timestamp': 'not-a-timestamp',
            'altitude': 400,
            'velocity': 7.8,
            'status': 'healthy'
        }
        response = self.client.post(
            '/telemetry',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('Invalid timestamp', data['error'])

    def test_post_telemetry_invalid_status(self):
        """Test POST /telemetry with invalid status."""
        payload = {
            'satelliteId': 'SAT001',
            'timestamp': '2025-12-10T10:00:00Z',
            'altitude': 400,
            'velocity': 7.8,
            'status': 'unknown'
        }
        response = self.client.post(
            '/telemetry',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('healthy', data['error'].lower())

    def test_post_telemetry_invalid_altitude_string(self):
        """Test POST /telemetry with altitude as string."""
        payload = {
            'satelliteId': 'SAT001',
            'timestamp': '2025-12-10T10:00:00Z',
            'altitude': 'not-a-number',
            'velocity': 7.8,
            'status': 'healthy'
        }
        response = self.client.post(
            '/telemetry',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('numeric', data['error'])

    def test_post_telemetry_invalid_velocity_string(self):
        """Test POST /telemetry with velocity as string."""
        payload = {
            'satelliteId': 'SAT001',
            'timestamp': '2025-12-10T10:00:00Z',
            'altitude': 400,
            'velocity': 'not-a-number',
            'status': 'healthy'
        }
        response = self.client.post(
            '/telemetry',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('numeric', data['error'])

    def test_post_telemetry_negative_altitude(self):
        """Test POST /telemetry with negative altitude."""
        payload = {
            'satelliteId': 'SAT001',
            'timestamp': '2025-12-10T10:00:00Z',
            'altitude': -100,
            'velocity': 7.8,
            'status': 'healthy'
        }
        response = self.client.post(
            '/telemetry',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('non-negative', data['error'])

    def test_post_telemetry_negative_velocity(self):
        """Test POST /telemetry with negative velocity."""
        payload = {
            'satelliteId': 'SAT001',
            'timestamp': '2025-12-10T10:00:00Z',
            'altitude': 400,
            'velocity': -7.8,
            'status': 'healthy'
        }
        response = self.client.post(
            '/telemetry',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('non-negative', data['error'])

    def test_post_telemetry_zero_altitude(self):
        """Test POST /telemetry with zero altitude (valid)."""
        payload = {
            'satelliteId': 'SAT001',
            'timestamp': '2025-12-10T10:00:00Z',
            'altitude': 0,
            'velocity': 7.8,
            'status': 'healthy'
        }
        response = self.client.post(
            '/telemetry',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)

    def test_post_telemetry_zero_velocity(self):
        """Test POST /telemetry with zero velocity (valid)."""
        payload = {
            'satelliteId': 'SAT001',
            'timestamp': '2025-12-10T10:00:00Z',
            'altitude': 400,
            'velocity': 0,
            'status': 'healthy'
        }
        response = self.client.post(
            '/telemetry',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)

    def test_post_telemetry_creates_entry_in_db(self):
        """Test that POST /telemetry creates entry in database."""
        payload = {
            'satelliteId': 'SAT001',
            'timestamp': '2025-12-10T10:00:00Z',
            'altitude': 400,
            'velocity': 7.8,
            'status': 'healthy'
        }
        response = self.client.post(
            '/telemetry',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        
        # Verify entry exists
        response_get = self.client.get('/telemetry/1')
        self.assertEqual(response_get.status_code, 200)
        data = json.loads(response_get.data)
        self.assertEqual(data['satelliteId'], 'SAT001')

    def test_post_telemetry_float_altitude(self):
        """Test POST /telemetry with float altitude."""
        payload = {
            'satelliteId': 'SAT001',
            'timestamp': '2025-12-10T10:00:00Z',
            'altitude': 400.5,
            'velocity': 7.8,
            'status': 'healthy'
        }
        response = self.client.post(
            '/telemetry',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)

    def test_post_telemetry_float_velocity(self):
        """Test POST /telemetry with float velocity."""
        payload = {
            'satelliteId': 'SAT001',
            'timestamp': '2025-12-10T10:00:00Z',
            'altitude': 400,
            'velocity': 7.8432,
            'status': 'healthy'
        }
        response = self.client.post(
            '/telemetry',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)

    # ===== DELETE /telemetry/<id> Tests =====

    def test_delete_telemetry_success(self):
        """Test DELETE /telemetry/<id> with valid id."""
        self.insert_sample_data()
        response = self.client.delete('/telemetry/1')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['message'], 'Telemetry entry deleted')

    def test_delete_telemetry_not_found(self):
        """Test DELETE /telemetry/<id> with non-existent id."""
        response = self.client.delete('/telemetry/999')
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Telemetry entry not found')

    def test_delete_telemetry_removes_from_db(self):
        """Test that DELETE /telemetry/<id> removes entry from database."""
        self.insert_sample_data()
        
        # Verify entry exists
        response_before = self.client.get('/telemetry/1')
        self.assertEqual(response_before.status_code, 200)
        
        # Delete entry
        response_delete = self.client.delete('/telemetry/1')
        self.assertEqual(response_delete.status_code, 200)
        
        # Verify entry is gone
        response_after = self.client.get('/telemetry/1')
        self.assertEqual(response_after.status_code, 404)

    def test_delete_telemetry_multiple(self):
        """Test deleting multiple different entries."""
        self.insert_sample_data()
        
        # Delete entry 1
        response1 = self.client.delete('/telemetry/1')
        self.assertEqual(response1.status_code, 200)
        
        # Delete entry 3
        response3 = self.client.delete('/telemetry/3')
        self.assertEqual(response3.status_code, 200)
        
        # Verify they're gone
        self.assertEqual(self.client.get('/telemetry/1').status_code, 404)
        self.assertEqual(self.client.get('/telemetry/3').status_code, 404)
        
        # Verify others exist
        self.assertEqual(self.client.get('/telemetry/2').status_code, 200)

    def test_delete_telemetry_empty_database(self):
        """Test DELETE /telemetry/<id> on empty database."""
        response = self.client.delete('/telemetry/1')
        self.assertEqual(response.status_code, 404)

    # ===== Integration Tests =====

    def test_full_workflow(self):
        """Test complete workflow: POST, GET, GET by id, DELETE."""
        # POST
        payload = {
            'satelliteId': 'SAT001',
            'timestamp': '2025-12-10T10:00:00Z',
            'altitude': 400,
            'velocity': 7.8,
            'status': 'healthy'
        }
        post_response = self.client.post(
            '/telemetry',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(post_response.status_code, 201)
        entry_id = json.loads(post_response.data)['id']
        
        # GET all
        get_all_response = self.client.get('/telemetry')
        get_all_data = json.loads(get_all_response.data)
        self.assertEqual(len(get_all_data['data']), 1)
        
        # GET by id
        get_by_id_response = self.client.get(f'/telemetry/{entry_id}')
        self.assertEqual(get_by_id_response.status_code, 200)
        
        # DELETE
        delete_response = self.client.delete(f'/telemetry/{entry_id}')
        self.assertEqual(delete_response.status_code, 200)
        
        # Verify deleted
        get_after_delete = self.client.get(f'/telemetry/{entry_id}')
        self.assertEqual(get_after_delete.status_code, 404)

    def test_multiple_entries_with_filters(self):
        """Test operations with multiple entries and filters."""
        # Add multiple entries
        for i in range(5):
            payload = {
                'satelliteId': f'SAT{i:03d}',
                'timestamp': f'2025-12-10T{10+i:02d}:00:00Z',
                'altitude': 400 + (i * 10),
                'velocity': 7.8 + (i * 0.1),
                'status': 'healthy' if i % 2 == 0 else 'critical'
            }
            response = self.client.post(
                '/telemetry',
                data=json.dumps(payload),
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 201)
        
        # Get all
        response = self.client.get('/telemetry?per_page=100')
        data = json.loads(response.data)
        self.assertEqual(data['pagination']['total'], 5)
        
        # Filter by status
        response = self.client.get('/telemetry?status=healthy&per_page=100')
        data = json.loads(response.data)
        self.assertEqual(len(data['data']), 3)

    def test_pagination_with_sorting(self):
        """Test pagination combined with sorting."""
        self.insert_sample_data()
        
        # Get first page sorted by altitude descending
        response = self.client.get('/telemetry?page=1&per_page=2&sort_by=altitude&sort_order=desc')
        data = json.loads(response.data)
        
        self.assertEqual(len(data['data']), 2)
        self.assertEqual(data['sorting']['sort_by'], 'altitude')
        self.assertEqual(data['sorting']['sort_order'], 'desc')


if __name__ == '__main__':
    unittest.main()
