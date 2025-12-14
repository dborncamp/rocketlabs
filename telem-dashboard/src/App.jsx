import { useState, useEffect, useRef } from 'react'
import Plotly from 'plotly.js-dist-min'
import './App.css'

function App() {
  // State for telemetry data
  const [telemetry, setTelemetry] = useState([])
  const [filteredTelemetry, setFilteredTelemetry] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // State for pagination
  const [currentPage, setCurrentPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [total, setTotal] = useState(0)
  const itemsPerPage = 20

  // State for filtering
  const [filterSatelliteId, setFilterSatelliteId] = useState('')
  const [filterStatus, setFilterStatus] = useState('')

  // State for sorting
  const [sortColumn, setSortColumn] = useState(null)
  const [sortDirection, setSortDirection] = useState('asc')

  // State for form
  const [formData, setFormData] = useState({
    satelliteId: '',
    timestamp: new Date().toISOString().slice(0, 16),
    altitude: '',
    velocity: '',
    status: 'healthy'
  })
  const [formError, setFormError] = useState('')

  // State for graph
  const [graphSatelliteId, setGraphSatelliteId] = useState('')
  const plotDiv = useRef(null)

  // Fetch telemetry data with filters and pagination
  const fetchTelemetry = async (page = 1, sortBy = sortColumn, sortOrder = sortDirection) => {
    setLoading(true)
    setError(null)
    try {
      let url = `telemetry?page=${page}&per_page=${itemsPerPage}`
      if (filterSatelliteId) url += `&satelliteId=${filterSatelliteId}`
      if (filterStatus) url += `&status=${filterStatus}`
      if (sortBy) url += `&sort_by=${sortBy}&sort_order=${sortOrder}`

      const response = await fetch(url)
      if (!response.ok) throw new Error('Failed to fetch telemetry')
      
      const data = await response.json()
      setTelemetry(data.data)
      setCurrentPage(data.pagination.page)
      setTotalPages(data.pagination.total_pages)
      setTotal(data.pagination.total)
      setSortColumn(data.sorting.sort_by)
      setSortDirection(data.sorting.sort_order)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  // Fetch data on component mount and when filters change
  useEffect(() => {
    fetchTelemetry(1)
  }, [filterSatelliteId, filterStatus])

  // Handle sorting
  const handleSort = (column) => {
    let newSortOrder = 'asc'
    if (sortColumn === column && sortDirection === 'asc') {
      newSortOrder = 'desc'
    }
    setSortColumn(column)
    setSortDirection(newSortOrder)
    fetchTelemetry(1, column, newSortOrder)
  }

  // Update filtered telemetry when data changes (no longer doing client-side sorting)
  useEffect(() => {
    setFilteredTelemetry(telemetry)
  }, [telemetry])

  // Validate ISO 8601 timestamp
  const isValidISO8601 = (timestamp) => {
    try {
      const date = new Date(timestamp)
      return !isNaN(date.getTime()) && timestamp !== ''
    } catch {
      return false
    }
  }

  // Handle form submission
  const handleFormSubmit = async (e) => {
    e.preventDefault()
    setFormError('')

    // Validate fields
    if (!formData.satelliteId.trim()) {
      setFormError('Satellite ID is required')
      return
    }
    if (!formData.timestamp) {
      setFormError('Timestamp is required')
      return
    }
    if (!isValidISO8601(formData.timestamp)) {
      setFormError('Invalid timestamp format')
      return
    }
    if (!formData.altitude || isNaN(parseFloat(formData.altitude))) {
      setFormError('Altitude must be a valid number')
      return
    }
    if (!formData.velocity || isNaN(parseFloat(formData.velocity))) {
      setFormError('Velocity must be a valid number')
      return
    }
    if (parseFloat(formData.altitude) < 0 || parseFloat(formData.velocity) < 0) {
      setFormError('Altitude and Velocity must be non-negative')
      return
    }

    try {
      const response = await fetch('/telemetry', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          satelliteId: formData.satelliteId,
          timestamp: new Date(formData.timestamp).toISOString(),
          altitude: parseFloat(formData.altitude),
          velocity: parseFloat(formData.velocity),
          status: formData.status
        })
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.error || 'Failed to add telemetry')
      }

      // Reset form and refresh data
      setFormData({
        satelliteId: '',
        timestamp: new Date().toISOString().slice(0, 16),
        altitude: '',
        velocity: '',
        status: 'healthy'
      })
      fetchTelemetry(1)
    } catch (err) {
      setFormError(err.message)
    }
  }

  // Handle delete
  const handleDelete = async (id) => {
    if (!confirm('Are you sure you want to delete this entry?')) return

    try {
      const response = await fetch(`/telemetry/${id}`, {
        method: 'DELETE'
      })

      if (!response.ok) throw new Error('Failed to delete telemetry')

      fetchTelemetry(currentPage)
    } catch (err) {
      setError(err.message)
    }
  }

  // Load and plot graph data
  const handlePlotGraph = async () => {
    if (!graphSatelliteId.trim()) {
      setError('Please enter a Satellite ID')
      return
    }

    try {
      const response = await fetch(`/telemetry?satelliteId=${graphSatelliteId}&per_page=1000`)
      if (!response.ok) throw new Error('Failed to fetch data for graph')

      const data = await response.json()
      const entries = data.data

      if (entries.length === 0) {
        setError('No data found for this satellite ID')
        return
      }

      // Sort by timestamp
      entries.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp))

      const timestamps = entries.map(e => e.timestamp)
      const altitudes = entries.map(e => e.altitude)
      const velocities = entries.map(e => e.velocity)

      const trace1 = {
        x: timestamps,
        y: altitudes,
        type: 'scatter',
        mode: 'lines+markers',
        name: 'Altitude (km)',
        yaxis: 'y1'
      }

      const trace2 = {
        x: timestamps,
        y: velocities,
        type: 'scatter',
        mode: 'lines+markers',
        name: 'Velocity (km/s)',
        yaxis: 'y2'
      }

      const layout = {
        title: `Telemetry Data for Satellite ${graphSatelliteId}`,
        xaxis: { title: 'Timestamp' },
        yaxis: { title: 'Altitude (km)', side: 'left' },
        yaxis2: { title: 'Velocity (km/s)', overlaying: 'y', side: 'right' },
        hovermode: 'x unified'
      }

      Plotly.newPlot(plotDiv.current, [trace1, trace2], layout)
      setError(null)
    } catch (err) {
      setError(err.message)
    }
  }

  const getSortIndicator = (column) => {
    if (sortColumn !== column) return ' ⇅'
    return sortDirection === 'asc' ? ' ↑' : ' ↓'
  }

  return (
    <div className="container">
      <h1>RocketLabs Code Challenge Satellite Telemetry Dashboard</h1>

      {error && <div className="error-message">{error}</div>}

      {/* Form Section */}
      <section className="form-section">
        <h2>Add New Telemetry Entry</h2>
        <form onSubmit={handleFormSubmit}>
          {formError && <div className="error-message">{formError}</div>}
          <div className="form-group">
            <label>Satellite ID:</label>
            <input
              type="text"
              value={formData.satelliteId}
              onChange={(e) => setFormData({ ...formData, satelliteId: e.target.value })}
            />
          </div>
          <div className="form-group">
            <label>Timestamp:</label>
            <input
              type="datetime-local"
              value={formData.timestamp}
              onChange={(e) => setFormData({ ...formData, timestamp: e.target.value })}
            />
          </div>
          <div className="form-group">
            <label>Altitude (km):</label>
            <input
              type="number"
              value={formData.altitude}
              onChange={(e) => setFormData({ ...formData, altitude: e.target.value })}
            />
          </div>
          <div className="form-group">
            <label>Velocity (km/s):</label>
            <input
              type="number"
              value={formData.velocity}
              onChange={(e) => setFormData({ ...formData, velocity: e.target.value })}
            />
          </div>
          <div className="form-group">
            <label>Status:</label>
            <select value={formData.status} onChange={(e) => setFormData({ ...formData, status: e.target.value })}>
              <option value="healthy">Healthy</option>
              <option value="critical">Critical</option>
            </select>
          </div>
          <button type="submit">Add Entry</button>
        </form>
      </section>

      {/* Filter Section */}
      <section className="table-section">
      <section className="filter-section">
        <h2>Filters</h2>
        <div className="filter-group">
          <label>Satellite ID:</label>
          <input
            type="text"
            value={filterSatelliteId}
            onChange={(e) => {
              setFilterSatelliteId(e.target.value)
              setCurrentPage(1)
            }}
            placeholder="Filter by satellite ID"
          />
        </div>
        <div className="filter-group">
          <label>Status:</label>
          <select
            value={filterStatus}
            onChange={(e) => {
              setFilterStatus(e.target.value)
              setCurrentPage(1)
            }}
          >
            <option value="">All</option>
            <option value="healthy">Healthy</option>
            <option value="critical">Critical</option>
          </select>
        </div>
      </section>

      {/* Table Section */}
        <h2>Telemetry Data</h2>
        {loading ? (
          <p>Loading...</p>
        ) : filteredTelemetry.length === 0 ? (
          <p>No telemetry data found.</p>
        ) : (
          <>
            <div className="table-wrapper">
              <table>
                <thead>
                  <tr>
                    <th onClick={() => handleSort('satelliteId')}>Satellite ID{getSortIndicator('satelliteId')}</th>
                    <th onClick={() => handleSort('timestamp')}>Timestamp{getSortIndicator('timestamp')}</th>
                    <th onClick={() => handleSort('altitude')}>Altitude (km){getSortIndicator('altitude')}</th>
                    <th onClick={() => handleSort('velocity')}>Velocity (km/s){getSortIndicator('velocity')}</th>
                    <th onClick={() => handleSort('status')}>Status{getSortIndicator('status')}</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredTelemetry.map((entry) => (
                    <tr key={entry.id}>
                      <td>{entry.satelliteId}</td>
                      <td>{new Date(entry.timestamp).toLocaleString()}</td>
                      <td>{entry.altitude}</td>
                      <td>{entry.velocity}</td>
                      <td className={entry.status === 'critical' ? 'status-critical' : 'status-healthy'}>
                        {entry.status}
                      </td>
                      <td>
                        <button className="delete-btn" onClick={() => handleDelete(entry.id)}>
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            <div className="pagination">
              <button
                onClick={() => fetchTelemetry(currentPage - 1)}
                disabled={currentPage === 1}
              >
                Previous
              </button>
              <span>
                Page {currentPage} of {totalPages} (Total: {total})
              </span>
              <button
                onClick={() => fetchTelemetry(currentPage + 1)}
                disabled={currentPage === totalPages}
              >
                Next
              </button>
            </div>
          </>
        )}
      </section>

      {/* Graph Section */}
      <section className="graph-section">
        <h2>Altitude & Velocity Graph</h2>
        <div className="graph-input">
          <input
            type="text"
            value={graphSatelliteId}
            onChange={(e) => setGraphSatelliteId(e.target.value)}
            placeholder="Enter Satellite ID"
          />
          <button onClick={handlePlotGraph}>Plot Graph</button>
        </div>
        <div ref={plotDiv} id="plot" style={{ width: '100%', height: '500px' }}></div>
      </section>
    </div>
  )
}

export default App
