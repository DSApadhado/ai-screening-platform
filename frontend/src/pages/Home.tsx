import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { createJob, listJobs } from '../services/api'
import { Briefcase, Plus } from 'lucide-react'

export default function Home() {
  const [jobs, setJobs] = useState<any[]>([])
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [creating, setCreating] = useState(false)
  const [showForm, setShowForm] = useState(false)
  const nav = useNavigate()

  useEffect(() => { listJobs().then(r => setJobs(r.data)) }, [])

  const handleCreate = async () => {
    if (!title || !description) return
    setCreating(true)
    try {
      const r = await createJob(title, description)
      nav(`/job/${r.data.id}`)
    } finally { setCreating(false) }
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-gray-800">Recruitment Jobs</h1>
        <button onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-2 bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700">
          <Plus size={20} /> New Job
        </button>
      </div>

      {showForm && (
        <div className="bg-white rounded-xl shadow-md p-6 mb-8">
          <h2 className="text-lg font-semibold mb-4">Create New Job</h2>
          <input className="w-full border rounded-lg px-4 py-2 mb-3" placeholder="Job Title"
            value={title} onChange={e => setTitle(e.target.value)} />
          <textarea className="w-full border rounded-lg px-4 py-2 mb-3 h-40" placeholder="Job Description (be detailed for better AI matching)"
            value={description} onChange={e => setDescription(e.target.value)} />
          <button onClick={handleCreate} disabled={creating}
            className="bg-indigo-600 text-white px-6 py-2 rounded-lg hover:bg-indigo-700 disabled:opacity-50">
            {creating ? 'Creating...' : 'Create Job'}
          </button>
        </div>
      )}

      <div className="grid gap-4">
        {jobs.map((j: any) => (
          <div key={j.id} onClick={() => nav(`/job/${j.id}`)}
            className="bg-white rounded-xl shadow-md p-6 cursor-pointer hover:shadow-lg transition-shadow">
            <div className="flex items-center gap-3">
              <Briefcase className="text-indigo-600" />
              <div>
                <h3 className="text-lg font-semibold">{j.title}</h3>
                <p className="text-sm text-gray-500">Created: {new Date(j.created_at).toLocaleDateString()}</p>
              </div>
            </div>
          </div>
        ))}
        {jobs.length === 0 && !showForm && (
          <p className="text-gray-500 text-center py-12">No jobs yet. Create one to get started.</p>
        )}
      </div>
    </div>
  )
}
