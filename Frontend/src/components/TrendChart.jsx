import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

function TrendChart({ trending }) {
  return (
    <div>
      <h3 className="card-title">
        Trending Skills <span>Current market demand</span>
      </h3>
      {(!trending || trending.length === 0) ? (
        <p>Loading trends...</p>
      ) : (
        <ResponsiveContainer width="100%" height={400}>
          <BarChart data={trending} layout="vertical">
            <XAxis type="number" />
            <YAxis type="category" dataKey="skill" width={170} />
            <Tooltip
              contentStyle={{
                borderRadius: "10px",
                border: "1px solid #E5E7EB",
                backgroundColor: "#FFFFFF",
                boxShadow: "0 4px 12px rgba(0,0,0,0.08)",
              }}
              cursor={{ fill: "rgba(99,102,241,0.08)" }}
            />
            <Bar dataKey="count" fill="#6366F1" radius={[0, 8, 8, 0]} />
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}

export default TrendChart;
