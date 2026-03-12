import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts'

interface Props {
  candidates: any[]
}

export default function ScoreChart({ candidates }: Props) {
  const scored = candidates.filter((c: any) => c.total_score > 0)
    .sort((a: any, b: any) => b.total_score - a.total_score)

  const barData = scored.map((c: any) => ({
    name: c.name,
    'AI Score': c.total_score?.toFixed(1),
    'Resume': c.resume_score,
    'GitHub': c.github_score,
    'JD Match': c.jd_match_score,
    'Test': c.test_total || 0,
  }))

  return (
    <div className="bg-white rounded-xl shadow-md p-6 mb-6">
      <h2 className="text-lg font-semibold mb-4">Candidate Scores</h2>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={barData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" tick={{ fontSize: 12 }} />
          <YAxis domain={[0, 100]} />
          <Tooltip />
          <Legend />
          <Bar dataKey="Resume" fill="#6366f1" />
          <Bar dataKey="GitHub" fill="#22c55e" />
          <Bar dataKey="JD Match" fill="#f59e0b" />
          <Bar dataKey="Test" fill="#ef4444" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
