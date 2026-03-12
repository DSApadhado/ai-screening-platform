import { useState } from 'react'
import { Play, Zap } from 'lucide-react'

interface Props {
  jobId: number
  loading: string
  candidateCount: number
  onAction: (name: string, fn: () => Promise<any>) => void
  actions: {
    processResumes: () => Promise<any>
    analyzeGithub: () => Promise<any>
    evaluate: () => Promise<any>
    shortlist: (topN: number, minScore: number) => Promise<any>
    sendTests: (link: string) => Promise<any>
    scoreTests: (min: number) => Promise<any>
    scheduleInterviews: (topN: number, startDate?: string) => Promise<any>
    runFull: (topN: number, minScore: number) => Promise<any>
  }
}

export default function PipelineControls({ loading, candidateCount, onAction, actions }: Props) {
  const [topN, setTopN] = useState(5)
  const [minScore, setMinScore] = useState(50)
  const [testLink, setTestLink] = useState('https://example.com/assessment')
  const [minTestScore, setMinTestScore] = useState(60)
  const [interviewTopN, setInterviewTopN] = useState(5)

  const steps = [
    { key: 'process', label: '1. Process Resumes', fn: () => onAction('process', actions.processResumes) },
    { key: 'github', label: '2. Analyze GitHub', fn: () => onAction('github', actions.analyzeGithub) },
    { key: 'evaluate', label: '3. AI Evaluate', fn: () => onAction('evaluate', actions.evaluate) },
    { key: 'shortlist', label: '4. Shortlist', fn: () => onAction('shortlist', () => actions.shortlist(topN, minScore)) },
    { key: 'send-tests', label: '5. Send Tests', fn: () => onAction('send-tests', () => actions.sendTests(testLink)) },
    { key: 'score-tests', label: '6. Score Tests', fn: () => onAction('score-tests', () => actions.scoreTests(minTestScore)) },
    { key: 'schedule', label: '7. Schedule Interviews', fn: () => onAction('schedule', () => actions.scheduleInterviews(interviewTopN)) },
  ]

  if (candidateCount === 0) return null

  return (
    <div className="bg-white rounded-xl shadow-md p-6 mb-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-semibold">Pipeline Controls</h2>
        <button onClick={() => onAction('full', () => actions.runFull(topN, minScore))}
          disabled={!!loading}
          className="flex items-center gap-2 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 disabled:opacity-50">
          <Zap size={16} /> Run Full Pipeline
        </button>
      </div>

      {/* Config */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-4 text-sm">
        <div>
          <label className="text-gray-500">Top N</label>
          <input type="number" value={topN} onChange={e => setTopN(+e.target.value)}
            className="w-full border rounded px-2 py-1 mt-1" />
        </div>
        <div>
          <label className="text-gray-500">Min AI Score</label>
          <input type="number" value={minScore} onChange={e => setMinScore(+e.target.value)}
            className="w-full border rounded px-2 py-1 mt-1" />
        </div>
        <div>
          <label className="text-gray-500">Test Link</label>
          <input value={testLink} onChange={e => setTestLink(e.target.value)}
            className="w-full border rounded px-2 py-1 mt-1" />
        </div>
        <div>
          <label className="text-gray-500">Min Test Score</label>
          <input type="number" value={minTestScore} onChange={e => setMinTestScore(+e.target.value)}
            className="w-full border rounded px-2 py-1 mt-1" />
        </div>
        <div>
          <label className="text-gray-500">Interview Top N</label>
          <input type="number" value={interviewTopN} onChange={e => setInterviewTopN(+e.target.value)}
            className="w-full border rounded px-2 py-1 mt-1" />
        </div>
      </div>

      {/* Step Buttons */}
      <div className="flex flex-wrap gap-2">
        {steps.map(s => (
          <button key={s.key} onClick={s.fn} disabled={!!loading}
            className="flex items-center gap-1 bg-indigo-50 text-indigo-700 px-3 py-2 rounded-lg hover:bg-indigo-100 disabled:opacity-50 text-sm font-medium">
            {loading === s.key ? <RefreshIcon /> : <Play size={14} />} {s.label}
          </button>
        ))}
      </div>
    </div>
  )
}

function RefreshIcon() {
  return <svg className="animate-spin h-3.5 w-3.5" viewBox="0 0 24 24">
    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
  </svg>
}
