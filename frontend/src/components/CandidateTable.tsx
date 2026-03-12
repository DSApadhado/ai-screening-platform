const STATUS_COLORS: Record<string, string> = {
  uploaded: 'bg-gray-100 text-gray-700',
  evaluated: 'bg-blue-100 text-blue-700',
  shortlisted: 'bg-green-100 text-green-700',
  test_sent: 'bg-yellow-100 text-yellow-700',
  test_scored: 'bg-purple-100 text-purple-700',
  interview_scheduled: 'bg-emerald-100 text-emerald-700',
  rejected: 'bg-red-100 text-red-700',
}

interface Props {
  candidates: any[]
  onSelect: (c: any) => void
}

export default function CandidateTable({ candidates, onSelect }: Props) {
  if (!candidates.length) return <p className="text-gray-500 text-center py-8">No candidates yet. Upload a CSV to begin.</p>

  return (
    <div className="bg-white rounded-xl shadow-md overflow-hidden">
      <div className="px-6 py-4 border-b">
        <h2 className="text-lg font-semibold">Candidates ({candidates.length})</h2>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50">
            <tr>
              {['#', 'Name', 'College', 'Branch', 'CGPA', 'AI Score', 'Test', 'Final', 'Status', ''].map(h => (
                <th key={h} className="px-4 py-3 text-left font-medium text-gray-500">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {candidates.map((c: any) => (
              <tr key={c.id} className="border-t hover:bg-gray-50 cursor-pointer" onClick={() => onSelect(c)}>
                <td className="px-4 py-3">{c.s_no}</td>
                <td className="px-4 py-3 font-medium">{c.name}</td>
                <td className="px-4 py-3 text-gray-600 max-w-[150px] truncate">{c.college}</td>
                <td className="px-4 py-3 text-gray-600 max-w-[120px] truncate">{c.branch}</td>
                <td className="px-4 py-3">{c.cgpa?.toFixed(2)}</td>
                <td className="px-4 py-3">
                  {c.total_score > 0 && <ScoreBar score={c.total_score} />}
                </td>
                <td className="px-4 py-3">
                  {c.test_total != null && <span>{c.test_total.toFixed(0)}</span>}
                </td>
                <td className="px-4 py-3 font-semibold">
                  {c.final_score > 0 ? c.final_score.toFixed(1) : c.total_score > 0 ? c.total_score.toFixed(1) : '—'}
                </td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${STATUS_COLORS[c.status] || 'bg-gray-100'}`}>
                    {c.status?.replace('_', ' ')}
                  </span>
                </td>
                <td className="px-4 py-3">
                  {c.meet_link && <a href={c.meet_link} target="_blank" rel="noreferrer"
                    className="text-indigo-600 hover:underline text-xs" onClick={e => e.stopPropagation()}>Meet</a>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function ScoreBar({ score }: { score: number }) {
  const color = score >= 70 ? 'bg-green-500' : score >= 50 ? 'bg-yellow-500' : 'bg-red-500'
  return (
    <div className="flex items-center gap-2">
      <div className="w-16 bg-gray-200 rounded-full h-2">
        <div className={`h-2 rounded-full ${color}`} style={{ width: `${Math.min(score, 100)}%` }} />
      </div>
      <span className="text-xs">{score.toFixed(0)}</span>
    </div>
  )
}
