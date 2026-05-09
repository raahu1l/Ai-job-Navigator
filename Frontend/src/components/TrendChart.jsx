import { useId, useMemo } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ResponsiveContainer,
  Cell,
} from "recharts";

const AXIS_MUTED = "#94A3B8";
const GRID_STROKE = "#E2E8F0";

function TrendChart({ trending, usingFallback = false }) {
  const uid = useId();
  const gradientId = `trendBarGrad-${uid.replace(/:/g, "")}`;

  const data = Array.isArray(trending) && trending.length > 0 ? trending : [];

  const chartData = useMemo(
    () =>
      data.map((d, i) => ({
        ...d,
        chartKey: `${String(d.skill ?? "skill")}-${i}`,
        count: typeof d.count === "number" ? d.count : Number(d.count) || 0,
      })),
    [data],
  );

  const maxCount = useMemo(() => {
    if (!chartData.length) {
      return 0;
    }
    return Math.max(...chartData.map((d) => d.count), 1);
  }, [chartData]);

  const formatYLabel = (value) => {
    const s = String(value ?? "");
    if (s.length <= 26) {
      return s;
    }
    return `${s.slice(0, 24)}…`;
  };

  const leftMargin = 118;

  return (
    <div className="trend-chart-root">
      <h3 className="card-title card-title--compact">
        Trending skills
        {!usingFallback && <span>(live mentions)</span>}
      </h3>
      {usingFallback && (
        <p className="chart-fallback-note">Sample demand mix until live data loads.</p>
      )}
      {chartData.length === 0 ? (
        <p className="chart-empty">Preparing market demand chart…</p>
      ) : (
        <div className="chart-wrap">
          <ResponsiveContainer width="100%" height="100%" minHeight={280}>
            <BarChart
              data={chartData}
              layout="vertical"
              margin={{ left: leftMargin, right: 18, top: 14, bottom: 10 }}
              barCategoryGap="18%"
            >
              <defs>
                <linearGradient id={gradientId} x1="0" y1="0" x2="1" y2="0">
                  <stop offset="0%" stopColor="#6366F1" stopOpacity={0.95} />
                  <stop offset="55%" stopColor="#7C3AED" stopOpacity={0.88} />
                  <stop offset="100%" stopColor="#8B5CF6" stopOpacity={0.72} />
                </linearGradient>
              </defs>
              <CartesianGrid
                strokeDasharray="3 4"
                horizontal={false}
                stroke={GRID_STROKE}
              />
              <XAxis
                type="number"
                domain={[0, Math.ceil(maxCount * 1.08)]}
                tick={{ fontSize: 11, fill: AXIS_MUTED, fontWeight: 500 }}
                tickLine={{ stroke: GRID_STROKE }}
                axisLine={{ stroke: GRID_STROKE }}
                tickMargin={10}
              />
              <YAxis
                type="category"
                dataKey="skill"
                width={leftMargin - 12}
                interval={0}
                tick={{
                  fontSize: 11,
                  fill: "#475569",
                  fontWeight: 600,
                }}
                tickMargin={10}
                tickLine={false}
                axisLine={{ stroke: GRID_STROKE }}
                tickFormatter={formatYLabel}
              />
              <Tooltip
                cursor={{ fill: "rgba(99, 102, 241, 0.075)" }}
                formatter={(value, _name, item) => [value, `${item.payload.skill}`]}
                labelFormatter={() => ""}
                contentStyle={{
                  borderRadius: "10px",
                  border: "1px solid #E5E7EB",
                  backgroundColor: "#FFFFFF",
                  boxShadow: "0 4px 20px rgba(15,23,42,0.1)",
                  fontSize: "0.8125rem",
                }}
                itemStyle={{ fontWeight: 700, color: "#1e293b" }}
                labelStyle={{ display: "none" }}
              />
              <Bar
                dataKey="count"
                name="mentions"
                radius={[0, 7, 7, 0]}
                animationDuration={600}
              >
                {chartData.map((entry) => (
                  <Cell key={entry.chartKey} fill={`url(#${gradientId})`} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}

export default TrendChart;
