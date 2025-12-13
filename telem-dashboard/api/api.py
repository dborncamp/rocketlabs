"""
API for managing satellite telemetry data.

Many of these things could be implemented with async or something for asynchronicity, but for the purposes of this exercise, I am keeping it simple.
Both a Backend and Frontend are required, so I am focusing on functionality over performance optimizations that are not included in the project requirements.

"""

import sqlite3
from flask import Flask, request, jsonify
from datetime import datetime
import os

app = Flask(__name__, static_folder='../dist', static_url_path='/')

# Database setup
DATABASE = 'telemetry.db'

# Initialize database on startup

def init_db():
    """
    Initialize the database with the telemetry table.
    
    Assume that the database name or schema will never change for this exercise.
    In an actual production system, you would want to use a more robust system where it would not be instantiating itself.
    """
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS telemetry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            satelliteId TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            altitude REAL NOT NULL,
            velocity REAL NOT NULL,
            status TEXT NOT NULL
        )
    ''')
    db.commit()
    db.close()

if not os.path.exists(DATABASE):
    init_db()



# Now for the functionality

@app.before_request
def clear_trailing():
    """Redirect paths with trailing slashes to non-trailing slash versions because Flask defaults to strict slashes and I want to avoid 400s."""
    from flask import redirect, request

    rp = request.path 
    if rp != '/' and rp.endswith('/'):
        return redirect(rp[:-1])

def get_db():
    """Get a database connection."""
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db


def validate_iso(timestamp_str):
    """Validate that a timestamp is in ISO 8601 format."""
    try:
        datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return True
    except (ValueError, AttributeError):
        return False

def validate_status(status):
    """Validate the status
    """
    return status in ['healthy', 'critical']

@app.route('/telemetry', methods=['GET'])
def get_telemetry():
    """Retrieve telemetry data with optional filtering, sorting, and pagination."""
    db = get_db()
    cursor = db.cursor()
    
    # Get query parameters for filtering
    satellite_id = request.args.get('satelliteId')
    status = request.args.get('status')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    sort_by = request.args.get('sort_by', 'id')
    sort_order = request.args.get('sort_order', 'asc')
    
    # Ensure valid pagination parameters
    page = max(1, page)
    per_page = max(1, min(per_page, 100))  # Cap at 100 items per page
    
    # Validate sort parameters to prevent SQL injection
    valid_columns = ['id', 'satelliteId', 'timestamp', 'altitude', 'velocity', 'status']
    if sort_by not in valid_columns:
        sort_by = 'id'
    
    if sort_order.lower() not in ['asc', 'desc']:
        sort_order = 'asc'
    
    # Build the base query
    query = 'SELECT * FROM telemetry WHERE 1=1'
    count_query = 'SELECT COUNT(*) as total FROM telemetry WHERE 1=1'
    params = []
    
    if satellite_id:
        query += ' AND satelliteId = ?'
        count_query += ' AND satelliteId = ?'
        params.append(satellite_id)
    
    if status:
        query += ' AND status = ?'
        count_query += ' AND status = ?'
        params.append(status)
    
    # Get total count
    cursor.execute(count_query, params)
    total = cursor.fetchone()['total']
    
    # Add sorting
    query += f' ORDER BY {sort_by} {sort_order}'
    
    # Calculate pagination
    offset = (page - 1) * per_page
    query += ' LIMIT ? OFFSET ?'
    params.extend([per_page, offset])
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    db.close()
    
    total_pages = (total + per_page - 1) // per_page
    
    return jsonify({
        'data': [dict(row) for row in rows],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'total_pages': total_pages
        },
        'sorting': {
            'sort_by': sort_by,
            'sort_order': sort_order
        }
    })

@app.route('/telemetry/<int:entry_id>', methods=['GET'])
def get_telemetry_by_id(entry_id):
    """Retrieve a specific telemetry entry by ID."""
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('SELECT * FROM telemetry WHERE id = ?', (entry_id,))
    row = cursor.fetchone()
    db.close()
    
    if not row:
        return jsonify({'error': 'Telemetry entry not found'}), 404
    
    return jsonify(dict(row))

@app.route('/telemetry', methods=['POST'])
def add_telemetry():
    """Add a new telemetry entry."""
    data = request.get_json()
    
    # Validate required fields are present
    required_fields = ['satelliteId', 'timestamp', 'altitude', 'velocity', 'status']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    # Validate timestamp format
    if not validate_iso(data['timestamp']):
        return jsonify({'error': 'Invalid timestamp format. Must be ISO 8601.'}), 400
    
    # Validate status
    if not validate_status(data['status']):
        return jsonify({'error': 'Status must be either "healthy" or "critical".'}), 400
    
    # Validate numeric fields
    try:
        altitude = float(data['altitude'])
        velocity = float(data['velocity'])
    except (ValueError, TypeError):
        return jsonify({'error': 'Altitude and velocity must be numeric.'}), 400
    
    if altitude < 0 or velocity < 0:
        return jsonify({'error': 'Altitude and velocity must be non-negative.'}), 400
    
    # Now that everything is validated, insert into the database
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('''
        INSERT INTO telemetry (satelliteId, timestamp, altitude, velocity, status)
        VALUES (?, ?, ?, ?, ?)
    ''', (data['satelliteId'], data['timestamp'], altitude, velocity, data['status']))
    
    db.commit()
    new_id = cursor.lastrowid
    db.close()
    
    # return 201 for successfully created
    return jsonify({'id': new_id, 'message': 'Telemetry entry added'}), 201


@app.route('/telemetry/<int:entry_id>', methods=['DELETE'])
def delete_telemetry(entry_id):
    """Delete a specific telemetry entry by ID."""
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('SELECT * FROM telemetry WHERE id = ?', (entry_id,))
    row = cursor.fetchone()
    
    if not row:
        db.close()
        return jsonify({'error': 'Telemetry entry not found'}), 404
    
    cursor.execute('DELETE FROM telemetry WHERE id = ?', (entry_id,))
    db.commit()
    db.close()
    
    return jsonify({'message': 'Telemetry entry deleted'}), 200


@app.route('/')
def index():
    """
    Serve the React frontend.
    
    In a production system, you would likely want to have more robust handling here,
    possibly with error handling for missing files, etc.
    In a production system, you might also want to serve different files based on routes and 
    be able to scale static file serving by adding it in another k8s service or using a CDN.
    Basically, move it closer to the user and away from the application server.
    But this is not a production system, so keeping it simple for now
    """
    return app.send_static_file('index.html')

