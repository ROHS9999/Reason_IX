import { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";

import { apiFetch } from "../config";

/* ── Typing animation ─────────────────────────────────────────────── */
function TypeWriter({ text, speed = 18 }) {
  const [displayed, setDisplayed] = useState("");
  const [done, setDone] = useState(false);
  useEffect(() => {
    setDisplayed(""); setDone(false);
    let i = 0;
    const id = setInterval(() => {
      i++;
      setDisplayed(text.slice(0, i));
      if (i >= text.length) { clearInterval(id); setDone(true); }
    }, speed);
    return () => clearInterval(id);
  }, [text]);
  return (
    <span>
      {displayed}
      {!done && <span style={{ animation: "blink 0.7s step-end infinite", borderRight: "2px solid #E85D04", marginLeft: 1 }}>&nbsp;</span>}
    </span>
  );
}

/* ── Animated result card ─────────────────────────────────────────── */
function ResultCard({ title, accentColor, bgColor, icon, items, delay = 0 }) {
  const [vis, setVis] = useState(false);
  useEffect(() => {
    const timer = setTimeout(() => setVis(true), delay);
    return () => clearTimeout(timer);
  }, [delay]);
  if (!items?.length) return null;
  return (
    <div style={{
      background: bgColor, borderRadius: 20,
      borderLeft: `5px solid ${accentColor}`,
      padding: "28px 28px 24px",
      opacity: vis ? 1 : 0,
      transform: vis ? "translateY(0) scale(1)" : "translateY(28px) scale(0.96)",
      transition: "all 0.6s cubic-bezier(0.34,1.2,0.64,1)",
      position: "relative", overflow: "hidden",
    }}>
      <div style={{ position: "absolute", right: 16, top: 8, fontSize: 64, opacity: 0.06, pointerEvents: "none", lineHeight: 1 }}>{icon}</div>
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 20 }}>
        <span style={{ fontSize: 20 }}>{icon}</span>
        <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.14em", textTransform: "uppercase", color: accentColor, fontFamily: "'DM Sans',sans-serif" }}>{title}</span>
      </div>
      <ul style={{ listStyle: "none", display: "flex", flexDirection: "column", gap: 14 }}>
        {items.map((item, i) => (
          <li key={i} style={{
            display: "flex", gap: 12, alignItems: "flex-start",
            opacity: 0, transform: "translateX(-12px)",
            animation: `slideRight 0.5s ${delay / 1000 + 0.12 * i + 0.2}s ease both`,
          }}>
            <span style={{ width: 6, height: 6, borderRadius: "50%", background: accentColor, marginTop: 7, flexShrink: 0 }} />
            <span style={{ fontSize: 14, lineHeight: 1.75, color: "#333", fontFamily: "'DM Sans',sans-serif", fontWeight: 300 }}>
              <TypeWriter text={item} speed={12} />
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}

/* ── Contradiction Meter ──────────────────────────────────────────── */
function ContradictionMeter({ stats, conflicts, delay = 0 }) {
  const [vis, setVis] = useState(false);
  const [animated, setAnimated] = useState(false);
  useEffect(() => {
    const t1 = setTimeout(() => setVis(true), delay);
    const t2 = setTimeout(() => setAnimated(true), delay + 200);
    return () => { clearTimeout(t1); clearTimeout(t2); };
  }, [delay]);

  // Real numbers from the pair checker: contradictions vs agreements among the claim pairs that were judged.
  const nC = stats?.contradictions || 0;
  const nA = stats?.agreements || 0;
  const total = nC + nA;
  const contradictionScore = total === 0 ? 0 : Math.round((nC / total) * 100);
  const agreementScore = total === 0 ? 0 : 100 - contradictionScore;

  const getLevel = (score) => {
    if (score >= 70) return { label: "High Contradiction", color: "#E85D04", emoji: "🔥" };
    if (score >= 40) return { label: "Moderate Tension", color: "#f59e0b", emoji: "⚡" };
    return { label: "Mostly Aligned", color: "#2D6A4F", emoji: "✅" };
  };
  const level = getLevel(contradictionScore);

  return (
    <div style={{
      background: "#fff", borderRadius: 20,
      borderLeft: "5px solid #E85D04",
      padding: "28px 28px 24px",
      opacity: vis ? 1 : 0,
      transform: vis ? "translateY(0) scale(1)" : "translateY(28px) scale(0.96)",
      transition: "all 0.6s cubic-bezier(0.34,1.2,0.64,1)",
      position: "relative", overflow: "hidden",
    }}>
      <div style={{ position: "absolute", right: 16, top: 8, fontSize: 64, opacity: 0.04, pointerEvents: "none", lineHeight: 1 }}>📊</div>

      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 24 }}>
        <span style={{ fontSize: 20 }}>📊</span>
        <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.14em", textTransform: "uppercase", color: "#E85D04", fontFamily: "'DM Sans',sans-serif" }}>
          Contradiction Intensity
        </span>
      </div>

      <div style={{ display: "flex", alignItems: "flex-end", gap: 16, marginBottom: 24 }}>
        <div style={{ display: "flex", flexDirection: "column" }}>
          <span style={{ fontSize: 56, fontWeight: 800, color: level.color, fontFamily: "'Syne',sans-serif", lineHeight: 1 }}>
            {animated ? contradictionScore : 0}%
          </span>
          <span style={{ fontSize: 13, color: "#888", fontFamily: "'DM Sans',sans-serif", marginTop: 4 }}>
            {level.emoji} {level.label}
          </span>
        </div>
        <div style={{ marginLeft: "auto" }}>
          <svg width="90" height="90" viewBox="0 0 90 90">
            <circle cx="45" cy="45" r="38" fill="none" stroke="#f0ebe3" strokeWidth="8" />
            <circle cx="45" cy="45" r="38" fill="none"
              stroke={level.color} strokeWidth="8"
              strokeDasharray={`${animated ? (contradictionScore / 100) * 239 : 0} 239`}
              strokeLinecap="round"
              transform="rotate(-90 45 45)"
              style={{ transition: "stroke-dasharray 1.2s cubic-bezier(0.34,1.2,0.64,1)" }}
            />
            <text x="45" y="50" textAnchor="middle" fontSize="16" fontWeight="800"
              fill={level.color} fontFamily="'Syne',sans-serif">{animated ? contradictionScore : 0}%</text>
          </svg>
        </div>
      </div>

      <div style={{ marginBottom: 20 }}>
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
          <span style={{ fontSize: 11, color: "#2D6A4F", fontWeight: 700, fontFamily: "'DM Sans',sans-serif", letterSpacing: "0.08em", textTransform: "uppercase" }}>
            ✅ Agreement {agreementScore}%
          </span>
          <span style={{ fontSize: 11, color: "#E85D04", fontWeight: 700, fontFamily: "'DM Sans',sans-serif", letterSpacing: "0.08em", textTransform: "uppercase" }}>
            ⚡ Contradiction {contradictionScore}%
          </span>
        </div>
        <div style={{ height: 12, borderRadius: 99, background: "#f0ebe3", overflow: "hidden", position: "relative" }}>
          <div style={{
            position: "absolute", left: 0, top: 0, bottom: 0,
            width: animated ? `${agreementScore}%` : "0%",
            background: "linear-gradient(90deg, #2D6A4F, #52b788)",
            borderRadius: 99, transition: "width 1.2s cubic-bezier(0.34,1.2,0.64,1)",
          }} />
          <div style={{
            position: "absolute", right: 0, top: 0, bottom: 0,
            width: animated ? `${contradictionScore}%` : "0%",
            background: "linear-gradient(90deg, #f59e0b, #E85D04)",
            borderRadius: 99, transition: "width 1.2s cubic-bezier(0.34,1.2,0.64,1)",
          }} />
        </div>
        <p style={{ fontSize: 11, color: "#aaa", fontFamily: "'DM Sans',sans-serif", marginTop: 10 }}>
          {stats?.pairs_checked || 0} claim pairs judged · {nC} contradictions · {nA} agreements · {stats?.neutral || 0} neutral
        </p>
      </div>

      {conflicts?.length > 0 && (
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          <span style={{ fontSize: 10, letterSpacing: "0.12em", fontWeight: 700, color: "#bbb", textTransform: "uppercase", fontFamily: "'DM Sans',sans-serif" }}>
            Model confidence per conflict
          </span>
          {conflicts.map((p, i) => {
            const barW = animated ? p.confidence : 0;
            return (
              <div key={p.id} style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <span style={{ fontSize: 10, color: "#aaa", fontFamily: "'DM Sans',sans-serif", width: 16, flexShrink: 0 }}>#{i + 1}</span>
                <div style={{ flex: 1, height: 8, borderRadius: 99, background: "#f0ebe3", overflow: "hidden" }}>
                  <div style={{
                    height: "100%", borderRadius: 99,
                    background: "linear-gradient(90deg, #f59e0b, #E85D04)",
                    width: `${barW}%`,
                    transition: `width 1s ${0.1 * i + 0.3}s cubic-bezier(0.34,1.2,0.64,1)`,
                  }} />
                </div>
                <span style={{ fontSize: 10, color: "#999", fontFamily: "'DM Sans',sans-serif", width: 28, textAlign: "right", flexShrink: 0 }}>{p.confidence}%</span>
              </div>
            );
          })}
        </div>
      )}

      {total === 0 && (
        <p style={{ fontSize: 13, color: "#bbb", fontFamily: "'DM Sans',sans-serif", marginTop: 8 }}>
          No contradictions or agreements to score yet. Upload 2+ sources on a similar topic.
        </p>
      )}
    </div>
  );
}

/* ── Claim pair (side-by-side) ────────────────────────────────────── */
const REL = {
  contradiction: { label: "Contradiction", color: "#E85D04", icon: "⚡" },
  agreement:     { label: "Agreement",     color: "#2D6A4F", icon: "✅" },
  neutral:       { label: "Neutral",       color: "#888",    icon: "➖" },
};

const WEB = {
  supported:    { label: "Supported by web sources",    color: "#2D6A4F", icon: "✅" },
  contradicted: { label: "Contradicted by web sources", color: "#E85D04", icon: "⚡" },
  unverified:   { label: "Could not be verified",       color: "#888",    icon: "❔" },
};

function ClaimBox({ claim, accent }) {
  const [open, setOpen] = useState(false);
  const [passage, setPassage] = useState(null);
  const [web, setWeb] = useState(null);
  const [webLoading, setWebLoading] = useState(false);

  async function verifyWeb() {
    setWebLoading(true);
    try {
      const r = await apiFetch(`/verify/`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ claim_id: claim.id }),
      });
      setWeb(await r.json());
    } catch (e) { setWeb({ error: "Request failed. Is the backend running?" }); }
    setWebLoading(false);
  }

  async function togglePassage() {
    if (!open && !passage) {
      try {
        const r = await apiFetch(`/chunk/${claim.chunk_id}`);
        setPassage(await r.json());
      } catch (e) { setPassage({ text: "Could not load the passage." }); }
    }
    setOpen(o => !o);
  }

  return (
    <div style={{ flex: "1 1 260px", minWidth: 0, background: "#fff", borderRadius: 14, padding: "16px 18px", border: `1px solid ${accent}33` }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10 }}>
        <span style={{ fontSize: 11, fontWeight: 700, color: accent, fontFamily: "'DM Sans',sans-serif", maxWidth: 190, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
          {claim.source_name}
        </span>
        {claim.page != null && (
          <span style={{ fontSize: 10, fontWeight: 700, color: "#666", background: "#f0ebe3", borderRadius: 99, padding: "2px 8px", fontFamily: "'DM Sans',sans-serif" }}>
            p.{claim.page}
          </span>
        )}
        {claim.support != null && (
          <span title="Probability, from an NLI model, that the source text really backs this claim"
            style={{ fontSize: 10, fontWeight: 700, color: claim.support >= 0.5 ? "#2D6A4F" : "#b45309", background: claim.support >= 0.5 ? "rgba(45,106,79,0.1)" : "rgba(245,158,11,0.15)", borderRadius: 99, padding: "2px 8px", fontFamily: "'DM Sans',sans-serif" }}>
            🛡 source support {Math.round(claim.support * 100)}%
          </span>
        )}
      </div>
      <p style={{ fontSize: 14, lineHeight: 1.65, color: "#222", fontFamily: "'DM Sans',sans-serif" }}>{claim.text}</p>
      {claim.evidence && (
        <p style={{ fontSize: 12, lineHeight: 1.6, color: "#888", fontStyle: "italic", marginTop: 8, fontFamily: "'DM Sans',sans-serif" }}>
          &ldquo;{claim.evidence}&rdquo;
          {!claim.evidence_verified && (
            <span title="This quote was not found word-for-word in the source passage" style={{ marginLeft: 6, color: "#f59e0b", fontStyle: "normal" }}>⚠ not verbatim</span>
          )}
        </p>
      )}
      <button onClick={togglePassage} style={{
        marginTop: 10, background: "none", border: "none", padding: 0, cursor: "pointer",
        fontSize: 11, fontWeight: 700, color: accent, fontFamily: "'DM Sans',sans-serif", letterSpacing: "0.04em",
      }}>
        {open ? "▲ Hide source passage" : "▼ View source passage"}
      </button>
      {open && passage && (
        <div style={{ marginTop: 8, maxHeight: 180, overflowY: "auto", fontSize: 12, lineHeight: 1.7, color: "#555", background: "#faf7f2", borderRadius: 10, padding: "10px 12px", fontFamily: "'DM Sans',sans-serif" }}>
          {passage.text}
        </div>
      )}

      <div style={{ marginTop: 12, paddingTop: 12, borderTop: "1px dashed #e5dfd5" }}>
        {!web && (
          <button onClick={verifyWeb} disabled={webLoading} style={{
            background: "none", border: `1px solid ${accent}55`, borderRadius: 99, padding: "5px 12px", cursor: webLoading ? "wait" : "pointer",
            fontSize: 11, fontWeight: 700, color: accent, fontFamily: "'DM Sans',sans-serif",
          }}>
            {webLoading ? "Searching the web…" : "🌐 Verify on the web"}
          </button>
        )}
        {web?.error && (
          <p style={{ fontSize: 12, color: "#b91c1c", fontFamily: "'DM Sans',sans-serif" }}>⚠ {web.error}</p>
        )}
        {web && !web.error && (() => {
          const w = WEB[web.verdict] || WEB.unverified;
          return (
            <div style={{ fontFamily: "'DM Sans',sans-serif" }}>
              <span style={{ fontSize: 11, fontWeight: 700, color: w.color }}>{w.icon} {w.label} · {web.confidence}%</span>
              <p style={{ fontSize: 12, lineHeight: 1.6, color: "#555", marginTop: 4 }}>{web.explanation}</p>
              {web.sources?.filter(src => /^https?:\/\//.test(src.url)).map(src => (
                <a key={src.url} href={src.url} target="_blank" rel="noopener noreferrer"
                  style={{ display: "block", fontSize: 11, color: "#0077B6", marginTop: 3, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  🔗 {src.title}
                </a>
              ))}
            </div>
          );
        })()}
      </div>
    </div>
  );
}

function PairCard({ pair }) {
  const rel = REL[pair.relation] || REL.neutral;
  return (
    <div style={{ background: `${rel.color}0D`, borderRadius: 18, borderLeft: `5px solid ${rel.color}`, padding: "20px 22px" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 14, flexWrap: "wrap" }}>
        <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.12em", textTransform: "uppercase", color: rel.color, fontFamily: "'DM Sans',sans-serif" }}>
          {rel.icon} {rel.label}
        </span>
        <span style={{ fontSize: 11, color: "#999", fontFamily: "'DM Sans',sans-serif" }}>
          confidence {pair.confidence}% · similarity {pair.similarity}
        </span>
        {pair.verified && (
          <span title="A larger model re-checked this verdict" style={{ fontSize: 11, fontWeight: 700, color: "#2D6A4F", fontFamily: "'DM Sans',sans-serif" }}>
            🔍 re-checked by larger model{pair.first_opinion && pair.first_opinion !== pair.relation ? ` (first opinion: ${pair.first_opinion})` : ""}
          </span>
        )}
      </div>
      <div style={{ display: "flex", gap: 14, flexWrap: "wrap", alignItems: "stretch" }}>
        <ClaimBox claim={pair.claim_a} accent={rel.color} />
        <ClaimBox claim={pair.claim_b} accent={rel.color} />
      </div>
      {pair.explanation && (
        <p style={{ fontSize: 13, lineHeight: 1.7, color: "#444", marginTop: 14, fontFamily: "'DM Sans',sans-serif" }}>
          <b>Why:</b> {pair.explanation}
        </p>
      )}
    </div>
  );
}

function PairsSection({ pairs, processing }) {
  const [filter, setFilter] = useState("contradiction");
  const counts = {
    contradiction: pairs.filter(p => p.relation === "contradiction").length,
    agreement: pairs.filter(p => p.relation === "agreement").length,
    all: pairs.length,
  };
  const shown = filter === "all" ? pairs : pairs.filter(p => p.relation === filter);
  const tabs = [["contradiction", "⚡ Conflicts"], ["agreement", "✅ Agreements"], ["all", "All"]];

  return (
    <div style={{ background: "#fff", borderRadius: 20, padding: "24px 24px 20px", boxShadow: "0 2px 20px rgba(0,0,0,0.05)" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 10, marginBottom: 18 }}>
        <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.14em", textTransform: "uppercase", color: "#E85D04", fontFamily: "'DM Sans',sans-serif" }}>
          Claim comparison
        </span>
        <div style={{ display: "flex", gap: 6 }}>
          {tabs.map(([key, label]) => (
            <button key={key} onClick={() => setFilter(key)} style={{
              border: "none", borderRadius: 99, padding: "6px 12px", cursor: "pointer",
              fontSize: 11, fontWeight: 700, fontFamily: "'DM Sans',sans-serif",
              background: filter === key ? "#1a1a1a" : "#f0ebe3", color: filter === key ? "#fff" : "#666",
            }}>{label} ({counts[key]})</button>
          ))}
        </div>
      </div>
      {shown.length === 0 ? (
        <p style={{ fontSize: 13, color: "#999", lineHeight: 1.7, fontFamily: "'DM Sans',sans-serif" }}>
          {processing
            ? "⏳ Comparing claims across your sources… results appear here in a few seconds."
            : pairs.length === 0
            ? "No comparable claim pairs were found. The sources may cover different topics."
            : filter === "contradiction"
              ? `No contradictions detected among the ${pairs.length} claim pairs compared. Check "Agreements" or "All" to see what was compared.`
              : "Nothing in this category."}
        </p>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          {shown.map(p => <PairCard key={p.id} pair={p} />)}
        </div>
      )}
    </div>
  );
}

/* ── Claim knowledge graph ─────────────────────────────────────────── */
const SRC_COLORS = ["#0077B6", "#E85D04", "#2D6A4F", "#7B2CBF", "#B08900", "#C9184A"];

function ClaimGraph({ graph }) {
  const [showAll, setShowAll] = useState(false);
  const [sel, setSel] = useState(null);

  const nodes = (graph?.nodes || []).filter(n => showAll || n.connected);
  const ids = new Set(nodes.map(n => n.id));
  const edges = (graph?.edges || []).filter(e => ids.has(e.source) && ids.has(e.target));
  if (!graph || (graph.edges || []).length === 0) return null;

  // one column per source, claims stacked top to bottom
  const sourceIds = [...new Set((graph.nodes || []).map(n => n.source_id))];
  const cols = sourceIds.length;
  const W = 900, TOP = 56, STEP = 44;
  const perCol = {};
  nodes.forEach(n => { (perCol[n.source_id] = perCol[n.source_id] || []).push(n); });
  const H = Math.max(200, TOP + Math.max(...Object.values(perCol).map(a => a.length), 1) * STEP + 20);
  const pos = {};
  sourceIds.forEach((sid, ci) => {
    const x = (ci + 0.5) * (W / cols);
    (perCol[sid] || []).forEach((n, i) => { pos[n.id] = { x, y: TOP + i * STEP }; });
  });
  const byId = Object.fromEntries((graph.nodes || []).map(n => [n.id, n]));
  const colorOf = sid => SRC_COLORS[sourceIds.indexOf(sid) % SRC_COLORS.length];
  const touching = sel ? edges.filter(e => e.source === sel || e.target === sel) : [];
  const selNode = sel ? byId[sel] : null;

  return (
    <div style={{ background: "#fff", borderRadius: 20, padding: "24px 24px 20px", boxShadow: "0 2px 20px rgba(0,0,0,0.05)" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 10, marginBottom: 6 }}>
        <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.14em", textTransform: "uppercase", color: "#0077B6", fontFamily: "'DM Sans',sans-serif" }}>
          🕸 Claim graph
        </span>
        <label style={{ fontSize: 11, color: "#666", fontFamily: "'DM Sans',sans-serif", cursor: "pointer" }}>
          <input type="checkbox" checked={showAll} onChange={e => { setShowAll(e.target.checked); setSel(null); }} style={{ marginRight: 6 }} />
          show claims without links
        </label>
      </div>
      <p style={{ fontSize: 12, color: "#999", marginBottom: 10, fontFamily: "'DM Sans',sans-serif" }}>
        Each dot is a claim, each column a source. <span style={{ color: "#E85D04", fontWeight: 700 }}>Orange = contradicts</span>,{" "}
        <span style={{ color: "#2D6A4F", fontWeight: 700 }}>green = supports</span>. Click a dot to see its links.
      </p>
      <svg viewBox={`0 0 ${W} ${H}`} style={{ width: "100%", height: "auto" }}>
        {sourceIds.map((sid, ci) => {
          const name = byId[(graph.nodes || []).find(n => n.source_id === sid)?.id]?.source_name || "";
          return (
            <text key={sid} x={(ci + 0.5) * (W / cols)} y={22} textAnchor="middle" fontSize="13" fontWeight="700" fill={colorOf(sid)} fontFamily="'DM Sans',sans-serif">
              {name.length > 26 ? name.slice(0, 25) + "…" : name}
            </text>
          );
        })}
        {edges.map((e, i) => {
          const a = pos[e.source], b = pos[e.target];
          if (!a || !b) return null;
          const mx = (a.x + b.x) / 2;
          const on = !sel || e.source === sel || e.target === sel;
          return (
            <path key={i} d={`M ${a.x} ${a.y} C ${mx} ${a.y}, ${mx} ${b.y}, ${b.x} ${b.y}`} fill="none"
              stroke={e.relation === "contradicts" ? "#E85D04" : "#2D6A4F"}
              strokeWidth={1 + e.confidence / 50} opacity={on ? 0.85 : 0.1} />
          );
        })}
        {nodes.map(n => {
          const p = pos[n.id];
          if (!p) return null;
          return (
            <circle key={n.id} cx={p.x} cy={p.y} r={sel === n.id ? 12 : 9} fill={colorOf(n.source_id)}
              stroke="#fff" strokeWidth="2" opacity={!n.connected ? 0.35 : 1} style={{ cursor: "pointer" }}
              onClick={() => setSel(sel === n.id ? null : n.id)}>
              <title>{n.label}</title>
            </circle>
          );
        })}
      </svg>
      {selNode && (
        <div style={{ marginTop: 10, padding: "14px 16px", borderRadius: 14, background: "#faf7f2", fontFamily: "'DM Sans',sans-serif" }}>
          <p style={{ fontSize: 13, color: "#222", lineHeight: 1.6 }}>
            <b style={{ color: colorOf(selNode.source_id) }}>{selNode.source_name}{selNode.page != null ? ` · p.${selNode.page}` : ""}:</b> {selNode.label}
          </p>
          {touching.length === 0 && <p style={{ fontSize: 12, color: "#999", marginTop: 6 }}>No links to other sources.</p>}
          {touching.map((e, i) => {
            const other = byId[e.source === sel ? e.target : e.source];
            return (
              <p key={i} style={{ fontSize: 12, color: "#555", marginTop: 6, lineHeight: 1.6 }}>
                <b style={{ color: e.relation === "contradicts" ? "#E85D04" : "#2D6A4F" }}>
                  {e.relation === "contradicts" ? "⚡ contradicts" : "✅ supports"} ({e.confidence}%)
                </b>{" "}
                <i>{other?.source_name}</i>: {other?.label}
              </p>
            );
          })}
        </div>
      )}
    </div>
  );
}

/* ── Ask Panel ────────────────────────────────────────────────────── */
function AskPanel({ activeTab, sources, querying, query, setQuery, handleQuery, queryResult }) {
  const activeSrc = sources.find(s => s.id === activeTab);
  const scopeLabel = activeTab === "combined"
    ? `Asking across all ${sources.length} sources`
    : activeSrc ? `Asking about: ${activeSrc.name}` : "";

  return (
    <div style={{
      background: "#1a1a1a", borderRadius: 20, padding: "28px",
      animation: "popIn 0.5s 0.3s ease both",
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
        <span style={{ fontSize: 20 }}>💬</span>
        <div>
          <div style={{ fontSize: 14, fontWeight: 700, color: "#F5F0E8", fontFamily: "'Syne',sans-serif" }}>Ask a Question</div>
        </div>
      </div>
      <p style={{ fontSize: 11, color: "#E85D04", fontFamily: "'DM Sans',sans-serif", marginBottom: 18, letterSpacing: "0.04em" }}>
        {scopeLabel}
      </p>

      <textarea value={query} onChange={e => setQuery(e.target.value)}
        onKeyDown={e => e.key === "Enter" && !e.shiftKey && (e.preventDefault(), handleQuery())}
        placeholder={activeTab === "combined"
          ? "e.g. What do all sources agree on? Where do they conflict?"
          : "e.g. What is the main argument of this source?"}
        rows={4}
        style={{
          width: "100%", background: "rgba(245,240,232,0.08)", border: "2px solid rgba(245,240,232,0.12)",
          borderRadius: 12, color: "#F5F0E8", padding: "12px 14px", fontSize: 13,
          outline: "none", fontFamily: "'DM Sans',sans-serif",
          resize: "none", lineHeight: 1.6, boxSizing: "border-box",
          transition: "border-color 0.2s",
        }}
        onFocus={e => e.target.style.borderColor = "#E85D04"}
        onBlur={e => e.target.style.borderColor = "rgba(245,240,232,0.12)"} />

      <button onClick={handleQuery} disabled={querying || !query.trim()} style={{
        width: "100%", marginTop: 12, padding: "13px", borderRadius: 12,
        background: query.trim() && !querying ? "#E85D04" : "rgba(245,240,232,0.1)",
        border: "none", color: "#fff",
        fontSize: 14, fontWeight: 700,
        cursor: query.trim() && !querying ? "pointer" : "not-allowed",
        fontFamily: "'Syne',sans-serif", letterSpacing: "0.03em",
        transition: "all 0.3s cubic-bezier(0.34,1.2,0.64,1)",
        display: "flex", alignItems: "center", justifyContent: "center", gap: 8,
      }}>
        {querying
          ? <><span style={{ width: 14, height: 14, borderRadius: "50%", border: "2px solid rgba(255,255,255,0.3)", borderTopColor: "#fff", animation: "spin 0.8s linear infinite", display: "inline-block" }} />Thinking…</>
          : "Ask →"}
      </button>

      {queryResult && (
        <div style={{
          marginTop: 18, background: "rgba(245,240,232,0.07)", borderRadius: 12,
          padding: "18px", borderLeft: "3px solid #E85D04",
          animation: "fadeUp 0.4s ease both",
        }}>
          <div style={{ fontSize: 10, letterSpacing: "0.12em", fontWeight: 700, color: "#E85D04", textTransform: "uppercase", fontFamily: "'DM Sans',sans-serif", marginBottom: 10 }}>Answer</div>
          <div style={{ fontSize: 13, lineHeight: 1.85, color: "rgba(245,240,232,0.85)", fontFamily: "'DM Sans',sans-serif", fontWeight: 300, whiteSpace: "pre-wrap" }}>
            <TypeWriter text={queryResult} speed={8} />
          </div>
        </div>
      )}
    </div>
  );
}

/* ── Source tab button ────────────────────────────────────────────── */
function SourceTab({ source, active, onClick }) {
  const TYPE = {
    pdf: { emoji: "📄", color: "#0077B6" },
    url: { emoji: "🌐", color: "#2D6A4F" },
    text: { emoji: "✍️", color: "#7209B7" },
  };
  const m = TYPE[source.type] || TYPE.text;
  return (
    <button onClick={onClick} style={{
      display: "flex", alignItems: "center", gap: 10,
      padding: "14px 20px", background: active ? "#1a1a1a" : "transparent",
      border: "none", borderRadius: 14, cursor: "pointer", whiteSpace: "nowrap",
      transition: "all 0.3s cubic-bezier(0.34,1.2,0.64,1)",
      transform: active ? "scale(1.03)" : "scale(1)",
      boxShadow: active ? "0 8px 24px rgba(0,0,0,0.15)" : "none",
    }}>
      <span style={{ fontSize: 18 }}>{m.emoji}</span>
      <div style={{ textAlign: "left" }}>
        <div style={{ fontSize: 12, fontWeight: 700, color: active ? "#fff" : "#555", fontFamily: "'Syne',sans-serif", transition: "color 0.3s", maxWidth: 120, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
          {source.name}
        </div>
        <div style={{ fontSize: 10, color: active ? m.color : "#aaa", fontFamily: "'DM Sans',sans-serif" }}>
          {source.chunk_count} chunks
        </div>
      </div>
    </button>
  );
}

/* ── Upload panel ─────────────────────────────────────────────────── */
function UploadPanel({ onNewResults, onClose }) {
  const fileRef = useRef();
  const [tab, setTab] = useState("pdf");
  const [files, setFiles] = useState([]);
  const [urls, setUrls] = useState([""]);
  const [textInput, setTextInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");

  const hasInput = files.length > 0 || urls.some(u => u.trim()) || textInput.trim();
  const inp = {
    width: "100%", background: "#F5F0E8", border: "2px solid #e8e2d9", borderRadius: 10,
    color: "#1a1a1a", padding: "10px 14px", fontSize: 13, outline: "none",
    fontFamily: "'DM Sans',sans-serif", boxSizing: "border-box",
  };

  async function handleAdd() {
    if (!hasInput) return;
    setLoading(true); setMsg("");
    try {
      const form = new FormData();
      files.forEach(f => form.append("files", f));
      form.append("url_input", urls.filter(u => u.trim()).join(","));
      form.append("text_input", textInput);
      const res = await apiFetch(`/upload/`, { method: "POST", body: form });
      const data = await res.json();
      if (data.error) { setMsg("⚠ " + data.error); return; }
      onNewResults(data);
      setFiles([]); setUrls([""]); setTextInput("");
      setMsg("✓ Done! Results updated.");
    } catch (e) { setMsg("⚠ Backend not reachable"); }
    finally { setLoading(false); }
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span style={{ fontSize: 12, fontWeight: 700, letterSpacing: "0.12em", textTransform: "uppercase", color: "#999", fontFamily: "'DM Sans',sans-serif" }}>Add Sources</span>
        <button onClick={onClose} style={{ background: "none", border: "none", color: "#aaa", cursor: "pointer", fontSize: 20, lineHeight: 1, padding: 0 }}>×</button>
      </div>
      <div style={{ display: "flex", gap: 6 }}>
        {["pdf", "url", "text"].map(t => (
          <button key={t} onClick={() => setTab(t)} style={{
            flex: 1, padding: "8px 4px", background: tab === t ? "#1a1a1a" : "#EDE8DF",
            border: "none", borderRadius: 10, color: tab === t ? "#fff" : "#888",
            fontSize: 11, fontWeight: 700, cursor: "pointer",
            fontFamily: "'DM Sans',sans-serif", textTransform: "uppercase",
            letterSpacing: "0.08em", transition: "all 0.25s",
          }}>{t}</button>
        ))}
      </div>

      {tab === "pdf" && <>
        <div onClick={() => fileRef.current.click()} style={{
          border: "2px dashed #ddd", borderRadius: 14, padding: "32px 16px",
          textAlign: "center", cursor: "pointer", background: "#fafafa", transition: "all 0.2s",
        }}
          onMouseEnter={e => { e.currentTarget.style.borderColor = "#E85D04"; e.currentTarget.style.background = "#fff8f5"; }}
          onMouseLeave={e => { e.currentTarget.style.borderColor = "#ddd"; e.currentTarget.style.background = "#fafafa"; }}>
          <input ref={fileRef} type="file" accept=".pdf" multiple style={{ display: "none" }}
            onChange={e => setFiles(p => [...p, ...Array.from(e.target.files)])} />
          <div style={{ fontSize: 28, marginBottom: 6 }}>📄</div>
          <p style={{ fontSize: 12, color: "#aaa", fontFamily: "'DM Sans',sans-serif" }}>Click to browse PDFs</p>
        </div>
        {files.map((f, i) => (
          <div key={i} style={{ display: "flex", alignItems: "center", gap: 8, background: "#F5F0E8", borderRadius: 10, padding: "10px 12px" }}>
            <span style={{ fontSize: 14 }}>📄</span>
            <span style={{ flex: 1, fontSize: 12, color: "#333", fontFamily: "'DM Sans',sans-serif", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{f.name}</span>
            <button onClick={() => setFiles(p => p.filter((_, j) => j !== i))} style={{ background: "none", border: "none", color: "#ccc", cursor: "pointer", fontSize: 14 }}>✕</button>
          </div>
        ))}
      </>}

      {tab === "url" && <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {urls.map((u, i) => (
          <div key={i} style={{ display: "flex", gap: 6 }}>
            <input style={{ ...inp, flex: 1 }} placeholder="https://" value={u}
              onChange={e => setUrls(us => us.map((x, j) => j === i ? e.target.value : x))} />
            {urls.length > 1 && <button onClick={() => setUrls(us => us.filter((_, j) => j !== i))}
              style={{ background: "none", border: "2px solid #ddd", borderRadius: 8, color: "#ccc", cursor: "pointer", padding: "0 10px", fontSize: 14 }}>✕</button>}
          </div>
        ))}
        <button onClick={() => setUrls(u => [...u, ""])}
          style={{ background: "none", border: "none", color: "#E85D04", fontSize: 12, cursor: "pointer", textAlign: "left", padding: 0, fontFamily: "'DM Sans',sans-serif" }}>+ Add URL</button>
      </div>}

      {tab === "text" && <textarea style={{ ...inp, resize: "none" }} rows={5} placeholder="Paste text…"
        value={textInput} onChange={e => setTextInput(e.target.value)} />}

      {msg && <p style={{ fontSize: 12, color: msg.startsWith("✓") ? "#2D6A4F" : "#dc2626", fontFamily: "'DM Sans',sans-serif" }}>{msg}</p>}

      <button onClick={handleAdd} disabled={loading || !hasInput} style={{
        padding: "13px", borderRadius: 12,
        background: hasInput && !loading ? "#1a1a1a" : "#e0dbd4",
        border: "none", color: hasInput && !loading ? "#fff" : "#aaa",
        fontSize: 13, fontWeight: 700, cursor: hasInput && !loading ? "pointer" : "not-allowed",
        fontFamily: "'Syne',sans-serif",
        display: "flex", alignItems: "center", justifyContent: "center", gap: 8,
        transition: "all 0.25s",
      }}>
        {loading
          ? <><span style={{ width: 14, height: 14, borderRadius: "50%", border: "2px solid rgba(255,255,255,0.3)", borderTopColor: "#fff", animation: "spin 0.8s linear infinite", display: "inline-block" }} />Analyzing…</>
          : "Add & Re-analyze"}
      </button>
    </div>
  );
}

/* ── Main Dashboard ───────────────────────────────────────────────── */
export default function Dashboard() {
  const navigate = useNavigate();
  const [sources, setSources] = useState([]);
  const [combined, setCombined] = useState(null);
  const [pairs, setPairs] = useState([]);
  const [status, setStatus] = useState({ state: "idle", stage: "" });
  const [graph, setGraph] = useState({ nodes: [], edges: [] });
  const [guard, setGuard] = useState(null);
  const [totalChunks, setTotalChunks] = useState(0);
  const [activeTab, setActiveTab] = useState("combined");
  const [panelOpen, setPanelOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [querying, setQuerying] = useState(false);
  const [queryResult, setQueryResult] = useState(null);
  const [headerVis, setHeaderVis] = useState(false);

  useEffect(() => {
    const raw = sessionStorage.getItem("analysisResult");
    if (raw) { try { applyResult(JSON.parse(raw)); sessionStorage.removeItem("analysisResult"); } catch (e) { } }
    else {
      // page was refreshed: the backend still holds the data, so reload it instead of showing an empty page
      apiFetch(`/status/`).then(r => r.json()).then(d => { if (d.sources?.length) applyResult(d); }).catch(() => { });
    }
    setTimeout(() => setHeaderVis(true), 80);
  }, []);

  // Clear query result whenever tab changes
  useEffect(() => {
    setQueryResult(null);
    setQuery("");
  }, [activeTab]);

  function applyResult(data, polling = false) {
    setStatus(data.status || { state: "idle", stage: "" });
    setSources(data.sources || []);
    setCombined(data.combined || null);
    setPairs(data.pairs || []);
    setGraph(data.graph || { nodes: [], edges: [] });
    setGuard(data.guard || null);
    setTotalChunks(data.total_chunks || 0);
    if (polling) return;  // background refresh: don't reset the tab the user is looking at
    const src = data.sources || [];
    setActiveTab(src.length > 1 ? "combined" : src[0]?.id ?? "combined");
    setQueryResult(null);
  }

  // The upload answers instantly; claims + contradictions are computed in the background. Poll until done.
  useEffect(() => {
    if (status.state !== "processing") return;
    const id = setInterval(async () => {
      try {
        const res = await apiFetch(`/status/`);
        applyResult(await res.json(), true);
      } catch (e) { /* keep polling */ }
    }, 1500);
    return () => clearInterval(id);
  }, [status.state]);

  async function handleClear() {
    if (!window.confirm("Clear all data?")) return;
    await apiFetch(`/clear/`, { method: "POST" });
    setSources([]); setCombined(null); setPairs([]); setGraph({ nodes: [], edges: [] }); setGuard(null); setTotalChunks(0); setStatus({ state: "idle", stage: "" });
    setActiveTab("combined"); setQueryResult(null);
  }

  // Query is scoped to activeTab — passes source_name param if on individual tab
  async function handleQuery() {
    if (!query.trim() || !sources.length) return;
    setQuerying(true); setQueryResult(null);
    try {
      const activeSrc = sources.find(s => s.id === activeTab);
      let url = `/compare/?query=${encodeURIComponent(query)}`;
      if (activeSrc) url += `&source_name=${encodeURIComponent(activeSrc.name)}`;
      const res = await apiFetch(url);
      const data = await res.json();
      const cites = (data.citations || [])
        .map(c => `[${c.n}] ${c.source}${c.page ? ` · p.${c.page}` : ""}`).join("\n");
      setQueryResult(cites ? `${data.answer}\n\nSources:\n${cites}` : data.answer);
    } catch (e) { setQueryResult("Error: " + e.message); }
    finally { setQuerying(false); }
  }

  const activeSrc = sources.find(s => s.id === activeTab);

  const CARD_CONFIGS = [
    { key: "summary", title: "Summary", icon: "🔍", accentColor: "#0077B6", bgColor: "rgba(0,119,182,0.05)" },
    { key: "agreements", title: "Key Findings", icon: "✅", accentColor: "#2D6A4F", bgColor: "rgba(45,106,79,0.05)" },
  ];

  function renderAnalysis(analysis, baseDelay = 0, scopePairs = [], isCombined = false) {
    if (!analysis) return (
      <div style={{ padding: "80px 0", textAlign: "center", color: "#bbb", fontFamily: "'DM Sans',sans-serif", fontSize: 15 }}>
        No analysis available.
      </div>
    );
    return (
      <div style={{ display: "grid", gridTemplateColumns: "1fr minmax(300px, 360px)", gap: 24, alignItems: "flex-start" }}>

        {/* LEFT column — cards + ask panel at bottom */}
        <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          {CARD_CONFIGS.map((cfg, i) => (
            <ResultCard key={cfg.key} title={cfg.title} icon={cfg.icon}
              accentColor={cfg.accentColor} bgColor={cfg.bgColor}
              items={analysis[cfg.key]} delay={baseDelay + i * 160} />
          ))}
          {guard?.removed > 0 && (
            <div style={{ padding: "12px 18px", borderRadius: 14, background: "rgba(0,119,182,0.07)", color: "#0077B6", fontSize: 12, fontWeight: 700, fontFamily: "'DM Sans',sans-serif" }}>
              🛡 Hallucination guard: {guard.removed} of {guard.checked} extracted claims were removed because the source text did not support them.
            </div>
          )}
          {(scopePairs.length > 0 || isCombined) && <PairsSection pairs={scopePairs} processing={status.state === "processing"} />}
          {isCombined && <ClaimGraph graph={graph} />}
          <AskPanel
            activeTab={activeTab}
            sources={sources}
            querying={querying}
            query={query}
            setQuery={setQuery}
            handleQuery={handleQuery}
            queryResult={queryResult}
          />
        </div>

        {/* RIGHT column — sticky contradiction graph only */}
        <div style={{ position: "sticky", top: 24 }}>
          <ContradictionMeter
            stats={analysis.stats}
            conflicts={scopePairs.filter(p => p.relation === "contradiction")}
            delay={baseDelay + 2 * 160}
          />
        </div>

      </div>
    );
  }

  return (
    <div style={{
      minHeight: "100vh", background: "#F5F0E8",
      fontFamily: "'Syne','DM Sans',sans-serif", color: "#1a1a1a",
      position: "relative", overflowX: "hidden",
    }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500&display=swap');
        @keyframes fadeUp    { from{opacity:0;transform:translateY(20px)} to{opacity:1;transform:translateY(0)} }
        @keyframes slideRight{ from{opacity:0;transform:translateX(-12px)} to{opacity:1;transform:translateX(0)} }
        @keyframes spin      { to{transform:rotate(360deg)} }
        @keyframes blink     { 0%,100%{opacity:1} 50%{opacity:0} }
        @keyframes popIn     { from{opacity:0;transform:scale(0.92)} to{opacity:1;transform:scale(1)} }
        @keyframes floatY    { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-18px) rotate(5deg)} }
        * { box-sizing:border-box; margin:0; padding:0; }
        ::-webkit-scrollbar{width:6px} ::-webkit-scrollbar-track{background:transparent}
        ::-webkit-scrollbar-thumb{background:#ddd;border-radius:3px}
      `}</style>

      {/* Floating bg emojis */}
      {[
        { e: "⚡", x: 3, y: 8, s: 20, d: 0, dr: 7 },
        { e: "💥", x: 93, y: 12, s: 18, d: 1.2, dr: 9 },
        { e: "🧩", x: 95, y: 60, s: 22, d: 0.5, dr: 8 },
        { e: "❓", x: 2, y: 72, s: 16, d: 2, dr: 11 },
      ].map((f, i) => (
        <div key={i} style={{
          position: "fixed", left: `${f.x}%`, top: `${f.y}%`,
          fontSize: f.s, opacity: 0.12, pointerEvents: "none", zIndex: 0,
          animation: `floatY ${f.dr}s ${f.d}s ease-in-out infinite`,
        }}>{f.e}</div>
      ))}

      <div style={{ position: "relative", zIndex: 1, display: "flex", flexDirection: "column", minHeight: "100vh" }}>

        {/* TOP STRIP */}
        <div style={{
          background: "#1a1a1a", padding: "12px 32px",
          display: "flex", alignItems: "center", justifyContent: "space-between",
          opacity: headerVis ? 1 : 0, transition: "opacity 0.5s",
        }}>
          <button onClick={() => navigate("/")} style={{
            background: "linear-gradient(90deg,#F5F0E8,#f0a070)",
            WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent",
            border: "none", cursor: "pointer",
            fontSize: 22, fontWeight: 800, letterSpacing: "-1px",
            fontFamily: "'Syne',sans-serif",
          }}>ReasonIX</button>

          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            {sources.length > 0 && (
              <span style={{ fontSize: 11, color: "rgba(245,240,232,0.4)", fontFamily: "'DM Sans',sans-serif" }}>
                {sources.length} source{sources.length > 1 ? "s" : ""} · {totalChunks} chunks
              </span>
            )}
            <button onClick={() => setPanelOpen(o => !o)} style={{
              background: panelOpen ? "#E85D04" : "rgba(245,240,232,0.08)",
              border: "none", borderRadius: 10, color: "#F5F0E8",
              padding: "8px 18px", fontSize: 12, fontWeight: 700, cursor: "pointer",
              fontFamily: "'DM Sans',sans-serif", transition: "all 0.25s", letterSpacing: "0.04em",
            }}>
              {panelOpen ? "✕ Close" : "+ Add Sources"}
            </button>
            {sources.length > 0 && (
              <button onClick={handleClear} style={{
                background: "none", border: "1px solid rgba(239,68,68,0.3)",
                borderRadius: 10, color: "rgba(252,165,165,0.7)",
                padding: "8px 14px", fontSize: 12, cursor: "pointer",
                fontFamily: "'DM Sans',sans-serif", transition: "all 0.2s",
              }}
                onMouseEnter={e => { e.currentTarget.style.borderColor = "rgba(239,68,68,0.7)"; e.currentTarget.style.color = "#fca5a5"; }}
                onMouseLeave={e => { e.currentTarget.style.borderColor = "rgba(239,68,68,0.3)"; e.currentTarget.style.color = "rgba(252,165,165,0.7)"; }}>
                Clear
              </button>
            )}
            <button onClick={() => navigate("/input")} style={{
              background: "none", border: "1px solid rgba(245,240,232,0.15)",
              borderRadius: 10, color: "rgba(245,240,232,0.4)",
              padding: "8px 14px", fontSize: 12, cursor: "pointer",
              fontFamily: "'DM Sans',sans-serif",
            }}>← Upload</button>
          </div>
        </div>

        {/* BODY */}
        <div style={{ flex: 1, display: "flex", overflow: "hidden" }}>

          {/* Upload side panel */}
          {panelOpen && (
            <div style={{
              width: 300, flexShrink: 0, padding: 24, overflowY: "auto",
              background: "#fff", borderRight: "2px solid #EDE8DF",
              animation: "popIn 0.35s ease both",
            }}>
              <UploadPanel onNewResults={applyResult} onClose={() => setPanelOpen(false)} />
            </div>
          )}

          {/* Main content */}
          <main style={{ flex: 1, overflowY: "auto", padding: "36px 40px", width: "100%" }}>

            {/* Empty state */}
            {sources.length === 0 && (
              <div style={{
                display: "flex", flexDirection: "column", alignItems: "center",
                justifyContent: "center", minHeight: "60vh", textAlign: "center", gap: 24,
                animation: "fadeUp 0.7s ease both",
              }}>
                <div style={{ fontSize: 72, filter: "drop-shadow(0 8px 24px rgba(232,93,4,0.2))" }}>🔍</div>
                <div>
                  <h2 style={{ fontSize: 32, fontWeight: 800, letterSpacing: "-1px", marginBottom: 12, fontFamily: "'Syne',sans-serif" }}>Nothing here yet</h2>
                  <p style={{ fontSize: 15, color: "#888", maxWidth: 360, lineHeight: 1.7, fontFamily: "'DM Sans',sans-serif", fontWeight: 300 }}>
                    Go to the upload page or click{" "}
                    <button onClick={() => setPanelOpen(true)} style={{ background: "none", border: "none", color: "#E85D04", cursor: "pointer", fontSize: 15, fontWeight: 500, fontFamily: "'DM Sans',sans-serif", padding: 0, textDecoration: "underline" }}>
                      Add Sources
                    </button>{" "}above.
                  </p>
                </div>
                <button onClick={() => navigate("/input")} style={{
                  background: "#1a1a1a", border: "none", color: "#F5F0E8",
                  borderRadius: 14, padding: "14px 36px", fontSize: 15, fontWeight: 700,
                  cursor: "pointer", fontFamily: "'Syne',sans-serif",
                  boxShadow: "0 8px 32px rgba(0,0,0,0.15)", transition: "all 0.3s",
                  letterSpacing: "0.04em",
                }}
                  onMouseEnter={e => e.currentTarget.style.transform = "translateY(-3px)"}
                  onMouseLeave={e => e.currentTarget.style.transform = "translateY(0)"}>
                  Upload Sources →
                </button>
              </div>
            )}

            {status.state === "processing" && (
              <div style={{ marginBottom: 20, padding: "12px 18px", borderRadius: 14, background: "rgba(232,93,4,0.08)", color: "#E85D04", fontSize: 13, fontWeight: 700, fontFamily: "'DM Sans',sans-serif", display: "flex", alignItems: "center", gap: 10 }}>
                <span style={{ width: 14, height: 14, borderRadius: "50%", border: "2px solid rgba(232,93,4,0.3)", borderTopColor: "#E85D04", animation: "spin 0.8s linear infinite", display: "inline-block" }} />
                {status.stage || "Analyzing…"} (you can already ask questions below)
              </div>
            )}
            {status.state === "error" && (
              <div style={{ marginBottom: 20, padding: "12px 18px", borderRadius: 14, background: "rgba(239,68,68,0.08)", color: "#b91c1c", fontSize: 13, fontFamily: "'DM Sans',sans-serif" }}>
                ⚠ Analysis failed: {status.stage}
              </div>
            )}

            {sources.length > 0 && (
              <div>
                {/* Source tabs */}
                <div style={{
                  display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 36,
                  padding: "16px", background: "#fff", borderRadius: 18,
                  boxShadow: "0 2px 20px rgba(0,0,0,0.06)",
                }}>
                  {sources.length > 1 && (
                    <button onClick={() => setActiveTab("combined")} style={{
                      display: "flex", alignItems: "center", gap: 10,
                      padding: "12px 20px",
                      background: activeTab === "combined" ? "#1a1a1a" : "transparent",
                      border: "none", borderRadius: 12, cursor: "pointer",
                      transition: "all 0.3s cubic-bezier(0.34,1.2,0.64,1)",
                      transform: activeTab === "combined" ? "scale(1.03)" : "scale(1)",
                      boxShadow: activeTab === "combined" ? "0 6px 20px rgba(0,0,0,0.15)" : "none",
                    }}>
                      <span style={{ fontSize: 18 }}>🔗</span>
                      <div style={{ textAlign: "left" }}>
                        <div style={{ fontSize: 12, fontWeight: 700, color: activeTab === "combined" ? "#fff" : "#555", fontFamily: "'Syne',sans-serif", transition: "color 0.3s" }}>All Sources</div>
                        <div style={{ fontSize: 10, color: activeTab === "combined" ? "#E85D04" : "#aaa", fontFamily: "'DM Sans',sans-serif" }}>Combined analysis</div>
                      </div>
                    </button>
                  )}
                  {sources.map(s => (
                    <SourceTab key={s.id} source={s} active={activeTab === s.id} onClick={() => setActiveTab(s.id)} />
                  ))}
                </div>

                {/* Analysis content — single column, full width */}
                {activeTab === "combined" && (
                  combined
                    ? <>
                      <div style={{ marginBottom: 28, animation: "fadeUp 0.5s ease both" }}>
                        <p style={{ fontSize: 11, letterSpacing: "0.14em", fontWeight: 600, color: "#E85D04", textTransform: "uppercase", fontFamily: "'DM Sans',sans-serif", marginBottom: 8 }}>Combined Analysis</p>
                        <h2 style={{ fontSize: 28, fontWeight: 800, letterSpacing: "-0.5px", fontFamily: "'Syne',sans-serif" }}>
                          All {sources.length} sources, compared.
                        </h2>
                      </div>
                      {renderAnalysis(combined, 0, pairs, true)}
                    </>
                    : <div style={{ padding: "60px 0", textAlign: "center", color: "#bbb", fontFamily: "'DM Sans',sans-serif", fontSize: 15 }}>
                      Combined view needs 2+ sources.
                    </div>
                )}

                {activeTab !== "combined" && activeSrc && (
                  <>
                    <div style={{ marginBottom: 28, animation: "fadeUp 0.5s ease both" }}>
                      <p style={{ fontSize: 11, letterSpacing: "0.14em", fontWeight: 600, color: "#0077B6", textTransform: "uppercase", fontFamily: "'DM Sans',sans-serif", marginBottom: 8 }}>Individual Analysis</p>
                      <h2 style={{ fontSize: 28, fontWeight: 800, letterSpacing: "-0.5px", fontFamily: "'Syne',sans-serif", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                        {activeSrc.name}
                      </h2>
                    </div>
                    {renderAnalysis(activeSrc.analysis, 0, pairs.filter(p => p.claim_a.source_id === activeSrc.id || p.claim_b.source_id === activeSrc.id), false)}
                  </>
                )}
              </div>
            )}
          </main>
        </div>
      </div>
    </div>
  );
}
