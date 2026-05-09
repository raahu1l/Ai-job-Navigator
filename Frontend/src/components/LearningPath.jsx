import { normalizeLearningPath } from "../analysisFallbacks";

const MAX_RESOURCE_CHIPS = 3;
const MAX_YT = 3;

function firstLine(text, maxLen = 140) {
  if (typeof text !== "string" || !text.trim()) {
    return "";
  }
  const line = text.trim().split(/\n/)[0].trim();
  if (line.length <= maxLen) {
    return line;
  }
  return `${line.slice(0, maxLen - 1)}…`;
}

function websiteHref(url) {
  const u = typeof url === "string" ? url.trim() : "";
  if (!u) {
    return "";
  }
  if (/^https?:\/\//i.test(u)) {
    return u;
  }
  return `https://${u}`;
}

function mergeUniqueChips(tools, resources, max) {
  const merged = [];
  const seen = new Set();
  const add = (arr) => {
    for (const x of arr || []) {
      const k = typeof x === "string" ? x.trim() : "";
      if (!k) {
        continue;
      }
      const low = k.toLowerCase();
      if (seen.has(low)) {
        continue;
      }
      seen.add(low);
      merged.push(k);
      if (merged.length >= max) {
        return;
      }
    }
  };
  add(tools);
  add(resources);
  return merged;
}

function LearningPath({
  targetRoleLabel,
  learningPath,
  loading,
  errorMessage,
}) {
  if (loading && !learningPath) {
    return (
      <div className="lp-card lp-card--loading" role="status">
        <div className="lp-loading-text">Generating roadmap…</div>
        {targetRoleLabel && (
          <p className="lp-target-line">{targetRoleLabel}</p>
        )}
      </div>
    );
  }

  if (errorMessage) {
    return (
      <div className="lp-card lp-card--error" role="alert">
        <p className="lp-eyebrow">Learning roadmap</p>
        {targetRoleLabel && (
          <p className="lp-target-line lp-target-line--error">{targetRoleLabel}</p>
        )}
        <p className="lp-error-text">{errorMessage}</p>
      </div>
    );
  }

  if (!learningPath) {
    return null;
  }

  const data = normalizeLearningPath(learningPath);
  const gaps = data.missing_skills_for_role || [];
  const steps = data.roadmap_steps?.length ? data.roadmap_steps : data.steps;

  return (
    <div className="lp-card lp-card--compact-roadmap">
      <p className="lp-eyebrow">Learning roadmap</p>
      {targetRoleLabel && <p className="lp-target-line">{targetRoleLabel}</p>}

      {gaps.length > 0 && (
        <div className="lp-missing-block lp-missing-block--tight">
          <h3 className="lp-subheading">Skills to close</h3>
          <ul className="lp-missing-chips" aria-label="Missing skills">
            {gaps.map((s) => (
              <li key={s}>
                <span className="lp-missing-chip">{s}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="lp-header lp-header--tight">
        <div className="lp-header-main">
          <h2 className="lp-title lp-title--sm">Start here</h2>
          <p className="lp-priority-name">
            {data.priority_skill || gaps[0] || "Prioritize one gap"}
          </p>
        </div>
        {data.estimated_time && (
          <div className="lp-time lp-time--pill" aria-label="Estimated time overall">
            {data.estimated_time}
          </div>
        )}
      </div>

      {data.message && (
        <div className="lp-message lp-message--muted lp-message--clamp">{data.message}</div>
      )}

      {steps.length > 0 ? (
        <ol className="lp-roadmap-steps lp-roadmap-steps--tight">
          {steps.map((step, index) => {
            const why = firstLine(step.why_it_matters, 160);
            const resChips = mergeUniqueChips(
              step.tools_and_apps,
              step.resources,
              MAX_RESOURCE_CHIPS,
            );
            const ytChips = (step.youtube_channels || [])
              .filter((x) => typeof x === "string" && x.trim())
              .slice(0, MAX_YT);
            const webSites = Array.isArray(step.best_websites) ? step.best_websites : [];
            const projectLine = firstLine(step.practice_project, 220);

            return (
              <li className="lp-roadmap-step-card lp-roadmap-step-card--dense" key={`${step.skill}-${index}`}>
                <header className="lp-roadstep-head lp-roadstep-head--dense">
                  <span className="lp-roadstep-num">{index + 1}</span>
                  <div className="lp-roadstep-title-wrap">
                    <h4 className="lp-roadstep-skill">{step.skill}</h4>
                    {step.estimated_time && (
                      <span className="lp-roadstep-time lp-roadstep-time--pill">{step.estimated_time}</span>
                    )}
                  </div>
                </header>
                {why && (
                  <section className="lp-roadstep-section lp-roadstep-section--tight">
                    <span className="lp-snippet-label">Why it matters</span>
                    <p className="lp-snippet-body lp-snippet-body--single-line">{why}</p>
                  </section>
                )}
                {resChips.length > 0 && (
                  <section className="lp-roadstep-section lp-roadstep-section--tight">
                    <span className="lp-snippet-label">Tools & resources</span>
                    <div className="lp-chip-row">
                      {resChips.map((label) => (
                        <span key={label} className="lp-chip">
                          {label}
                        </span>
                      ))}
                    </div>
                  </section>
                )}
                {ytChips.length > 0 && (
                  <section className="lp-roadstep-section lp-roadstep-section--tight">
                    <span className="lp-snippet-label">YouTube</span>
                    <div className="lp-chip-row">
                      {ytChips.map((label) => (
                        <span key={label} className="lp-chip lp-chip--yt">
                          {label}
                        </span>
                      ))}
                    </div>
                  </section>
                )}
                {webSites.length > 0 && (
                  <section className="lp-roadstep-section lp-roadstep-section--tight">
                    <span className="lp-snippet-label">Best websites</span>
                    <ul className="lp-website-list">
                      {webSites.map((w) => {
                        const href = websiteHref(w.url);
                        return (
                          <li key={`${w.name}-${href}`}>
                            <a
                              className="lp-website-link"
                              href={href}
                              target="_blank"
                              rel="noopener noreferrer"
                            >
                              {w.name}
                            </a>
                          </li>
                        );
                      })}
                    </ul>
                  </section>
                )}
                {!resChips.length && step.resource && (
                  <p className="lp-step-resource">{step.resource}</p>
                )}
                {projectLine && (
                  <section className="lp-roadstep-project lp-roadstep-project--compact">
                    <span className="lp-snippet-label">Practice project</span>
                    <p className="lp-snippet-body lp-snippet-body--project">{projectLine}</p>
                  </section>
                )}
                {step.platform && (
                  <p className="lp-step-platform lp-step-platform--muted">
                    <span className="lp-step-platform-label">Extra</span> {step.platform}
                  </p>
                )}
              </li>
            );
          })}
        </ol>
      ) : (
        gaps.length > 0 && (
          <p className="lp-steps-empty">
            Detailed roadmap steps missing — retry generation.
          </p>
        )
      )}
    </div>
  );
}

export default LearningPath;
