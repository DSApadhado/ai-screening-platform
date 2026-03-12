import { useState, useEffect, useCallback } from 'react'
import { useParams } from 'react-router-dom'
import {
  getJob, uploadCandidates, uploadResumes, uploadTestResults,
  processResumes, analyzeGithub, evaluateCandidates,
  shortlistCandidates, sendTestLinks, scoreTests, scheduleInterviews, runFullPipeline,
} from '../services/api'
import CandidateTable from '../components/CandidateTable'
import CandidateDetail from '../components/CandidateDetail'
import PipelineControls from '../components/PipelineControls'
import ScoreChart from '../components/ScoreChart'
import { Upload, Play, RefreshCw } from 'lucide-react'

export default function JobDashboard() {
  const { jobId } = useParams<{ jobId: string }>()
  const id = Number(jobId)
  const [job, setJob] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState('')
  const [selectedCandidate, setSelectedCandidate] = useState<any>(null)
  const [message, setMessage] = useState('')

  const refresh = useCallback(async () => {
    setLoading(true)
    try {
      const r = await getJob(id)
      setJob(r.data)
    } finally { setLoading(false) }
  }, [id])

  useEffect(() => { refresh() }, [refresh])

  const showMsg = (msg: string) => { setMessage(msg); setTimeout(() => setMessage(''), 4000) }

  const handleAction = async (action: string, fn: () => Promise<any>) => {
    setActionLoading(action)
    try {
      const r = await fn()
      showMsg(r.data.message || r.data.steps?.map((s: any) => s.message).join(' → ') || 'Done')
      await refresh()
    } catch (e: any) {
      showMsg(`Error: ${e.response?.data?.detail || e.message}`)
    } finally { setActionLoading('') }
  }

  const handleFileUpload = async (type: 'candidates' | 'resumes' | 'tests', files: FileList) => {
    if (type === 'candidates') {
      await handleAction('upload', () => uploadCandidates(id, files[0]))
    } else if (type === 'resumes') {
      await handleAction('upload-resumes', () => uploadResumes(id, Array.from(files)))
    } else {
      await handleAction('upload-tests', () => uploadTestResults(id, files[0]))
    }
  }

  if (loading && !job) return <div className="text-center py-12">Loading...</div>
  if (!job) return <div className="text-center py-12 text-red-500">Job not found</div>

  return (
    <div>
      {message && (
        <div className="fixed top-4 right-4 bg-indigo-600 text-white px-6 py-3 rounded-lg shadow-lg z-50 animate-pulse">
          {message}
        </div>
      )}

      <div className="flex justify-between items-start mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">{job.title}</h1>
          <p className="text-gray-500 mt-1 max-w-2xl line-clamp-2">{job.description}</p>
        </div>
        <button onClick={refresh} className="text-gray-500 hover:text-indigo-600">
          <RefreshCw size={20} />
        </button>
      </div>

      {/* Upload Section */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <UploadCard label="Upload Candidates (CSV/XLSX)" accept=".csv,.xlsx,.xls"
          onUpload={files => handleFileUpload('candidates', files)} loading={actionLoading === 'upload'} />
        <UploadCard label="Upload Resumes (PDFs)" accept=".pdf" multiple
          onUpload={files => handleFileUpload('resumes', files)} loading={actionLoading === 'upload-resumes'} />
        <UploadCard label="Upload Test Results (CSV/XLSX)" accept=".csv,.xlsx,.xls"
          onUpload={files => handleFileUpload('tests', files)} loading={actionLoading === 'upload-tests'} />
      </div>

      {/* Pipeline Controls */}
      <PipelineControls
        jobId={id}
        loading={actionLoading}
        candidateCount={job.candidates?.length || 0}
        onAction={handleAction}
        actions={{
          processResumes: () => processResumes(id),
          analyzeGithub: () => analyzeGithub(id),
          evaluate: () => evaluateCandidates(id),
          shortlist: (topN: number, minScore: number) => shortlistCandidates(id, topN, minScore),
          sendTests: (link: string) => sendTestLinks(id, link),
          scoreTests: (min: number) => scoreTests(id, min),
          scheduleInterviews: (topN: number, startDate?: string) => scheduleInterviews(id, topN, startDate),
          runFull: (topN: number, minScore: number) => runFullPipeline(id, topN, minScore),
        }}
      />

      {/* Score Chart */}
      {job.candidates?.some((c: any) => c.total_score > 0) && (
        <ScoreChart candidates={job.candidates} />
      )}

      {/* Candidate Table */}
      <CandidateTable candidates={job.candidates || []} onSelect={setSelectedCandidate} />

      {/* Candidate Detail Modal */}
      {selectedCandidate && (
        <CandidateDetail candidate={selectedCandidate} onClose={() => setSelectedCandidate(null)} />
      )}
    </div>
  )
}

function UploadCard({ label, accept, multiple, onUpload, loading }: {
  label: string; accept: string; multiple?: boolean; loading: boolean;
  onUpload: (files: FileList) => void;
}) {
  return (
    <label className="bg-white rounded-xl shadow-md p-4 cursor-pointer hover:shadow-lg transition-shadow border-2 border-dashed border-gray-200 hover:border-indigo-400 flex flex-col items-center justify-center gap-2 min-h-[100px]">
      <Upload className={loading ? 'animate-spin text-indigo-600' : 'text-gray-400'} size={24} />
      <span className="text-sm text-gray-600 text-center">{loading ? 'Uploading...' : label}</span>
      <input type="file" accept={accept} multiple={multiple} className="hidden"
        onChange={e => e.target.files && onUpload(e.target.files)} disabled={loading} />
    </label>
  )
}
