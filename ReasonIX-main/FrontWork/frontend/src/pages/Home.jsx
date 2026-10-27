import { useNavigate } from "react-router-dom";
import { useEffect, useState, useRef } from "react";

const floaters = [
  { emoji:"⚡", x:8,  y:12, size:28, delay:0,   dur:3  },
  { emoji:"💥", x:85, y:8,  size:22, delay:1.2, dur:4  },
  { emoji:"🔍", x:92, y:55, size:26, delay:0.5, dur:3.5},
  { emoji:"🧩", x:5,  y:70, size:24, delay:2,   dur:4.5},
  { emoji:"❓", x:75, y:85, size:20, delay:0.8, dur:4  },
  { emoji:"⚡", x:45, y:5,  size:18, delay:3,   dur:2.5},
  { emoji:"💥", x:18, y:88, size:30, delay:1.5, dur:5  },
  { emoji:"🔍", x:60, y:92, size:16, delay:2.5, dur:3.5},
  { emoji:"🧩", x:95, y:28, size:22, delay:0.3, dur:4  },
  { emoji:"❓", x:30, y:15, size:19, delay:4,   dur:3  },
];

const features = [
  { tag:"01", title:"Analyze Anything", body:"PDFs, live URLs, raw text — feed it any content and watch it reason through it.", accent:"#E85D04" },
  { tag:"02", title:"Per-Source Breakdown", body:"Every source unpacked separately. Know exactly what each one says.", accent:"#7209B7" },
  { tag:"03", title:"Find Contradictions", body:"Surfaces where sources clash, agree, or quietly contradict each other.", accent:"#0077B6" },
  { tag:"04", title:"Ask Anything", body:"Query across all your sources at once. Get specific, grounded answers.", accent:"#2D6A4F" },
];

export default function Home() {
  const navigate = useNavigate();
  const [vis, setVis] = useState(false);
  const [hovered, setHovered] = useState(null);

  useEffect(() => { setTimeout(() => setVis(true), 80); }, []);

  return (
    <div style={{
      minHeight:"100vh", background:"#F5F0E8",
      fontFamily:"'Syne','DM Serif Display',serif",
      color:"#1a1a1a", overflowX:"hidden", position:"relative",
    }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500&display=swap');
        @keyframes floatY { 0%,100%{transform:translateY(0px) rotate(0deg)} 50%{transform:translateY(-22px) rotate(8deg)} }
        @keyframes floatY2 { 0%,100%{transform:translateY(0px) rotate(0deg)} 50%{transform:translateY(-18px) rotate(-6deg)} }
        @keyframes fadeUp { from{opacity:0;transform:translateY(32px)} to{opacity:1;transform:translateY(0)} }
        @keyframes fadeIn { from{opacity:0} to{opacity:1} }
        @keyframes cardPop { from{opacity:0;transform:translateY(24px) scale(0.97)} to{opacity:1;transform:translateY(0) scale(1)} }
        @keyframes pulse { 0%,100%{transform:scale(1)} 50%{transform:scale(1.04)} }
        .hero-btn:hover { transform:translateY(-3px) !important; box-shadow:0 16px 48px rgba(232,93,4,0.35) !important; }
        .feat-card:hover .feat-num { transform:scale(1.3) rotate(-8deg); }
        * { box-sizing:border-box; margin:0; padding:0; }
      `}</style>

      {/* floating emojis */}
      {floaters.map((f,i) => (
        <div key={i} style={{
          position:"fixed", left:`${f.x}%`, top:`${f.y}%`,
          fontSize:f.size, opacity:0.18, pointerEvents:"none", zIndex:0,
          animation:`${i%2===0?"floatY":"floatY2"} ${f.dur}s ${f.delay}s ease-in-out infinite`,
          filter:"grayscale(0.2)",
        }}>{f.emoji}</div>
      ))}

      {/* content */}
      <div style={{ position:"relative", zIndex:1 }}>

        {/* HERO */}
        <section style={{
          minHeight:"100vh", display:"flex", flexDirection:"column",
          alignItems:"center", justifyContent:"center",
          padding:"80px 24px 60px", textAlign:"center",
        }}>
          {/* badge */}
          <div style={{
            opacity: vis?1:0, animation: vis?"fadeIn 0.6s ease both":"none",
            display:"inline-flex", alignItems:"center", gap:8,
            background:"#1a1a1a", color:"#F5F0E8", borderRadius:100,
            padding:"7px 18px", fontSize:11, fontFamily:"'DM Sans',sans-serif",
            fontWeight:500, letterSpacing:"0.12em", textTransform:"uppercase", marginBottom:40,
          }}>
            <span style={{ width:6, height:6, borderRadius:"50%", background:"#E85D04",
              animation:"pulse 2s infinite", display:"inline-block" }} />
            AI Document Intelligence
          </div>

          {/* big logo/name */}
          <h1 style={{
            fontSize:"clamp(52px,10vw,120px)", fontWeight:800, lineHeight:1,
            letterSpacing:"-4px", marginBottom:32,
            fontFamily:"'Syne',sans-serif",
            opacity:vis?1:0,
            animation: vis?"fadeUp 0.8s 0.1s ease both":"none",
            display:"flex", alignItems:"baseline", justifyContent:"center", gap:4,
          }}>
            <span style={{ color:"#1a1a1a" }}>Reason</span>
            <span style={{
              WebkitTextStroke:"3px #1a1a1a", color:"transparent",
              fontStyle:"italic", fontFamily:"'DM Serif Display',serif",
            }}>IX</span>
          </h1>

          {/* tagline */}
          <p style={{
            fontSize:"clamp(16px,2.5vw,22px)", color:"#555", maxWidth:560,
            lineHeight:1.65, marginBottom:52,
            fontFamily:"'DM Sans',sans-serif", fontWeight:300,
            opacity:vis?1:0, animation:vis?"fadeUp 0.8s 0.25s ease both":"none",
          }}>
            Upload documents, articles & data. Surface contradictions.<br />
            Understand what your sources actually say.
          </p>

          {/* CTA */}
          <button className="hero-btn" onClick={() => navigate("/input")} style={{
            background:"#E85D04", color:"#fff", border:"none",
            borderRadius:100, padding:"18px 52px",
            fontSize:16, fontWeight:700, cursor:"pointer",
            fontFamily:"'Syne',sans-serif", letterSpacing:"0.04em",
            boxShadow:"0 8px 32px rgba(232,93,4,0.25)",
            transition:"all 0.3s cubic-bezier(0.34,1.56,0.64,1)",
            opacity:vis?1:0, animation:vis?"fadeUp 0.8s 0.4s ease both":"none",
          }}>
            Start Analyzing →
          </button>

          {/* scroll hint */}
          <div style={{
            position:"absolute", bottom:40,
            display:"flex", flexDirection:"column", alignItems:"center", gap:8,
            opacity:0.4, animation:"fadeIn 1s 1.5s ease both", animationFillMode:"both",
          }}>
            <span style={{ fontSize:11, letterSpacing:"0.15em", fontFamily:"'DM Sans',sans-serif" }}>SCROLL</span>
            <div style={{ width:1, height:40, background:"#1a1a1a", animation:"pulse 2s infinite" }} />
          </div>
        </section>

        {/* FEATURES */}
        <section style={{ padding:"80px 40px 120px", maxWidth:1100, margin:"0 auto" }}>
          <div style={{
            display:"flex", alignItems:"baseline", gap:20, marginBottom:64,
            borderTop:"2px solid #1a1a1a", paddingTop:32,
          }}>
            <span style={{ fontSize:11, letterSpacing:"0.18em", opacity:0.4,
              fontFamily:"'DM Sans',sans-serif", fontWeight:500 }}>WHAT IT DOES</span>
            <div style={{ flex:1, height:1, background:"#1a1a1a", opacity:0.12 }} />
          </div>

          <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fit,minmax(240px,1fr))", gap:2 }}>
            {features.map((f,i) => (
              <div key={i} className="feat-card"
                onMouseEnter={() => setHovered(i)}
                onMouseLeave={() => setHovered(null)}
                style={{
                  background: hovered===i ? "#1a1a1a" : "#EDE8DF",
                  padding:"36px 32px", cursor:"default",
                  transition:"background 0.35s ease, transform 0.35s ease",
                  transform: hovered===i ? "translateY(-6px) scale(1.01)" : "none",
                  animation:`cardPop 0.6s ${0.1*i}s ease both`,
                  borderLeft:`4px solid ${f.accent}`,
                  position:"relative", overflow:"hidden",
                }}>
                <div className="feat-num" style={{
                  fontSize:64, fontWeight:800, color:f.accent, opacity: hovered===i?0.25:0.12,
                  position:"absolute", top:-10, right:16, lineHeight:1,
                  fontFamily:"'Syne',sans-serif",
                  transition:"all 0.3s ease",
                }}>{f.tag}</div>
                <p style={{
                  fontSize:11, letterSpacing:"0.14em", fontWeight:600,
                  color: hovered===i?"rgba(255,255,255,0.4)":"rgba(0,0,0,0.35)",
                  fontFamily:"'DM Sans',sans-serif", marginBottom:14,
                  textTransform:"uppercase",
                }}>Feature {f.tag}</p>
                <h3 style={{
                  fontSize:24, fontWeight:800, marginBottom:14, letterSpacing:"-0.5px",
                  color: hovered===i ? "#fff" : "#1a1a1a",
                  fontFamily:"'Syne',sans-serif",
                  transition:"color 0.3s",
                }}>{f.title}</h3>
                <p style={{
                  fontSize:14, lineHeight:1.75,
                  color: hovered===i ? "rgba(255,255,255,0.65)" : "#666",
                  fontFamily:"'DM Sans',sans-serif", fontWeight:300,
                  transition:"color 0.3s",
                }}>{f.body}</p>
              </div>
            ))}
          </div>
        </section>

        {/* BOTTOM CTA */}
        <section style={{
          background:"#1a1a1a", color:"#F5F0E8",
          padding:"100px 40px", textAlign:"center",
        }}>
          <p style={{ fontSize:11, letterSpacing:"0.18em", opacity:0.4, marginBottom:24,
            fontFamily:"'DM Sans',sans-serif" }}>READY?</p>
          <h2 style={{ fontSize:"clamp(40px,7vw,80px)", fontWeight:800, letterSpacing:"-2px",
            marginBottom:40, fontFamily:"'Syne',sans-serif", lineHeight:1 }}>
            Stop guessing.<br />
            <em style={{ fontFamily:"'DM Serif Display',serif", fontWeight:400 }}>Start knowing.</em>
          </h2>
          <button className="hero-btn" onClick={() => navigate("/input")} style={{
            background:"#E85D04", color:"#fff", border:"none",
            borderRadius:100, padding:"18px 52px",
            fontSize:16, fontWeight:700, cursor:"pointer",
            fontFamily:"'Syne',sans-serif",
            boxShadow:"0 8px 32px rgba(232,93,4,0.35)",
            transition:"all 0.3s cubic-bezier(0.34,1.56,0.64,1)",
          }}>Analyze Your First Source →</button>
        </section>
      </div>
    </div>
  );
}
