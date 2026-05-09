import { DEFAULT_MARKET_ANALYSIS } from "../analysisFallbacks";

function MarketAnalysis({ analysis }) {
  const a = analysis && typeof analysis === "object" ? analysis : {};
  const market_summary = a.market_summary || DEFAULT_MARKET_ANALYSIS.market_summary;
  const your_strength = a.your_strength || DEFAULT_MARKET_ANALYSIS.your_strength;
  const biggest_opportunity =
    a.biggest_opportunity || DEFAULT_MARKET_ANALYSIS.biggest_opportunity;
  const demand_trend = a.demand_trend || DEFAULT_MARKET_ANALYSIS.demand_trend;

  const trend = String(demand_trend || "").toLowerCase();
  const trendClass =
    trend === "growing"
      ? "trend-growing"
      : trend === "stable"
        ? "trend-stable"
        : "trend-declining";

  return (
    <div className="market-grid">
      <div className="market-card">
        <div className="market-label">Market Summary</div>
        <div className="market-value">{market_summary}</div>
      </div>
      <div className="market-card">
        <div className="market-label">Your Strength</div>
        <div className="market-value">{your_strength}</div>
      </div>
      <div className="market-card">
        <div className="market-label">Biggest Opportunity</div>
        <div className="market-value">{biggest_opportunity}</div>
      </div>
      <div className="market-card">
        <div className="market-label">Demand Trend</div>
        <div className={`market-value ${trendClass}`}>{demand_trend}</div>
      </div>
    </div>
  );
}

export default MarketAnalysis;
