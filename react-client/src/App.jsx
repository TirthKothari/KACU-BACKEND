import { useState } from 'react'
import axios from 'axios'
import './App.css'

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL

function App() {
  const [loanTypes, setLoanTypes] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const fetchLoanTypes = async () => {
    setLoading(true)
    setError(null)

    try {
      const response = await axios.get(`${BACKEND_URL}/api/loan-types/active/`)
      setLoanTypes(response.data)
      console.log('API Response:', response.data)
    } catch (err) {
      setError(err.message)
      console.error('Error fetching loan types:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="App">
      <h1>KACU Client</h1>
      <p>Backend URL: {BACKEND_URL}</p>

      <button onClick={fetchLoanTypes} disabled={loading}>
        {loading ? 'Loading...' : 'Fetch Active Loan Types'}
      </button>

      {error && (
        <div className="error">
          <h3>Error:</h3>
          <p>{error}</p>
        </div>
      )}

      {loanTypes && (
        <div className="result">
          <h3>Loan Types:</h3>
          <pre>{JSON.stringify(loanTypes, null, 2)}</pre>
        </div>
      )}
    </div>
  )
}

export default App
