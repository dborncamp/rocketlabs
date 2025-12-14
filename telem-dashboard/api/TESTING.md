# Telemetry API Testing Documentation

## Overview

This document provides comprehensive information about testing the telemetry API backend. The test suite includes 94 unit tests covering all functionality in `api.py` and `util.py`.

## Test Structure

The test suite is organized into three main test classes:

1. **UtilFunctionsTestCase** - Tests for utility functions (6 tests)
2. **ValidationFunctionsTestCase** - Tests for validation functions (21 tests)
3. **TelemetryAPITestCase** - Tests for API endpoints (67 tests)

**Total: 94 comprehensive unit tests**

## Running the Tests

### Prerequisites

Ensure you have the dependencies installed:

```bash
pip install -r requirements.txt
```

### Run All Tests

```bash
cd telem-dashboard/api/
python -m unittest tests/test_api.py
```

### Run All Tests with Verbose Output

```bash
cd telem-dashboard/api/
python -m unittest tests/test_api.py -v
```

### Run Specific Test Class

```bash
# Utility functions tests
python -m unittest test_api.UtilFunctionsTestCase -v

# Validation functions tests
python -m unittest test_api.ValidationFunctionsTestCase -v

# API endpoint tests
python -m unittest test_api.TelemetryAPITestCase -v
```

### Run Specific Test Method

```bash
python -m unittest test_api.TelemetryAPITestCase.test_post_telemetry_success -v
```

### Run Tests with Coverage Report

```bash
pip install coverage
cd telem-dashboard/api/
coverage run -m unittest tests/test_api.py
coverage report
coverage html  # Generates HTML coverage report
```

## Test Coverage Details

### Utility Functions Tests (6 tests)

Tests for `util.py` functions:

#### `init_db(database)` Tests

- **test_init_db_creates_table**: Verifies that `init_db()` creates the telemetry table
- **test_init_db_table_structure**: Confirms table has correct columns (id, satelliteId, timestamp, altitude, velocity, status)
- **test_init_db_idempotent**: Ensures `init_db()` can be called multiple times safely

#### `get_db(database)` Tests

- **test_get_db_returns_connection**: Verifies `get_db()` returns a valid SQLite connection object
- **test_get_db_row_factory**: Confirms `row_factory` is set to `sqlite3.Row` for column access
- **test_get_db_creates_file**: Tests that `get_db()` creates the database file if it doesn't exist

### Validation Functions Tests (21 tests)

Tests for `api.py` validation functions:

#### `validate_iso(timestamp_str)` Tests (11 tests)

Valid timestamps:

- `test_validate_iso_valid_z_format`: Validates timestamps with Z timezone (e.g., "2025-12-10T10:00:00Z")
- `test_validate_iso_valid_plus_offset`: Validates timestamps with +00:00 offset
- `test_validate_iso_valid_with_milliseconds`: Validates timestamps with milliseconds (e.g., "2025-12-10T10:00:00.000Z")
- `test_validate_iso_valid_without_timezone`: Validates timestamps without timezone
- `test_validate_iso_valid_negative_offset`: Validates timestamps with negative offset (e.g., -05:00)

Invalid timestamps:

- `test_validate_iso_invalid_format`: Tests with "12-10-2025" format
- `test_validate_iso_invalid_date_slash`: Tests with slashes "2025/12/10"
- `test_validate_iso_invalid_month`: Tests with invalid month "2025-13-01T00:00:00Z"
- `test_validate_iso_invalid_day`: Tests with invalid day "2025-12-32T00:00:00Z"
- `test_validate_iso_non_string`: Tests with non-string input (integer)
- `test_validate_iso_empty_string`: Tests with empty string
- `test_validate_iso_none`: Tests with None value

#### `validate_status(status)` Tests (10 tests)

Valid statuses:

- `test_validate_status_healthy`: Tests "healthy" status
- `test_validate_status_critical`: Tests "critical" status

Invalid statuses:

- `test_validate_status_case_sensitive`: Verifies status validation is case-sensitive
- `test_validate_status_invalid`: Tests invalid value "warning"
- `test_validate_status_empty`: Tests with empty string
- `test_validate_status_none`: Tests with None value

### API Endpoint Tests (67 tests)

#### GET /telemetry Tests (25 tests)

**Basic Functionality**

- `test_get_telemetry_empty`: Returns empty data for empty database
- `test_get_telemetry_all_data`: Returns all data with high per_page limit
- `test_get_telemetry_response_structure`: Validates response JSON structure

**Pagination Tests**

- `test_get_telemetry_pagination_first_page`: First page retrieval (page=1, per_page=2)
- `test_get_telemetry_pagination_second_page`: Second page retrieval (page=2, per_page=2)
- `test_get_telemetry_pagination_last_page`: Last page retrieval
- `test_get_telemetry_invalid_page_zero`: Page 0 defaults to page 1
- `test_get_telemetry_invalid_page_negative`: Negative page defaults to page 1
- `test_get_telemetry_per_page_cap`: per_page=500 is capped at 100
- `test_get_telemetry_per_page_minimum`: per_page=0 enforces minimum of 1

**Filtering Tests**

- `test_get_telemetry_filter_by_satellite_id`: Filters results by satelliteId
- `test_get_telemetry_filter_by_status`: Filters results by status (healthy/critical)
- `test_get_telemetry_filter_by_both`: Filters by both satelliteId and status
- `test_get_telemetry_filter_no_matches`: Returns empty when no matches found

**Sorting Tests**

- `test_get_telemetry_sort_by_id_asc`: Sorts by id ascending
- `test_get_telemetry_sort_by_id_desc`: Sorts by id descending
- `test_get_telemetry_sort_by_altitude`: Sorts by altitude ascending
- `test_get_telemetry_sort_by_velocity`: Sorts by velocity descending
- `test_get_telemetry_sort_by_satellite_id`: Sorts by satelliteId
- `test_get_telemetry_sort_by_timestamp`: Sorts by timestamp
- `test_get_telemetry_sort_by_status`: Sorts by status
- `test_get_telemetry_invalid_sort_column`: Invalid sort_by defaults to "id"
- `test_get_telemetry_invalid_sort_order`: Invalid sort_order defaults to "asc"

#### GET /telemetry/<id> Tests (4 tests)

- `test_get_telemetry_by_id_success`: Successfully retrieves entry with id=1
- `test_get_telemetry_by_id_different_entries`: Verifies different ids return different entries
- `test_get_telemetry_by_id_not_found`: Returns 404 for non-existent id
- `test_get_telemetry_by_id_empty_database`: Returns 404 on empty database

#### POST /telemetry Tests (24 tests)

**Successful Creation**

- `test_post_telemetry_success`: Creates entry with valid data (201 status)
- `test_post_telemetry_creates_entry_in_db`: Verifies entry is persisted in database

**Missing Required Fields**

- `test_post_telemetry_missing_satellite_id`: Rejects missing satelliteId
- `test_post_telemetry_missing_timestamp`: Rejects missing timestamp
- `test_post_telemetry_missing_altitude`: Rejects missing altitude
- `test_post_telemetry_missing_velocity`: Rejects missing velocity
- `test_post_telemetry_missing_status`: Rejects missing status

**Timestamp Validation**

- `test_post_telemetry_invalid_timestamp`: Rejects invalid timestamp format

**Status Validation**

- `test_post_telemetry_invalid_status`: Rejects invalid status values

**Numeric Validation**

- `test_post_telemetry_invalid_altitude_string`: Rejects non-numeric altitude
- `test_post_telemetry_invalid_velocity_string`: Rejects non-numeric velocity
- `test_post_telemetry_negative_altitude`: Rejects negative altitude
- `test_post_telemetry_negative_velocity`: Rejects negative velocity

**Valid Edge Cases**

- `test_post_telemetry_zero_altitude`: Allows zero altitude
- `test_post_telemetry_zero_velocity`: Allows zero velocity
- `test_post_telemetry_float_altitude`: Accepts float altitude values
- `test_post_telemetry_float_velocity`: Accepts float velocity values

#### DELETE /telemetry/<id> Tests (5 tests)

- `test_delete_telemetry_success`: Successfully deletes entry (200 status)
- `test_delete_telemetry_not_found`: Returns 404 for non-existent id
- `test_delete_telemetry_removes_from_db`: Verifies entry is removed from database
- `test_delete_telemetry_multiple`: Deletes multiple different entries
- `test_delete_telemetry_empty_database`: Returns 404 on empty database

#### Integration Tests (9 tests)

- `test_full_workflow`: Complete workflow POST → GET all → GET by id → DELETE
- `test_multiple_entries_with_filters`: Multiple entries with filtering operations
- `test_pagination_with_sorting`: Pagination combined with sorting

## Sample Test Data

Tests use sample telemetry data:

| ID | Satellite | Timestamp | Altitude | Velocity | Status |
|----|-----------|-----------|----------|----------|--------|
| 1 | SAT001 | 2025-12-10T10:00:00Z | 400 | 7.8 | healthy |
| 2 | SAT001 | 2025-12-10T11:00:00Z | 410 | 7.9 | healthy |
| 3 | SAT001 | 2025-12-10T12:00:00Z | 350 | 6.5 | critical |
| 4 | SAT002 | 2025-12-10T10:30:00Z | 500 | 8.0 | healthy |
| 5 | SAT002 | 2025-12-10T11:30:00Z | 510 | 8.1 | healthy |
| 6 | SAT003 | 2025-12-10T09:00:00Z | 300 | 6.0 | critical |

## Test Isolation

- Each test uses an isolated temporary database
- Database is created in `setUp()` before each test
- Database is cleaned up in `tearDown()` after each test
- No test data leaks between tests
- `DATABASE` constant is patched for tests using `unittest.mock.patch`

## Expected Test Results

All 94 tests should pass:

```txt
Ran 94 tests in X.XXXs

OK
```

## API Endpoints Reference

### GET /telemetry

Retrieve telemetry data with filtering, sorting, and pagination.

**Query Parameters:**

- `satelliteId` (optional): Filter by satellite ID
- `status` (optional): Filter by status (healthy/critical)
- `page` (optional, default: 1): Page number
- `per_page` (optional, default: 20, max: 100): Items per page
- `sort_by` (optional, default: id): Column to sort by (id, satelliteId, timestamp, altitude, velocity, status)
- `sort_order` (optional, default: asc): Sort order (asc, desc)

**Response Structure:**

```json
{
  "data": [
    {
      "id": 1,
      "satelliteId": "SAT001",
      "timestamp": "2025-12-10T10:00:00Z",
      "altitude": 400,
      "velocity": 7.8,
      "status": "healthy"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 100,
    "total_pages": 5
  },
  "sorting": {
    "sort_by": "id",
    "sort_order": "asc"
  }
}
```

### GET /telemetry/<id>

Retrieve a specific telemetry entry by ID.

**Parameters:**

- `id` (path): Entry ID

**Response:**

```json
{
  "id": 1,
  "satelliteId": "SAT001",
  "timestamp": "2025-12-10T10:00:00Z",
  "altitude": 400,
  "velocity": 7.8,
  "status": "healthy"
}
```

### POST /telemetry

Add a new telemetry entry.

**Request Body:**

```json
{
  "satelliteId": "SAT001",
  "timestamp": "2025-12-10T10:00:00Z",
  "altitude": 400,
  "velocity": 7.8,
  "status": "healthy"
}
```

**Response (201 Created):**

```json
{
  "id": 1,
  "message": "Telemetry entry added"
}
```

**Validation:**

- All fields required
- `timestamp` must be ISO 8601 format
- `status` must be "healthy" or "critical"
- `altitude` and `velocity` must be numeric and non-negative

### DELETE /telemetry/<id>

Delete a telemetry entry by ID.

**Parameters:**

- `id` (path): Entry ID

**Response (200 OK):**

```json
{
  "message": "Telemetry entry deleted"
}
```

## Validation Rules

### Timestamp (ISO 8601)

Valid formats:

- `2025-12-10T10:00:00Z`
- `2025-12-10T10:00:00+00:00`
- `2025-12-10T10:00:00-05:00`
- `2025-12-10T10:00:00.000Z`
- `2025-12-10T10:00:00` (no timezone)

### Status

Valid values: `healthy`, `critical` (case-sensitive)

### Numeric Fields (altitude, velocity)

- Must be numeric (int or float)
- Must be non-negative (>= 0)
- Accepts zero values

## Continuous Integration

To use these tests in CI/CD pipelines:

### GitHub Actions Example

```yaml
name: Run Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          pip install flask
      - name: Run tests
        run: |
          cd api
          python -m unittest tests/test_api.py -v
```

## Adding New Tests

To add new tests to the suite:

1. Add a new test method to the appropriate test class
2. Method name must start with `test_`
3. Add descriptive docstring
4. Use `self.client` for HTTP requests
5. Use `self.insert_sample_data()` to populate test data
6. Use `json.loads()` to parse responses
7. Use `self.assertEqual()` and other assertions

**Example:**

```python
def test_new_feature(self):
    """Test description."""
    self.insert_sample_data()
    response = self.client.get('/telemetry?my_param=value')
    self.assertEqual(response.status_code, 200)
    data = json.loads(response.data)
    self.assertIn('key', data)
```

## Database Schema

The telemetry table structure:

```sql
CREATE TABLE telemetry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    satelliteId TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    altitude REAL NOT NULL,
    velocity REAL NOT NULL,
    status TEXT NOT NULL
)
```

## Performance Considerations

- Tests use in-memory SQLite connections for speed
- Each test has isolated database (no shared state)
- Average test suite execution time: < 5 seconds
- Can be run in parallel with proper database isolation
