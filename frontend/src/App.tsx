import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Home from './pages/Home'
import JobDashboard from './pages/JobDashboard'

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-50">
        <nav className="bg-indigo-600 text-white px-6 py-4 shadow-lg">
          <a href="/" className="text-xl font-bold">🤖 AI Screening Platform</a>
        </nav>
        <main className="max-w-7xl mx-auto px-4 py-8">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/job/:jobId" element={<JobDashboard />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
