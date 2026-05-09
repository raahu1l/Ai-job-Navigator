import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

function TrendChart({ trending, usingFallback = false }) {
  const data = Array.isArray(trending) && trending.length > 0 ? trending : [];

  return (
    <div className="trend-chart-root">
      <h3 className="card-title card-title--compact">Trending skills</h3>
      {usingFallback && (
        <p className="chart-fallback-note">Sample demand mix until live data loads.</p>
      )}
      {data.length === 0 ? (
        <p className="chart-empty">Preparing market demand chart…</p>
      ) : (
        <div className="chart-wrap">
          <ResponsiveContainer width="100%" height="100%" minHeight={280}>
            <BarChart data={data} layout="vertical" margin={{ left: 8, right: 16, top: 8, bottom: 8 }}>
            <XAxis type="number" tick={{ fontSize: 12 }} />
            <YAxis type="category" dataKey="skill" width={120} tick={{ fontSize: 11 }} />
            <Tooltip
              contentStyle={{
                borderRadius: "10px",
                border: "1px solid #E5E7EB",
                backgroundColor: "#FFFFFF",
                boxShadow: "0 2px 8px rgba(15,23,42,0.08)",
              }}
              cursor={{ fill: "rgba(99,102,241,0.08)" }}
            />
            <Bar dataKey="count" fill="#6366F1" radius={[0, 6, 6, 0]} />
          </BarChart>
        </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}

export default TrendChart;
