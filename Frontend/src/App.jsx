import { useEffect, useState } from 'react'

function App() {
  const [healthResponse, setHealthResponse] = useState(null)

  useEffect(() => {
    fetch('http://localhost:5000/api/health')
      .then((response) => response.json())
      .then((data) => setHealthResponse(data))
  }, [])

  return (
    <div>{JSON.stringify(healthResponse)}</div>
  )
}

export default App
