import { useState, useRef, useEffect } from "react";

const LANG_DATA = {
  en: {
    detecting: "📍 Detecting your location...",
    locationFound: (loc) =>
      `📍 You are in ${loc}.\n\nHow can I help you?\n\n👉 Type a product + district (e.g. "Urea in Bhadohi")\n👉 Type a product + "near me" (e.g. "Urea near me")\n👉 Or type just a product name to search nearby\n\nSelect from the chips below or type your query.`,
    locationFailed:
      "📍 Could not detect your location.\n\nYou can still search by district. Type a product + district (e.g. 'Urea in Bhadohi').",
    placeholder: "Try 'Urea near me' or 'DAP in Bhadohi'...",
    districtPlaceholder: "Try 'Urea near me' or 'DAP in Bhadohi'...",
    districts: "Districts",
    products: "Products",
    actions: "Actions",
    logout: "Logout",
    send: "Send",
    noResponse: "No response received. Please try again.",
    noRasa: "Cannot connect to Rasa. Make sure it is running on port 5005.",
    districtChips: [
      "Bhadohi","Pilibhit","Pratapgarh","Rae Bareli",
      "Rampur","Saharanpur","Sambhal","Sant Kabeer Nagar","Shahjahanpur",
    ],
    productChips: ["Urea","DAP","MOP","NPKS","SSP","FOM"],
    actionChips: ["Yes","No","Change District","Help","Bye"],
  },
  hi: {
    detecting: "📍 आपका स्थान पता किया जा रहा है...",
    locationFound: (loc) =>
      `📍 आप ${loc} में हैं।\n\nआप किस जिले में खोजना चाहते हैं?\n\nनीचे से जिला चुनें या नाम टाइप करें।`,
    locationFailed:
      "📍 स्थान पता नहीं चला।\n\nकृपया अपना जिला नाम टाइप करें।",
    placeholder: "जिला, उत्पाद या कमांड टाइप करें...",
    districtPlaceholder: "अपना जिला नाम टाइप करें...",
    districts: "जिले",
    products: "उत्पाद",
    actions: "विकल्प",
    logout: "लॉगआउट",
    send: "भेजें",
    noResponse: "कोई जवाब नहीं मिला। फिर कोशिश करें।",
    noRasa: "Rasa से कनेक्ट नहीं हो सका।",
    districtChips: [
      "भदोही","पीलीभीत","प्रतापगढ़","रायबरेली",
      "रामपुर","सहारनपुर","संभल","संत कबीर नगर","शाहजहांपुर",
    ],
    productChips: ["यूरिया","डीएपी","एमओपी","एनपीकेएस","एसएसपी","एफओएम"],
    actionChips: ["हाँ","नहीं","जिला बदलो","मदद","अलविदा"],
  },
};

const T = {
  bg:        "#0D1F12",
  surface:   "rgba(255,255,255,0.045)",
  surfaceHover: "rgba(255,255,255,0.07)",
  glass:     "rgba(14,30,16,0.82)",
  border:    "rgba(134,197,88,0.18)",
  borderMid: "rgba(134,197,88,0.32)",
  textPrimary:   "#EBF0E4",
  textSecondary: "#8FA882",
  textMuted:     "rgba(235,240,228,0.35)",
  green1: "#1A4D25",
  green2: "#26703A",
  green3: "#3A9E52",
  accent: "#7ED957",
  accentDim: "rgba(126,217,87,0.15)",
  wheat: "#C8A96E",
  wheatDim: "rgba(200,169,110,0.14)",
  gold: "#D4A843",
  chipDistrict: { bg:"rgba(58,158,82,0.14)", border:"rgba(58,158,82,0.38)", text:"#9DD670" },
  chipProduct:  { bg:"rgba(200,169,110,0.12)", border:"rgba(200,169,110,0.32)", text:"#C8A96E" },
  chipAction:   { bg:"rgba(212,168,67,0.12)", border:"rgba(212,168,67,0.28)", text:"#D4A843" },
};

const STYLES = `
  @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500;600&display=swap');
  *{box-sizing:border-box;margin:0;padding:0;}
  body{background:#0D1F12;font-family:'DM Sans',sans-serif;}
  @keyframes fadeUp{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}
  @keyframes blink{0%,100%{opacity:.3}50%{opacity:1}}
  @keyframes spin{to{transform:rotate(360deg)}}
  @keyframes glow{0%,100%{box-shadow:0 0 6px rgba(126,217,87,.5)}50%{box-shadow:0 0 14px rgba(126,217,87,.9)}}
  @keyframes panelIn{from{opacity:0;transform:translateY(-8px) scale(.97)}to{opacity:1;transform:translateY(0) scale(1)}}
  .msg-in{animation:fadeUp .28s ease forwards;}
  .dot1{animation:blink 1.2s .0s infinite;}
  .dot2{animation:blink 1.2s .2s infinite;}
  .dot3{animation:blink 1.2s .4s infinite;}
  .chip-btn:hover{transform:translateY(-2px);filter:brightness(1.18);}
  .chip-btn:disabled{opacity:.38;cursor:not-allowed;transform:none!important;}
  .lang-card:hover{transform:translateY(-5px);border-color:rgba(58,158,82,.6)!important;background:rgba(58,158,82,.12)!important;box-shadow:0 16px 48px rgba(26,77,37,.45)!important;}
  .send-btn:hover:not(:disabled){transform:translateY(-1px);filter:brightness(1.1);}
  .send-btn:disabled{opacity:.38;cursor:not-allowed;}
  .logout-hover:hover{background:rgba(200,169,110,.22)!important;color:#EBF0E4!important;border-color:rgba(200,169,110,.5)!important;}
  .input-field:focus{border-color:rgba(58,158,82,.7)!important;background:rgba(255,255,255,.07)!important;box-shadow:0 0 0 3px rgba(58,158,82,.12)!important;}
  .tbl-row:hover td{background:rgba(58,158,82,.07)!important;}
  .hist-item:hover{background:rgba(58,158,82,.1)!important;border-color:rgba(58,158,82,.25)!important;}
  .hist-clear:hover{color:#C8A96E!important;border-color:rgba(200,169,110,.4)!important;}
  .hist-close:hover{background:rgba(255,255,255,.1)!important;color:#EBF0E4!important;}
  .hist-btn:hover{background:rgba(200,169,110,.2)!important;border-color:rgba(200,169,110,.4)!important;}
  ::-webkit-scrollbar{width:3px;height:3px;}
  ::-webkit-scrollbar-track{background:transparent;}
  ::-webkit-scrollbar-thumb{background:rgba(126,217,87,.2);border-radius:99px;}
`;

const DISTRICTS = [
  "bhadohi","pilibhit","pratapgarh","rae bareli","rampur",
  "saharanpur","sambhal","sant kabeer nagar","shahjahanpur",
];

const PRODUCT_KEYWORDS = {
  urea:"Urea", dap:"DAP", mop:"MOP", npks:"NPKS", npk:"NPKS",
  ssp:"SSP", fom:"FOM",
  "यूरिया":"Urea","डीएपी":"DAP","एमओपी":"MOP",
  "एनपीकेएस":"NPKS","एसएसपी":"SSP","एफओएम":"FOM",
};

/**
 * NEAR_ME_PHRASES: patterns that trigger location-based search.
 * These are checked client-side so we can auto-reroute if Rasa misclassifies.
 */
const NEAR_ME_PHRASES = [
  "near me", "nearby", "close to me", "around me",
  "mere paas", "pas mein", "najdeeki", "najdiki",
  "aas paas", "side mein", "paas waala",
];

function hasNearMeIntent(message) {
  const lower = message.toLowerCase();
  return NEAR_ME_PHRASES.some(p => lower.includes(p));
}

function hasDistrictInMessage(message) {
  const lower = message.toLowerCase();
  return DISTRICTS.some(d => lower.includes(d));
}

function detectSearchIntent(message) {
  const lower = message.toLowerCase();
  let district = null;
  let product = null;
  for (const d of DISTRICTS) {
    if (lower.includes(d)) { district = d; break; }
  }
  for (const [kw, name] of Object.entries(PRODUCT_KEYWORDS)) {
    if (lower.includes(kw.toLowerCase()) || message.includes(kw)) {
      product = name; break;
    }
  }
  return { district, product };
}

function countResults(text) {
  const matches = text.match(/<tr>/g);
  return matches ? Math.max(0, matches.length - 1) : 0;
}

function formatDateTime(str) {
  try {
    const d = new Date(str.replace(" ", "T"));
    return d.toLocaleString("en-IN", {
      day:"2-digit", month:"short", year:"numeric",
      hour:"2-digit", minute:"2-digit",
    });
  } catch { return str; }
}

async function getLocationFromGPS(lat, lon) {
  try {
    const res = await fetch(
      `https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lon}&format=json`,
      { headers: { "Accept-Language": "en" } }
    );
    const data = await res.json();
    const a = data.address || {};
    return (
      a.county || a.state_district || a.district ||
      a.city || a.town || a.suburb || a.village ||
      a.state || "Unknown Location"
    );
  } catch { return null; }
}

function Avatar({ sender, name }) {
  const isBot = sender === "bot";
  return (
    <div style={{
      width:34, height:34, borderRadius:10, flexShrink:0,
      display:"flex", alignItems:"center", justifyContent:"center",
      fontSize:12, fontWeight:700, letterSpacing:.5,
      fontFamily:"'Syne',sans-serif",
      background: isBot
        ? `linear-gradient(135deg, ${T.green1}, ${T.green3})`
        : "linear-gradient(135deg, #3a2010, #6b3a1f)",
      color: T.textPrimary,
      boxShadow: isBot
        ? "0 3px 10px rgba(26,77,37,.5)"
        : "0 3px 10px rgba(60,20,8,.5)",
    }}>
      {isBot ? "AG" : (name?.[0] || "U").toUpperCase()}
    </div>
  );
}

function TypingBubble() {
  return (
    <div className="msg-in" style={{
      display:"flex", gap:10, alignItems:"flex-end",
      alignSelf:"flex-start", maxWidth:"80%",
    }}>
      <Avatar sender="bot" />
      <div style={{
        padding:"14px 18px", borderRadius:"4px 18px 18px 18px",
        background:T.surface, border:`1px solid ${T.border}`,
        display:"flex", gap:6, alignItems:"center",
      }}>
        {[0,1,2].map(i => (
          <span key={i} className={`dot${i+1}`} style={{
            width:7, height:7, borderRadius:"50%",
            background:T.textSecondary, display:"block",
          }}/>
        ))}
      </div>
    </div>
  );
}

function Bubble({ msg, farmerName }) {
  const isBot = msg.sender === "bot";
  return (
    <div className="msg-in" style={{
      display:"flex", gap:10, alignItems:"flex-end",
      alignSelf: isBot ? "flex-start" : "flex-end",
      flexDirection: isBot ? "row" : "row-reverse",
      maxWidth:"82%",
    }}>
      <Avatar sender={msg.sender} name={farmerName} />
      <div style={{
        padding:"12px 16px",
        borderRadius: isBot ? "4px 18px 18px 18px" : "18px 4px 18px 18px",
        background: isBot
          ? T.surface
          : `linear-gradient(135deg, ${T.green1}, ${T.green2})`,
        border: isBot ? `1px solid ${T.border}` : "none",
        boxShadow: isBot ? "none" : "0 4px 18px rgba(26,77,37,.4)",
        fontSize:13.5, lineHeight:1.75,
        color:T.textPrimary, wordBreak:"break-word",
      }}>
        {msg.isDetecting ? (
          <div style={{ display:"flex", alignItems:"center", gap:10 }}>
            <div style={{
              width:14, height:14,
              border:"2px solid rgba(126,217,87,.3)",
              borderTopColor:T.accent, borderRadius:"50%",
              animation:"spin .8s linear infinite", flexShrink:0,
            }}/>
            <span style={{ color:T.textSecondary, fontSize:13 }}>{msg.text}</span>
          </div>
        ) : msg.text?.includes("<table") ? (
          <div style={{ overflowX:"auto", borderRadius:10, border:`1px solid ${T.border}` }}
            dangerouslySetInnerHTML={{ __html: msg.text }}/>
        ) : (
          msg.text?.split("\n").map((line, i) => (
            <div key={i}>{line || <>&nbsp;</>}</div>
          ))
        )}
      </div>
    </div>
  );
}

function ChipRow({ label, chips, color, onSend, loading }) {
  return (
    <div style={{ display:"flex", alignItems:"center", gap:6, flexWrap:"wrap" }}>
      <span style={{
        fontSize:9, fontWeight:700, letterSpacing:1.4,
        textTransform:"uppercase", color:T.textMuted,
        width:52, flexShrink:0,
      }}>{label}</span>
      {chips.map(chip => (
        <button key={chip} className="chip-btn" disabled={loading}
          onClick={() => onSend(chip)}
          style={{
            padding:"4px 12px", borderRadius:999,
            fontSize:12, fontWeight:500, cursor:"pointer",
            transition:"all .18s ease", fontFamily:"'DM Sans',sans-serif",
            background:color.bg, border:`1px solid ${color.border}`,
            color:color.text,
          }}>
          {chip}
        </button>
      ))}
    </div>
  );
}

// ── History Panel ──
function HistoryPanel({ history, loading, onClose, onClear, onReplay }) {
  return (
    <div style={{
      position:"absolute", top:68, right:16,
      width:360, maxHeight:400,
      background:"rgba(10,20,12,0.97)",
      border:`1px solid ${T.border}`,
      borderRadius:16,
      boxShadow:"0 20px 60px rgba(0,0,0,.65), 0 0 0 1px rgba(255,255,255,.03) inset",
      zIndex:100,
      display:"flex", flexDirection:"column",
      overflow:"hidden",
      animation:"panelIn .25s ease forwards",
      backdropFilter:"blur(20px)",
    }}>
      {/* Panel header */}
      <div style={{
        display:"flex", alignItems:"center", justifyContent:"space-between",
        padding:"13px 16px",
        borderBottom:`1px solid ${T.border}`,
        flexShrink:0,
      }}>
        <span style={{ fontSize:13, fontWeight:600, color:T.wheat, letterSpacing:.3 }}>
          🕐 Search History
        </span>
        <div style={{ display:"flex", gap:8, alignItems:"center" }}>
          {history.length > 0 && (
            <button className="hist-clear"
              onClick={onClear}
              style={{
                fontSize:11, color:T.textMuted,
                background:"transparent",
                border:`1px solid rgba(200,169,110,.15)`,
                padding:"3px 10px", borderRadius:999,
                cursor:"pointer", transition:"all .2s ease",
                fontFamily:"'DM Sans',sans-serif",
              }}>
              Clear All
            </button>
          )}
          <button className="hist-close"
            onClick={onClose}
            style={{
              width:26, height:26,
              background:"rgba(255,255,255,.05)",
              border:`1px solid ${T.border}`,
              borderRadius:8, color:T.textMuted,
              cursor:"pointer", fontSize:12,
              display:"flex", alignItems:"center", justifyContent:"center",
              transition:"all .2s ease",
            }}>
            ✕
          </button>
        </div>
      </div>

      {/* List */}
      <div style={{ overflowY:"auto", flex:1, padding:8 }}>
        {loading ? (
          <div style={{
            textAlign:"center", color:T.textMuted,
            fontSize:13, padding:"32px 16px",
          }}>
            Loading...
          </div>
        ) : history.length === 0 ? (
          <div style={{
            textAlign:"center", color:T.textMuted,
            fontSize:13, padding:"32px 16px",
          }}>
            No search history yet.<br/>
            <span style={{ fontSize:11, opacity:.6 }}>
              Searches will appear here automatically.
            </span>
          </div>
        ) : (
          history.map((item, i) => (
            <div key={i} className="hist-item"
              onClick={() => onReplay(item)}
              style={{
                display:"flex", alignItems:"center",
                justifyContent:"space-between",
                padding:"10px 12px", borderRadius:10,
                cursor:"pointer",
                transition:"all .15s ease",
                border:"1px solid transparent",
                marginBottom:4, gap:12,
              }}>
              <div style={{ display:"flex", flexDirection:"column", gap:3, flex:1, minWidth:0 }}>
                <span style={{ fontSize:13, fontWeight:600, color:T.textPrimary }}>
                  {item.product}
                </span>
                <span style={{ fontSize:11.5, color:T.textSecondary }}>
                  📍 {item.district}
                </span>
              </div>
              <div style={{ display:"flex", flexDirection:"column", alignItems:"flex-end", gap:3, flexShrink:0 }}>
                <span style={{
                  fontSize:11, fontWeight:600, color:T.accent,
                  background:"rgba(126,217,87,.12)",
                  padding:"2px 8px", borderRadius:999,
                  border:"1px solid rgba(126,217,87,.2)",
                }}>
                  {item.results_count} retailers
                </span>
                <span style={{ fontSize:10, color:T.textMuted }}>
                  {formatDateTime(item.searched_at)}
                </span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

function LangScreen({ onSelect }) {
  return (
    <div style={{
      flex:1, display:"flex", flexDirection:"column",
      alignItems:"center", justifyContent:"center",
      gap:40, padding:"40px 32px",
    }}>
      <div style={{ position:"relative", width:88, height:88 }}>
        <div style={{
          width:88, height:88, borderRadius:"50%",
          background:`radial-gradient(circle, ${T.green2}55, transparent 70%)`,
          display:"flex", alignItems:"center", justifyContent:"center",
          fontSize:48,
        }}>🌾</div>
        <div style={{
          position:"absolute", bottom:0, right:0,
          width:28, height:28, borderRadius:"50%",
          background:`linear-gradient(135deg, ${T.green1}, ${T.green3})`,
          display:"flex", alignItems:"center", justifyContent:"center",
          fontSize:14, boxShadow:"0 0 12px rgba(126,217,87,.4)",
        }}>🌱</div>
      </div>

      <div style={{ textAlign:"center" }}>
        <h1 style={{
          fontFamily:"'Syne',sans-serif", fontWeight:800,
          fontSize:30, color:T.textPrimary, letterSpacing:-.5, marginBottom:10,
        }}>Welcome to AgroConnect</h1>
        <p style={{ fontSize:14, color:T.textSecondary, lineHeight:1.8 }}>
          Find fertilizer retailers near you<br/>
          <span style={{ opacity:.65 }}>अपने पास के उर्वरक विक्रेता खोजें</span>
        </p>
      </div>

      <div style={{ display:"flex", gap:16, flexWrap:"wrap", justifyContent:"center" }}>
        {[
          { code:"en", flag:"🇬🇧", name:"English", native:"Continue in English" },
          { code:"hi", flag:"🇮🇳", name:"हिंदी",   native:"हिंदी में जारी रखें" },
        ].map(l => (
          <button key={l.code} className="lang-card"
            onClick={() => onSelect(l.code)}
            style={{
              display:"flex", flexDirection:"column", alignItems:"center", gap:10,
              padding:"24px 36px", borderRadius:20, cursor:"pointer",
              transition:"all .28s ease",
              border:`1px solid ${T.border}`,
              background:T.surface,
              fontFamily:"'DM Sans',sans-serif",
              minWidth:150,
              boxShadow:"0 8px 32px rgba(0,0,0,.35)",
            }}>
            <span style={{ fontSize:38 }}>{l.flag}</span>
            <span style={{ fontSize:17, fontWeight:700, color:T.textPrimary, fontFamily:"'Syne',sans-serif" }}>{l.name}</span>
            <span style={{ fontSize:12, color:T.textSecondary }}>{l.native}</span>
          </button>
        ))}
      </div>

      <p style={{ fontSize:11, color:T.textMuted, letterSpacing:.5 }}>
        Powered by AI · Fertilizer Retailer Network
      </p>
    </div>
  );
}

function Wrapper({ children }) {
  return (
    <div style={{
      minHeight:"100vh", display:"flex",
      justifyContent:"center", alignItems:"center",
      padding:16,
      background:`
        radial-gradient(ellipse at 15% 50%, rgba(38,112,58,.35) 0%, transparent 55%),
        radial-gradient(ellipse at 85% 15%, rgba(126,217,87,.12) 0%, transparent 45%),
        radial-gradient(ellipse at 55% 85%, rgba(20,50,12,.7) 0%, transparent 50%),
        linear-gradient(150deg, #081408 0%, #0D1F12 45%, #091508 100%)
      `,
      position:"relative",
    }}>
      <div style={{
        position:"absolute", inset:0, pointerEvents:"none",
        backgroundImage:"radial-gradient(circle, rgba(126,217,87,.06) 1px, transparent 0)",
        backgroundSize:"28px 28px",
      }}/>
      {children}
    </div>
  );
}

function Shell({ children }) {
  return (
    <div style={{
      width:"100%", maxWidth:780,
      height:"94vh", display:"flex", flexDirection:"column",
      borderRadius:24,
      border:"1px solid rgba(134,197,88,.16)",
      background:"rgba(8,20,10,.75)",
      backdropFilter:"blur(24px)",
      overflow:"hidden",
      boxShadow:`
        0 0 0 1px rgba(255,255,255,.04) inset,
        0 40px 100px rgba(0,0,0,.7),
        0 0 80px rgba(38,112,58,.12)
      `,
      position:"relative",
    }}>
      {children}
    </div>
  );
}

// ── Main Chatbot ──
function Chatbot({ onLogout, farmerName, farmerPhone }) {
  const [lang, setLang] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [locationStatus, setLocationStatus] = useState("detecting");
  const [detectedLocation, setDetectedLocation] = useState(null);
  const [farmerLocation, setFarmerLocation] = useState(null);
  const [showHistory, setShowHistory] = useState(false);
  const [history, setHistory] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior:"smooth" });
  }, [messages, loading]);

  useEffect(() => { if (lang) detectLocation(); }, [lang]);

  // Load history from localStorage on mount
  useEffect(() => {
    const key = `history_${farmerPhone || "guest"}`;
    const local = localStorage.getItem(key);
    if (local) {
      try { setHistory(JSON.parse(local)); } catch {}
    }
  }, [farmerPhone]);

  const detectLocation = () => {
    const l = LANG_DATA[lang];
    setLocationStatus("detecting");
    setMessages([{ sender:"bot", text:l.detecting, isDetecting:true }]);
    if (!navigator.geolocation) { locationFailed(); return; }
    navigator.geolocation.getCurrentPosition(
      async ({ coords:{ latitude, longitude } }) => {
        setFarmerLocation({ lat:latitude, lon:longitude });
        const loc = await getLocationFromGPS(latitude, longitude);
        if (loc) {
          setDetectedLocation(loc);
          setLocationStatus("found");
          setMessages([{ sender:"bot", text:LANG_DATA[lang].locationFound(loc) }]);
        } else locationFailed();
      },
      () => locationFailed(),
      { timeout:8000 }
    );
  };

  const locationFailed = () => {
    setLocationStatus("failed");
    setMessages([{ sender:"bot", text:LANG_DATA[lang].locationFailed }]);
  };

  const saveToHistory = async (district, product, resultsCount) => {
    if (!district || !product) return;
    const record = {
      district: district.charAt(0).toUpperCase() + district.slice(1),
      product,
      results_count: resultsCount,
      searched_at: new Date().toISOString().replace("T"," ").substring(0,19),
    };
    const key = `history_${farmerPhone || "guest"}`;
    const updated = [record, ...history].slice(0, 20);
    setHistory(updated);
    localStorage.setItem(key, JSON.stringify(updated));

    // Save to DB
    if (farmerPhone) {
      try {
        await fetch("http://127.0.0.1:8000/history/save", {
          method:"POST",
          headers:{ "Content-Type":"application/json" },
          body: JSON.stringify({ phone:farmerPhone, ...record }),
        });
      } catch {}
    }
  };

  const loadHistoryFromDB = async () => {
    if (!farmerPhone) return;
    setHistoryLoading(true);
    try {
      const res = await fetch(`http://127.0.0.1:8000/history/${farmerPhone}`);
      const data = await res.json();
      if (Array.isArray(data) && data.length > 0) {
        setHistory(data);
        localStorage.setItem(`history_${farmerPhone}`, JSON.stringify(data));
      }
    } catch {} finally {
      setHistoryLoading(false);
    }
  };

  const clearHistory = async () => {
    setHistory([]);
    localStorage.removeItem(`history_${farmerPhone || "guest"}`);
    if (farmerPhone) {
      try {
        await fetch(`http://127.0.0.1:8000/history/${farmerPhone}`, { method:"DELETE" });
      } catch {}
    }
  };

  const openHistory = () => {
    setShowHistory(true);
    loadHistoryFromDB();
  };

  const sendMessage = async (overrideText) => {
    const userMessage = overrideText !== undefined ? overrideText : input;
    if (!userMessage.trim()) return;
    const l = LANG_DATA[lang];
    setMessages(p => [...p, { sender:"user", text:userMessage }]);
    setInput("");
    setLoading(true);
    try {
      const res = await fetch("http://localhost:5005/webhooks/custom_channel/webhook", {
        method:"POST",
        headers:{ "Content-Type":"application/json" },
        body: JSON.stringify({
          sender: farmerName || "user",
          message: userMessage,
          metadata: {
            farmer_lat: farmerLocation?.lat || null,
            farmer_lon: farmerLocation?.lon || null,
          },
        }),
      });
      const data = await res.json();
      if (data?.length > 0) {
        const combined = data.map(d => d.text || "").join("\n");
        setMessages(p => [...p, { sender:"bot", text:combined }]);

        // Save to history if it was a retailer search
        const { district, product } = detectSearchIntent(userMessage);
        if (district && product) {
          const count = countResults(combined);
          saveToHistory(district, product, count);
        }
      } else {
        setMessages(p => [...p, { sender:"bot", text:l.noResponse }]);
      }
    } catch {
      setMessages(p => [...p, { sender:"bot", text:l.noRasa }]);
    } finally {
      setLoading(false);
    }
  };

  // Language selection screen
  if (!lang) {
    return (
      <>
        <style>{STYLES}</style>
        <Wrapper>
          <Shell>
            <div style={{
              padding:"16px 22px",
              background:"linear-gradient(135deg, rgba(8,20,10,.98) 0%, rgba(22,50,18,.95) 100%)",
              borderBottom:`1px solid rgba(134,197,88,.14)`,
              display:"flex", alignItems:"center", justifyContent:"space-between",
              flexShrink:0,
            }}>
              <div style={{ display:"flex", alignItems:"center", gap:12 }}>
                <div style={{
                  width:40, height:40, borderRadius:12,
                  background:`linear-gradient(135deg, ${T.green1}, ${T.green3})`,
                  display:"flex", alignItems:"center", justifyContent:"center",
                  fontSize:19, boxShadow:"0 4px 14px rgba(58,158,82,.4)",
                }}>🌱</div>
                <div>
                  <div style={{
                    fontFamily:"'Syne',sans-serif", fontWeight:800,
                    fontSize:18, color:T.textPrimary,
                  }}>AgroConnect</div>
                  <div style={{
                    fontSize:10, color:T.textSecondary,
                    letterSpacing:1.2, textTransform:"uppercase",
                  }}>Fertilizer Retailer Network</div>
                </div>
              </div>
              <button className="logout-hover" onClick={onLogout} style={{
                background:T.wheatDim, color:T.wheat,
                border:`1px solid rgba(200,169,110,.28)`,
                padding:"7px 16px", borderRadius:20,
                cursor:"pointer", fontSize:12.5, fontWeight:600,
                fontFamily:"'DM Sans',sans-serif",
                transition:"all .22s ease",
              }}>Exit</button>
            </div>
            <LangScreen onSelect={setLang} />
          </Shell>
        </Wrapper>
      </>
    );
  }

  const l = LANG_DATA[lang];

  return (
    <>
      <style>{STYLES}</style>
      <Wrapper>
        <Shell>

          {/* Header */}
          <div style={{
            padding:"16px 22px",
            background:"linear-gradient(135deg, rgba(8,20,10,.98) 0%, rgba(22,50,18,.95) 100%)",
            borderBottom:`1px solid rgba(134,197,88,.14)`,
            display:"flex", alignItems:"center", justifyContent:"space-between",
            flexShrink:0, position:"relative", overflow:"hidden",
          }}>
            <div style={{
              position:"absolute", right:90, top:"50%",
              transform:"translateY(-50%)",
              fontSize:52, opacity:.05, pointerEvents:"none",
            }}>🌾</div>
            <div style={{
              position:"absolute", bottom:0, left:0, right:0, height:1,
              background:"linear-gradient(90deg,transparent,rgba(134,197,88,.4),transparent)",
            }}/>

            <div style={{ display:"flex", alignItems:"center", gap:12 }}>
              <div style={{
                width:8, height:8, borderRadius:"50%",
                background:"#7ED957", animation:"glow 2s infinite",
              }}/>
              <div style={{
                width:40, height:40, borderRadius:12, flexShrink:0,
                background:`linear-gradient(135deg, ${T.green1}, ${T.green3})`,
                display:"flex", alignItems:"center", justifyContent:"center",
                fontSize:19, boxShadow:"0 4px 14px rgba(58,158,82,.4)",
              }}>🌱</div>
              <div>
                <div style={{
                  fontFamily:"'Syne',sans-serif", fontWeight:800,
                  fontSize:18, color:T.textPrimary, letterSpacing:-.2, lineHeight:1,
                }}>AgroConnect</div>
                <div style={{
                  fontSize:10,
                  color: detectedLocation ? T.accent : T.textSecondary,
                  letterSpacing:1.2, textTransform:"uppercase", marginTop:3, fontWeight:600,
                }}>
                  {detectedLocation ? `📍 ${detectedLocation}` : "Fertilizer Retailer Network"}
                </div>
              </div>
            </div>

            {/* Right side — history btn + farmer badge + logout */}
            <div style={{ display:"flex", alignItems:"center", gap:10 }}>

              {/* History button */}
              <button className="hist-btn"
                onClick={openHistory}
                title="Search History"
                style={{
                  width:34, height:34, borderRadius:10,
                  background:"rgba(200,169,110,.08)",
                  border:`1px solid rgba(200,169,110,.2)`,
                  color:T.wheat, fontSize:15, cursor:"pointer",
                  display:"flex", alignItems:"center", justifyContent:"center",
                  transition:"all .2s ease",
                }}>
                🕐
              </button>

              {/* Farmer badge */}
              {farmerName && (
                <div style={{
                  display:"flex", alignItems:"center", gap:8,
                  padding:"5px 12px 5px 6px",
                  background:"rgba(200,169,110,.07)",
                  border:`1px solid rgba(200,169,110,.16)`,
                  borderRadius:999,
                }}>
                  <div style={{
                    width:24, height:24, borderRadius:"50%",
                    background:"linear-gradient(135deg, #3D1A06, #6B3A1A)",
                    display:"flex", alignItems:"center", justifyContent:"center",
                    fontSize:11, fontWeight:700, color:T.textPrimary,
                    fontFamily:"'Syne',sans-serif",
                  }}>
                    {(farmerName[0] || "F").toUpperCase()}
                  </div>
                  <span style={{
                    fontSize:12, color:T.wheat, fontWeight:500,
                    maxWidth:90, overflow:"hidden",
                    textOverflow:"ellipsis", whiteSpace:"nowrap",
                  }}>{farmerName}</span>
                </div>
              )}

              <button className="logout-hover" onClick={onLogout} style={{
                background:T.wheatDim, color:T.wheat,
                border:`1px solid rgba(200,169,110,.28)`,
                padding:"7px 16px", borderRadius:20,
                cursor:"pointer", fontSize:12.5, fontWeight:600,
                fontFamily:"'DM Sans',sans-serif",
                transition:"all .22s ease", letterSpacing:.3,
              }}>{l.logout}</button>
            </div>
          </div>

          {/* History Panel */}
          {showHistory && (
            <HistoryPanel
              history={history}
              loading={historyLoading}
              onClose={() => setShowHistory(false)}
              onClear={clearHistory}
              onReplay={(item) => {
                setShowHistory(false);
                sendMessage(`${item.product.toLowerCase()} in ${item.district.toLowerCase()}`);
              }}
            />
          )}

          {/* Messages */}
          <div style={{
            flex:1, overflowY:"auto",
            display:"flex", flexDirection:"column",
            gap:14, padding:"24px 20px",
          }}>
            <div style={{
              display:"flex", alignItems:"center", gap:12,
              color:T.textMuted, fontSize:10, letterSpacing:1.2,
              textTransform:"uppercase",
            }}>
              <div style={{ flex:1, height:1, background:`linear-gradient(90deg,transparent,${T.border})` }}/>
              Today
              <div style={{ flex:1, height:1, background:`linear-gradient(90deg,${T.border},transparent)` }}/>
            </div>

            {messages.map((msg, i) => (
              <Bubble key={i} msg={msg} farmerName={farmerName} />
            ))}

            {loading && <TypingBubble />}
            <div ref={bottomRef} />
          </div>

          {/* Chips */}
          {locationStatus !== "detecting" && (
            <div style={{
              borderTop:`1px solid ${T.border}`,
              background:T.glass, backdropFilter:"blur(12px)",
              padding:"10px 16px",
              display:"flex", flexDirection:"column", gap:8,
              flexShrink:0,
            }}>
              <ChipRow label={l.districts} chips={l.districtChips} color={T.chipDistrict} onSend={sendMessage} loading={loading}/>
              <ChipRow label={l.products}  chips={l.productChips}  color={T.chipProduct}  onSend={sendMessage} loading={loading}/>
              <ChipRow label={l.actions}   chips={l.actionChips}   color={T.chipAction}   onSend={sendMessage} loading={loading}/>
            </div>
          )}

          {/* Input */}
          <div style={{
            display:"flex", gap:10, padding:"14px 16px",
            borderTop:`1px solid ${T.border}`,
            background:T.glass, backdropFilter:"blur(12px)",
            flexShrink:0,
          }}>
            <input className="input-field"
              type="text"
              placeholder={locationStatus === "failed" ? l.districtPlaceholder : l.placeholder}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => { if (e.key === "Enter" && !loading) sendMessage(); }}
              disabled={loading || locationStatus === "detecting"}
              style={{
                flex:1, background:"rgba(255,255,255,.05)",
                border:`1px solid ${T.border}`, borderRadius:14,
                padding:"12px 16px", fontSize:13.5,
                color:T.textPrimary, outline:"none",
                fontFamily:"'DM Sans',sans-serif",
                transition:"all .22s ease",
              }}
            />
            <button className="send-btn"
              onClick={() => sendMessage()}
              disabled={loading || locationStatus === "detecting"}
              style={{
                background:`linear-gradient(135deg, ${T.green1}, ${T.green2})`,
                color:T.textPrimary, border:"none", borderRadius:14,
                padding:"12px 22px", fontWeight:600, fontSize:14,
                cursor:"pointer", fontFamily:"'DM Sans',sans-serif",
                transition:"all .22s ease",
                boxShadow:"0 4px 16px rgba(26,77,37,.45)",
                letterSpacing:.3, flexShrink:0,
              }}>
              {loading ? (
                <div style={{
                  width:16, height:16,
                  border:"2px solid rgba(235,240,228,.3)",
                  borderTopColor:"#EBF0E4", borderRadius:"50%",
                  animation:"spin .7s linear infinite",
                }}/>
              ) : l.send}
            </button>
          </div>

        </Shell>
      </Wrapper>
    </>
  );
}

export default Chatbot;
