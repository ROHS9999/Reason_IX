import { useState, useRef } from "react";
import { apiFetch } from "../config";
import { useNavigate } from "react-router-dom";

const floaters = [
  { emoji:"📄", x:5,  y:20, size:24, delay:0,   dur:8  },
  { emoji:"🌐", x:90, y:15, size:20, delay:1,   dur:7  },
  { emoji:"✍️", x:88, y:75, size:22, delay:2,   dur:9  },
  { emoji:"📎", x:3,  y:80, size:18, delay:0.5, dur:10 },
  { emoji:"🔎", x:50, y:4,  size:16, delay:1.5, dur:6  },
];

const TABS = [
  { id:"pdf",  icon:"📄", label:"PDF Files",  sub:"Upload any PDF documents"  },
  { id:"url",  icon:"🌐", label:"URLs",       sub:"Import from the web"     },
  { id:"text", icon:"✍️", label:"Raw Text",  sub:"Paste any content"       },
];

export default function Input() {
  const navigate = useNavigate();
  const fileRef  = useRef();
  const [tab,       setTab]       = useState("pdf");
  const [files,     setFiles]     = useState([]);
  const [urls,      setUrls]      = useState([""]);
  const [textInput, setTextInput] = useState("");
  const [loading,   setLoading]   = useState(false);
  const [error,     setError]     = useState("");
  const [dragOver,  setDragOver]  = useState(false);

  const hasInput = files.length > 0 || urls.some(u=>u.trim()) || textInput.trim();

  function onDrop(e) {
    e.preventDefault(); setDragOver(false);
    setFiles(p=>[...p,...Array.from(e.dataTransfer.files).filter(f=>f.type==="application/pdf")]);
  }

  async function handleProceed() {
    if (!hasInput) return;
    setLoading(true); setError("");
    try {
      const form = new FormData();
      files.forEach(f => form.append("files", f));
      form.append("url_input", urls.filter(u=>u.trim()).join(","));
      form.append("text_input", textInput);
      // this page = a fresh start, so wipe whatever the backend still holds from earlier uploads
      await apiFetch(`/clear/`, { method:"POST" });
      const res  = await apiFetch(`/upload/`, { method:"POST", body:form });
      const data = await res.json();
      if (data.error) { setError(data.error); setLoading(false); return; }
      sessionStorage.setItem("analysisResult", JSON.stringify(data));
      navigate("/dashboard");
    } catch(e) {
      setError("Cannot reach backend. Is it running on port 8000?");
      setLoading(false);
    }
  }

  const inp = {
    width:"100%", background:"#fff",
    border:"2px solid #e8e2d9", borderRadius:12,
    color:"#1a1a1a", padding:"12px 16px", fontSize:14,
    outline:"none", fontFamily:"'DM Sans',sans-serif",
    transition:"border-color 0.2s",
  };

  return (
    <div style={{ minHeight:"100vh", background:"#F5F0E8",
      fontFamily:"'Syne','DM Sans',sans-serif", color:"#1a1a1a",
      position:"relative", overflowX:"hidden" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500&display=swap');
        @keyframes floatY  { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-20px) rotate(6deg)} }
        @keyframes floatY2 { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-16px) rotate(-5deg)} }
        @keyframes slideIn { from{opacity:0;transform:translateX(-20px)} to{opacity:1;transform:translateX(0)} }
        @keyframes popIn   { from{opacity:0;transform:scale(0.92)} to{opacity:1;transform:scale(1)} }
        @keyframes spin    { to{transform:rotate(360deg)} }
        @keyframes shimmer { 0%{background-position:-400px 0} 100%{background-position:400px 0} }
        .tab-btn:hover { background:#fff !important; transform:translateY(-2px); }
        .upload-btn:hover:not(:disabled) { transform:translateY(-3px) !important; box-shadow:0 20px 60px rgba(232,93,4,0.4) !important; }
        input:focus,textarea:focus { border-color:#E85D04 !important; }
        * { box-sizing:border-box; margin:0; padding:0; }
      `}</style>

      {/* Floaters */}
      {floaters.map((f,i)=>(
        <div key={i} style={{ position:"fixed",left:`${f.x}%`,top:`${f.y}%`,
          fontSize:f.size,opacity:0.15,pointerEvents:"none",zIndex:0,
          animation:`${i%2===0?"floatY":"floatY2"} ${f.dur}s ${f.delay}s ease-in-out infinite`
        }}>{f.emoji}</div>
      ))}

      <div style={{ position:"relative",zIndex:1,maxWidth:700,margin:"0 auto",padding:"60px 24px 80px" }}>

        {/* Back link */}
        <button onClick={()=>navigate("/")} style={{
          background:"none",border:"none",cursor:"pointer",
          display:"flex",alignItems:"center",gap:8,
          fontSize:13,color:"#888",fontFamily:"'DM Sans',sans-serif",
          marginBottom:52,padding:0,transition:"color 0.2s",
        }}
          onMouseEnter={e=>e.currentTarget.style.color="#1a1a1a"}
          onMouseLeave={e=>e.currentTarget.style.color="#888"}>
          ← Back to home
        </button>

        {/* Title block */}
        <div style={{ marginBottom:52, animation:"slideIn 0.6s ease both" }}>
          <div style={{ fontSize:11,letterSpacing:"0.18em",fontWeight:600,
            color:"#E85D04",textTransform:"uppercase",fontFamily:"'DM Sans',sans-serif",
            marginBottom:12 }}>Step 1 of 2</div>
          <h1 style={{ fontSize:"clamp(36px,7vw,64px)",fontWeight:800,
            letterSpacing:"-2px",lineHeight:1,fontFamily:"'Syne',sans-serif",
            marginBottom:16 }}>
            Add your<br />
            <span style={{ fontStyle:"italic",fontFamily:"'DM Serif Display',serif",fontWeight:400 }}>sources.</span>
          </h1>
          <p style={{ fontSize:15,color:"#777",lineHeight:1.7,maxWidth:460,
            fontFamily:"'DM Sans',sans-serif",fontWeight:300 }}>
            Drop in PDFs, paste URLs, or write raw text. Mix and match as many as you want.
          </p>
        </div>

        {/* Tab selector */}
        <div style={{ display:"grid",gridTemplateColumns:"1fr 1fr 1fr",gap:10,marginBottom:24 }}>
          {TABS.map((t,i)=>(
            <button key={t.id} className="tab-btn" onClick={()=>setTab(t.id)} style={{
              background: tab===t.id?"#1a1a1a":"#EDE8DF",
              border:"none",borderRadius:16,padding:"18px 16px",cursor:"pointer",
              textAlign:"left",transition:"all 0.25s cubic-bezier(0.34,1.56,0.64,1)",
              animation:`popIn 0.5s ${0.08*i}s ease both`,
              boxShadow: tab===t.id?"0 8px 32px rgba(0,0,0,0.2)":"none",
            }}>
              <span style={{ fontSize:22,display:"block",marginBottom:10 }}>{t.icon}</span>
              <span style={{ fontSize:14,fontWeight:700,color:tab===t.id?"#fff":"#1a1a1a",
                display:"block",marginBottom:4,fontFamily:"'Syne',sans-serif" }}>{t.label}</span>
              <span style={{ fontSize:11,color:tab===t.id?"rgba(255,255,255,0.5)":"#999",
                fontFamily:"'DM Sans',sans-serif",fontWeight:400 }}>{t.sub}</span>
            </button>
          ))}
        </div>

        {/* Input area */}
        <div style={{ background:"#fff",borderRadius:24,padding:32,
          boxShadow:"0 4px 40px rgba(0,0,0,0.07)",
          animation:"popIn 0.5s 0.2s ease both" }}>

          {tab==="pdf" && <>
            <div onDrop={onDrop}
              onDragOver={e=>{e.preventDefault();setDragOver(true)}}
              onDragLeave={()=>setDragOver(false)}
              onClick={()=>fileRef.current.click()} style={{
                border:`2.5px dashed ${dragOver?"#E85D04":"#ddd"}`,
                borderRadius:18, padding:"52px 24px", textAlign:"center",
                cursor:"pointer", background:dragOver?"rgba(232,93,4,0.04)":"#fafafa",
                transition:"all 0.25s",
              }}>
              <input ref={fileRef} type="file" accept=".pdf" multiple style={{display:"none"}}
                onChange={e=>setFiles(p=>[...p,...Array.from(e.target.files)])} />
              <div style={{ fontSize:40,marginBottom:12 }}>📄</div>
              <p style={{ fontSize:15,fontWeight:700,color:"#1a1a1a",marginBottom:6,
                fontFamily:"'Syne',sans-serif" }}>Drop PDFs here</p>
              <p style={{ fontSize:13,color:"#aaa",fontFamily:"'DM Sans',sans-serif" }}>or click to browse · multiple files OK</p>
            </div>
            {files.length>0&&(
              <div style={{ marginTop:16,display:"flex",flexDirection:"column",gap:8 }}>
                {files.map((f,i)=>(
                  <div key={i} style={{ display:"flex",alignItems:"center",gap:12,
                    background:"#F5F0E8",borderRadius:12,padding:"12px 16px",
                    animation:"slideIn 0.3s ease both" }}>
                    <span style={{ fontSize:18 }}>📄</span>
                    <span style={{ flex:1,fontSize:13,fontFamily:"'DM Sans',sans-serif",
                      color:"#333",overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap" }}>{f.name}</span>
                    <span style={{ fontSize:11,color:"#aaa",fontFamily:"'DM Sans',sans-serif" }}>
                      {(f.size/1024).toFixed(0)}KB</span>
                    <button onClick={e=>{e.stopPropagation();setFiles(p=>p.filter((_,j)=>j!==i))}}
                      style={{ background:"none",border:"none",color:"#ccc",cursor:"pointer",
                        fontSize:16,transition:"color 0.2s",padding:0 }}
                      onMouseEnter={e=>e.currentTarget.style.color="#E85D04"}
                      onMouseLeave={e=>e.currentTarget.style.color="#ccc"}>✕</button>
                  </div>
                ))}
              </div>
            )}
          </>}

          {tab==="url"&&(
            <div style={{ display:"flex",flexDirection:"column",gap:12 }}>
              <p style={{ fontSize:13,color:"#aaa",fontFamily:"'DM Sans',sans-serif",marginBottom:4 }}>
                Each URL becomes a separate source with its own analysis
              </p>
              {urls.map((u,i)=>(
                <div key={i} style={{ display:"flex",gap:10,animation:"slideIn 0.3s ease both" }}>
                  <input value={u} onChange={e=>setUrls(us=>us.map((x,j)=>j===i?e.target.value:x))}
                    placeholder="https://example.com/paper"
                    style={{ ...inp, flex:1 }} />
                  {urls.length>1&&(
                    <button onClick={()=>setUrls(us=>us.filter((_,j)=>j!==i))}
                      style={{ background:"none",border:"2px solid #e8e2d9",borderRadius:10,
                        color:"#ccc",cursor:"pointer",padding:"0 14px",fontSize:16,transition:"all 0.2s" }}
                      onMouseEnter={e=>{e.currentTarget.style.borderColor="#E85D04";e.currentTarget.style.color="#E85D04";}}
                      onMouseLeave={e=>{e.currentTarget.style.borderColor="#e8e2d9";e.currentTarget.style.color="#ccc";}}>✕</button>
                  )}
                </div>
              ))}
              <button onClick={()=>setUrls(u=>[...u,""])} style={{
                background:"none",border:"2px dashed #ddd",borderRadius:12,
                padding:"12px",fontSize:13,color:"#aaa",cursor:"pointer",
                fontFamily:"'DM Sans',sans-serif",transition:"all 0.2s",
              }}
                onMouseEnter={e=>{e.currentTarget.style.borderColor="#E85D04";e.currentTarget.style.color="#E85D04";}}
                onMouseLeave={e=>{e.currentTarget.style.borderColor="#ddd";e.currentTarget.style.color="#aaa";}}>
                + Add another URL
              </button>
            </div>
          )}

          {tab==="text"&&(
            <div>
              <p style={{ fontSize:13,color:"#aaa",fontFamily:"'DM Sans',sans-serif",marginBottom:12 }}>
                Paste articles, notes, abstracts — anything text-based
              </p>
              <textarea value={textInput} onChange={e=>setTextInput(e.target.value)}
                placeholder="Paste your content here…" rows={10}
                style={{ ...inp,resize:"vertical",lineHeight:1.7 }} />
              {textInput&&(
                <p style={{ fontSize:11,color:"#bbb",textAlign:"right",marginTop:6,
                  fontFamily:"'DM Sans',sans-serif" }}>
                  {textInput.split(/\s+/).filter(Boolean).length} words
                </p>
              )}
            </div>
          )}
        </div>

        {/* Source preview chips */}
        {hasInput&&(
          <div style={{ marginTop:20,display:"flex",flexWrap:"wrap",gap:8,
            animation:"popIn 0.4s ease both" }}>
            {files.map((f,i)=>(
              <span key={i} style={{ fontSize:12,padding:"6px 14px",borderRadius:100,
                background:"#1a1a1a",color:"#F5F0E8",fontFamily:"'DM Sans',sans-serif",
                fontWeight:500,display:"flex",alignItems:"center",gap:6 }}>
                📄 {f.name.length>20?f.name.slice(0,20)+"…":f.name}
              </span>
            ))}
            {urls.filter(u=>u.trim()).map((u,i)=>{
              let host=u;
              try{host=new URL(u.startsWith("http")?u:"https://"+u).hostname;}catch(e){}
              return(
                <span key={i} style={{ fontSize:12,padding:"6px 14px",borderRadius:100,
                  background:"#E85D04",color:"#fff",fontFamily:"'DM Sans',sans-serif",fontWeight:500,
                  display:"flex",alignItems:"center",gap:6 }}>🌐 {host}</span>
              );
            })}
            {textInput.trim()&&(
              <span style={{ fontSize:12,padding:"6px 14px",borderRadius:100,
                background:"#7209B7",color:"#fff",fontFamily:"'DM Sans',sans-serif",fontWeight:500,
                display:"flex",alignItems:"center",gap:6 }}>
                ✍️ Text · {textInput.split(/\s+/).filter(Boolean).length}w
              </span>
            )}
          </div>
        )}

        {error&&(
          <div style={{ marginTop:16,padding:"14px 18px",borderRadius:14,
            background:"rgba(239,68,68,0.08)",border:"2px solid rgba(239,68,68,0.2)",
            color:"#dc2626",fontSize:13,fontFamily:"'DM Sans',sans-serif" }}>{error}</div>
        )}

        {/* Proceed button */}
        <button className="upload-btn" onClick={handleProceed} disabled={loading||!hasInput}
          style={{
            width:"100%",marginTop:28,padding:"18px",borderRadius:16,
            background:hasInput&&!loading?"#1a1a1a":"#ccc",
            border:"none",color:"#F5F0E8",
            fontSize:16,fontWeight:700,cursor:hasInput&&!loading?"pointer":"not-allowed",
            fontFamily:"'Syne',sans-serif",letterSpacing:"0.04em",
            transition:"all 0.3s cubic-bezier(0.34,1.56,0.64,1)",
            boxShadow:hasInput&&!loading?"0 8px 40px rgba(0,0,0,0.2)":"none",
            display:"flex",alignItems:"center",justifyContent:"center",gap:12,
          }}>
          {loading ? (
            <><span style={{ width:18,height:18,borderRadius:"50%",
              border:"2.5px solid rgba(255,255,255,0.3)",borderTopColor:"#fff",
              animation:"spin 0.8s linear infinite",display:"inline-block" }} />
            Analyzing your sources…</>
          ) : "Analyze & See Results →"}
        </button>
      </div>
    </div>
  );
}
