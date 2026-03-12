import { X } from 'lucide-react'

interface Props {
  candidate: any
  onClose: () => void
}

export default function CandidateDetail({ candidate: c, onClose }: Props) {
  const breakdown = c.score_breakdown || {}

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
        <div className="flex justify-between items-center p-6 border-b sticky top-0 bg-white rounded-t-2xl">
          <h2 className="text-xl font-bold">{c.name}</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600"><X /></button>
        </div>

        <div className="p-6 space-y-6">
          {/* Basic Info */}
          <Section title="Profile">
            <Info label="Email" value={c.email} />
            <Info label="College" value={c.college} />
            <Info label="Branch" value={c.branch} />
            <Info label="CGPA" value={c.cgpa?.toFixed(2)} />
            {c.github_url && <Info label="GitHub" value={<a href={c.github_url} target="_blank" rel="noreferrer" className="text-indigo-600 hover:underline">{c.github_url}</a>} />}
          </Section>

          {/* AI Project & Research */}
          {c.best_ai_project && (
            <Section title="Best AI Project">
              <p className="text-sm text-gray-700 whitespace-pre-wrap">{c.best_ai_project}</p>
            </Section>
          )}
          {c.research_work && (
            <Section title="Research Work">
              <p className="text-sm text-gray-700 whitespace-pre-wrap">{c.research_work}</p>
            </Section>
          )}

          {/* Scores */}
          {c.total_score > 0 && (
            <Section title="AI Evaluation Scores">
              <div className="grid grid-cols-2 gap-3">
                <ScoreItem label="Resume" score={c.resume_score} reason={breakdown.resume_reasoning} />
                <ScoreItem label="GitHub" score={c.github_score} reason={breakdown.github_reasoning} />
                <ScoreItem label="JD Match" score={c.jd_match_score} reason={breakdown.jd_match_reasoning} />
                <ScoreItem label="Project" score={c.project_score} reason={breakdown.project_reasoning} />
                <ScoreItem label="Research" score={c.research_score} reason={breakdown.research_reasoning} />
                <ScoreItem label="Overall AI" score={c.ai_score} />
              </div>
            </Section>
          )}

          {/* Test Scores */}
          {(c.test_la != null || c.test_code != null) && (
            <Section title="Test Scores">
              <div className="grid grid-cols-3 gap-3">
                <ScoreItem label="Logical Aptitude" score={c.test_la} />
                <ScoreItem label="Coding" score={c.test_code} />
                <ScoreItem label="Test Average" score={c.test_total} />
              </div>
            </Section>
          )}

          {/* Final Score */}
          {(c.final_score > 0 || c.total_score > 0) && (
            <Section title="Final Score">
              <div className="text-3xl font-bold text-indigo-600">{(c.final_score || c.total_score).toFixed(1)} / 100</div>
            </Section>
          )}

          {/* Summary */}
          {breakdown.overall_summary && (
            <Section title="AI Summary">
              <p className="text-sm text-gray-700">{breakdown.overall_summary}</p>
              {breakdown.weight_reasoning && (
                <p className="text-xs text-indigo-600 mt-2 italic">Ranking strategy: {breakdown.weight_reasoning}</p>
              )}
              {breakdown.strengths?.length > 0 && (
                <div className="mt-2">
                  <span className="text-xs font-semibold text-green-600">Strengths:</span>
                  <ul className="list-disc list-inside text-sm text-gray-600">
                    {breakdown.strengths.map((s: string, i: number) => <li key={i}>{s}</li>)}
                  </ul>
                </div>
              )}
              {breakdown.weaknesses?.length > 0 && (
                <div className="mt-2">
                  <span className="text-xs font-semibold text-red-600">Weaknesses:</span>
                  <ul className="list-disc list-inside text-sm text-gray-600">
                    {breakdown.weaknesses.map((w: string, i: number) => <li key={i}>{w}</li>)}
                  </ul>
                </div>
              )}
              {breakdown.recommendation && (
                <div className="mt-2">
                  <span className="text-xs font-semibold">Recommendation: </span>
                  <span className={`text-sm font-bold ${breakdown.recommendation === 'strong_yes' ? 'text-green-600' : breakdown.recommendation === 'yes' ? 'text-green-500' : breakdown.recommendation === 'maybe' ? 'text-yellow-600' : 'text-red-500'}`}>
                    {breakdown.recommendation.replace('_', ' ').toUpperCase()}
                  </span>
                </div>
              )}
            </Section>
          )}

          {/* Interview */}
          {c.interview_time && (
            <Section title="Interview">
              <Info label="Time" value={new Date(c.interview_time).toLocaleString()} />
              {c.meet_link && <Info label="Meet Link" value={<a href={c.meet_link} target="_blank" rel="noreferrer" className="text-indigo-600 hover:underline">{c.meet_link}</a>} />}
            </Section>
          )}
        </div>
      </div>
    </div>
  )
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-2">{title}</h3>
      {children}
    </div>
  )
}

function Info({ label, value }: { label: string; value: any }) {
  return (
    <div className="flex gap-2 text-sm py-0.5">
      <span className="text-gray-500 min-w-[80px]">{label}:</span>
      <span className="text-gray-800">{value || '—'}</span>
    </div>
  )
}

function ScoreItem({ label, score, reason }: { label: string; score?: number; reason?: string }) {
  if (score == null) return null
  const color = score >= 70 ? 'text-green-600' : score >= 50 ? 'text-yellow-600' : 'text-red-600'
  return (
    <div className="bg-gray-50 rounded-lg p-3">
      <div className="flex justify-between items-center">
        <span className="text-xs text-gray-500">{label}</span>
        <span className={`font-bold ${color}`}>{score}</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-1.5 mt-1">
        <div className={`h-1.5 rounded-full ${score >= 70 ? 'bg-green-500' : score >= 50 ? 'bg-yellow-500' : 'bg-red-500'}`}
          style={{ width: `${Math.min(score, 100)}%` }} />
      </div>
      {reason && <p className="text-xs text-gray-500 mt-1">{reason}</p>}
    </div>
  )
}
