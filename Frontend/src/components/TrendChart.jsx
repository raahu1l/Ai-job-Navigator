import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

function TrendChart({ trending }) {
  if (!trending || trending.length === 0) {
    return <p>Loading trends...</p>;
  }

  return (
    <ResponsiveContainer width="100%" height={400}>
      <BarChart data={trending} layout="vertical">
        <XAxis type="number" />
        <YAxis type="category" dataKey="skill" />
        <Tooltip />
        <Bar dataKey="count" />
      </BarChart>
    </ResponsiveContainer>
  );
}

export default TrendChart;
