# RocketLab Code Challenge

;tldr

Using Docker (the image is available on Docker Hub):

```bash
docker run -p 5000:5000 dborncamp/rocketlabs:latest
```

visit `http://localhost:5000` to see the application running.
Dummy example data is included in the container to illustrate the functionality.
Enjoy!

---

This is for the RocketLabs code challenge which was given to me on 12/12/2025.
The goal for this project is to make an application that models a space ground system by creating a telemetry dashboard.
It has two components: a backend that simulates a spacecraft sending telemetry data, and a frontend that displays the data.

I chose to use Vite with React and Flask for the frontend and Flask for the backend.
I leaned heavily on the [flaskMega Tutorial](https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world) for the backend structure and ideas.
And the [React + Flask series](https://blog.miguelgrinberg.com/post/create-a-react-flask-project-in-2025) help with getting react and Flask to talk to each other.

## Docker Setup

A multistage Dockerfile is provided to build and run the application.
While there are several upgrades that could be made to the application efficient (discussed later), this is a functional starting point.
The first stage builds the React frontend using a Node.js image, and the second stage sets up a Python Flask server to serve both the API and the built frontend.
The final image uses `gunicorn` to run the Flask application that serves both the API and the static files that were built in the first stage.

```bash
docker build -t rocketlabs-dashboard:latest -f Dockerfile.yaml .
docker run -p 5000:5000 rocketlabs-dashboard:latest
```

visit `http://localhost:5000` to see the application running.

## Backend API

Many of these things could be implemented with async or something for asynchronicity, but for the purposes of this exercise, I am keeping it simple.
Both a Backend and Frontend are required, so I am focusing on functionality over performance optimizations that are not included in the project requirements.

The API focuses on the `/telemetry` endpoint that has the following functionalities:

- GET `/telemetry`: Retrieve all telemetry data. This has the optional query parameters:
  - satelliteId: Filter by satellite ID.
  - status: Filter by health status (e.g., “healthy”, “critical”).
- POST `/telemetry`: Add a new telemetry entry.
- GET `/telemetry`/:id: Retrieve a specific telemetry entry by ID.
- DELETE `/telemetry`/:id: Delete a specific telemetry entry.

Request body should include the following fields with their respective data types:

### Data Schema

```json
{
    "satelliteId": "string",
    "timestamp": "An ISO 8601 datetime",
    "altitude": "number",
    "velocity": "number",
    "status": "string; either 'healthy' or 'critical'"
}
```

When data is posted, the timestamp should be validated to ensure it is in the correct ISO 8601 format.
The data will be stored in an SQLite database using a Flask backend for API endpoints.
At this point, I assume that the status field will only have two possible values: "healthy" and "critical".

### Local Development Setup

Get Python and NPM set up on your machine.
I use conda for Python environment management and nvm for Node.js version management.

```bash
# Install python 3.14 environment
conda create -n rocketlabs python=3.14 python-dotenv flask
conda activate rocketlabs

# Install Node.js version 24 using nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  # This loads nvm bash_completion
nvm install 24

# Run the backend API server
npm run api
```

To run with separate frontend and backend servers, change the `vite.config.js` to not proxy API requests to the Flask server and change the package.json to remove the api reference.
This would be a good place to break out the frontend and backend into separate containers in the future.
Instructions for starting the frontend server are in the Frontend section below.

### Posting Data to Backend

An example of posting data to the backend using curl for local testing:

```bash
curl --header "Content-Type: application/json" --request POST --data '{"satelliteId": "1h5", "timestamp": "2025-12-12T18:39:35.000Z", "altitude": 500, "velocity": 100, "status": "healthy" }'  http://localhost:5000/telemetry
```

## Frontend

The frontend is built with Vite and React and uses React's `useState` and `useEffect` hooks to manage state and side effects.
It's objective is to be "a web interface to display and manage satellite telemetry data."
To do that it has the following features:

- The ability to post data to the Flask backend API.
  - This data is validated on the frontend before being sent to the backend and will conform to the backend data Schema.
- Display a table of telemetry data with columns: Satellite ID, Timestamp, Altitude, Velocity, Health Status.
  - The table fetches data from the Flask backend API.
  - The table supports pagination to handle large datasets.
  - The table allows sorting by any column.
- Allow users to filter telemetry data by Satellite ID and Health Status.
- Provide a form to add new telemetry entries.
- Allow users to delete telemetry entries.
- Has a plotly.js graph to visualize altitude and velocity over time for a given satellite id using data taken from the backend API.

### Running the Frontend Application Locally

Install Python and NPM on your machine.

```bash
# Install python 3.14 environment
conda create -n rocketlabs python=3.14 python-dotenv flask
conda activate rocketlabs

# Install Node.js version 24 using nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  # This loads nvm bash_completion
nvm install 24
```

Start the backend API server in one terminal:

```bash
npm run api
```

Start the frontend development server in another terminal:

```bash
npm install
npm run dev
```

The frontend will be available at `http://localhost:5173` and the backend API at `http://localhost:5000`.

### Frontend Navigation

The first page is a section to add telemetry data to the database.
This POSTs data to the backend API and does validation on user input.
For example, strings are not allowed in the altitude or velocity fields, and the timestamp must be in ISO 8601 format which is restricted to using a datetime-local input type.

The second section is a table and filters to view the telemetry data.
The table allows sorting by clicking on the column headers, and filtering by satellite ID and health status.
Each row has a delete button to remove that telemetry entry from the database.
Pagination is implemented to show 20 entries per page, a new request is made on each sort to correctly return the view of the data.

Finally, there is a graph section that uses plotly.js to visualize altitude and velocity over time for a given satellite ID.
An existing satellite ID must be provided to see the data, however no validation is done to check if the satellite ID exists before making the request at this time.

## Unit Tests

Unit tests are provided for the backend API using PyTest.
Knowing that RocketLabs uses AI, I allowed AI create the initial tests and then modified them to fit the application better.
I was surprised at how well it worked, and it saved me a lot of time.

The tests are based on the `unittest` module but can be run using `pytest` for better output formatting.

**Optional:**

To install `pytest` in your Python environment:

```bash
pip install pytest
```

Then, run the tests get into the `telem-dashboard/api` directory and run the tests

```bash
cd telem-dashboard/api
```

And either run with pytest:

```bash
pytest tests/test_api.py -v
```

Or with python -m unittest:

```bash
python -m unittest tests/test_api.py -v
```

See [api/tests/TESTING.md](telem-dashboard/api/tests/TESTING.md) for the full documentation of the test suite.

## Future Improvements

- Allow for other status values beyond "healthy" and "critical".
- Make the dockerfile smaller and more efficient.
  - Break out the frontend and backend into separate containers to allow for better scaling and management.
- Add authentication and authorization to the API.
- Add configuration options for the backend server (e.g., port, database location debug mode).
- Implement WebSocket support for real-time telemetry updates.
- Improve error handling and logging in both frontend and backend.
- Check for existing satellite IDs before making requests to the backend for graphing or give user feedback if no data is found.
- Add unit tests for the frontend components.
