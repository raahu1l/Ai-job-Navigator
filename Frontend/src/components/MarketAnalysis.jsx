function MarketAnalysis({ analysis }) {
  if (!analysis) {
    return null;
  }

  const trend = String(analysis.demand_trend || "").toLowerCase();
  const trendClass = trend === "growing"
    ? "trend-growing"
    : trend === "stable"
      ? "trend-stable"
      : "trend-declining";

  return (
    <div className="market-grid">
      <div className="market-card">
        <div className="market-label">Market Summary</div>
        <div className="market-value">{analysis.market_summary}</div>
      </div>
      <div className="market-card">
        <div className="market-label">Your Strength</div>
        <div className="market-value">{analysis.your_strength}</div>
      </div>
      <div className="market-card">
        <div className="market-label">Biggest Opportunity</div>
        <div className="market-value">{analysis.biggest_opportunity}</div>
      </div>
      <div className="market-card">
        <div className="market-label">Demand Trend</div>
        <div className={`market-value ${trendClass}`}>{analysis.demand_trend}</div>
      </div>
    </div>
  );
}

export default MarketAnalysis;
