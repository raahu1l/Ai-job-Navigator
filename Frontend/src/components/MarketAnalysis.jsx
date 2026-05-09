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
    <section className="market-insight-card" aria-label="Market insight">
      <h3 className="market-insight-title">Market insight</h3>
      <p className="market-insight-summary">{market_summary}</p>
      <dl className="market-insight-dl">
        <div className="market-insight-row">
          <dt>Your edge</dt>
          <dd>{your_strength}</dd>
        </div>
        <div className="market-insight-row">
          <dt>Top opportunity</dt>
          <dd>{biggest_opportunity}</dd>
        </div>
        <div className="market-insight-row">
          <dt>Demand</dt>
          <dd>
            <span className={trendClass}>{demand_trend}</span>
          </dd>
        </div>
      </dl>
    </section>
  );
}

export default MarketAnalysis;
