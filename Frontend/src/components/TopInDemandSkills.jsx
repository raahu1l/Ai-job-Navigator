import { useState } from "react";

function formatPct(p) {
  const n = Number(p);
  if (!Number.isFinite(n)) {
    return "—";
  }
  const t = Math.round(n * 10) / 10;
  return `${t}%`;
}

export default function TopInDemandSkills({ snapshot }) {
  const [open, setOpen] = useState(false);

  if (!snapshot) {
    return null;
  }

  const total = snapshot.total_jobs_analyzed ?? 0;
  const top = Array.isArray(snapshot.top_skills) ? snapshot.top_skills : [];
  const contextLine =
    typeof snapshot.market_context_line === "string" && snapshot.market_context_line.trim()
      ? snapshot.market_context_line.trim()
      : "";
  const insight = typeof snapshot.insight_line === "string" ? snapshot.insight_line : "";

  return (
    <section className="demand-snapshot" aria-labelledby="demand-snapshot-title">
      <button
        type="button"
        className="demand-snapshot__toggle"
        aria-expanded={open}
        id="demand-snapshot-title"
        onClick={() => setOpen((v) => !v)}
      >
        <span className="demand-snapshot__toggle-text">
          <span className="demand-snapshot__toggle-main">Top in-demand skills</span>
          {contextLine ? (
            <span className="demand-snapshot__context">{contextLine}</span>
          ) : null}
          <span className="demand-snapshot__meta">
            {total > 0 ? (
              <>
                {top.length > 0 ? `${top.length} skills · ` : ""}
                grounded in live Adzuna job text
              </>
            ) : (
              "Run a live search to populate skill demand"
            )}
          </span>
        </span>
        <span className="demand-snapshot__chev" aria-hidden>
          {open ? "▾" : "▸"}
        </span>
      </button>

      {open && (
        <div className="demand-snapshot__body">
          {snapshot.unavailable && (
            <p className="demand-snapshot__muted">
              Demand snapshot could not be loaded. Refresh after redeploy, or check network.
            </p>
          )}
          {insight && !snapshot.unavailable && (
            <p className="demand-snapshot__insight">{insight}</p>
          )}
          {top.length > 0 ? (
            <ul className="demand-snapshot__list">
              {top.map((row) => (
                <li key={row.skill} className="demand-snapshot__row">
                  <span className="demand-snapshot__skill">{row.skill}</span>
                  <span className="demand-snapshot__freq">
                    {row.jobs_with_skill} · {formatPct(row.pct_of_jobs)}
                  </span>
                </li>
              ))}
            </ul>
          ) : (
            !snapshot.unavailable && (
              <p className="demand-snapshot__muted">
                No repeated whitelist skills surfaced from these postings—try broader role keywords.
              </p>
            )
          )}
        </div>
      )}
    </section>
  );
}
