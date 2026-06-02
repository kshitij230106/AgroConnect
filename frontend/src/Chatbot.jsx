import { useState, useRef, useEffect } from "react";
import "./Chatbot.css";

const LANG_DATA = {
  en: {welcome: (name) =>
   `Hello ${name}! Welcome to AgroConnect.\n\nWhich district are you from?\n\nSelect a district below or type its name.\n\nOr say NO to exit.`,
    placeholder: "Type district, product, yes or no...",
    districts: "Districts",
    products: "Products",
    actions: "Actions",
    logout: "Logout",
    send: "Send",
    noResponse: "No response received. Please try again.",
    noRasa: "Cannot connect to Rasa. Make sure it is running on port 5005.",
    districtChips: ["Anakapalli","Anantapur","Annamayya","Bapatla","Chittoor","East Godavari","Eluru","Guntur","Konaseema","Krishna","Kurnool","Nandyal","NTR","Palnadu","Prakasam","SPSR Nellore","Sri Sathya Sai","Tirupati","West Godavari"],
    productChips: ["Urea", "DAP", "Sulphate", "15-15-15-9", "20-20-0-13"],
    actionChips: ["Yes", "No", "Change District", "Help", "Bye"],
  },
  hi: {
    welcome: (name) =>
  `नमस्ते ${name}! AgroConnect में आपका स्वागत है।\n\nआप किस जिले से हैं?\n\nनीचे दिए गए जिले चुनें या नाम टाइप करें।`,
    placeholder: "जिला, उत्पाद, हाँ या नहीं टाइप करें...",
    districts: "जिले",
    products: "उत्पाद",
    actions: "विकल्प",
    logout: "लॉगआउट",
    send: "भेजें",
    noResponse: "कोई जवाब नहीं मिला। कृपया फिर से कोशिश करें।",
    noRasa: "Rasa से कनेक्ट नहीं हो सका। कृपया सर्वर चालू करें।",
    districtChips: ["अनाकापल्ली","अनंतपुर","अन्नमय्या","बापटला","चित्तूर","पूर्व गोदावरी","एलुरु","गुंटूर","कोनसीमा","कृष्णा","कुरनूल","नंद्याल","एनटीआर","पालनाडु","प्रकाशम","एसपीएसआर नेल्लोर","श्री सत्य साई","तिरुपति","पश्चिम गोदावरी"],
    productChips: ["यूरिया", "डीएपी", "सल्फेट", "15-15-15-9", "20-20-0-13"],
    actionChips: ["हाँ", "नहीं", "जिला बदलो", "मदद", "अलविदा"],
  },
  ta: {
    welcome: (name) =>
  `வணக்கம் ${name}! AgroConnect-க்கு வரவேற்கிறோம்.\n\nநீங்கள் எந்த மாவட்டத்தில் இருக்கிறீர்கள்?\n\nகீழே உள்ள மாவட்டத்தைத் தேர்ந்தெடுக்கவும் அல்லது பெயரை தட்டச்சு செய்யவும்.`,
    placeholder: "மாவட்டம், தயாரிப்பு, ஆம் அல்லது இல்லை என தட்டச்சு செய்யுங்கள்...",
    districts: "மாவட்டங்கள்",
    products: "தயாரிப்புகள்",
    actions: "விருப்பங்கள்",
    logout: "வெளியேறு",
    send: "அனுப்பு",
    noResponse: "பதில் இல்லை. மீண்டும் முயற்சிக்கவும்.",
    noRasa: "Rasa இணைக்க முடியவில்லை. சர்வரை இயக்கவும்.",
    districtChips: ["அனகாபல்லி","அனந்தபூர்","அன்னமையா","பாபட்லா","சித்தூர்","கிழக்கு கோதாவரி","எலூரு","குண்டூர்","கோனசீமா","கிருஷ்ணா","கர்நூல்","நந்த்யால்","என்டிஆர்","பால்நாடு","பிரகாசம்","எஸ்பிஎஸ்ஆர் நெல்லூர்","ஸ்ரீ சத்ய சாய்","திருப்பதி","மேற்கு கோதாவரி"],
    productChips: ["யூரியா", "டிஏபி", "சல்பேட்", "15-15-15-9", "20-20-0-13"],
    actionChips: ["ஆம்", "இல்லை", "மாவட்டம் மாற்று", "உதவி", "விடை"],
  },
};

function Chatbot({ onLogout, farmerName }) {
  const [lang, setLang] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const selectLanguage = (selectedLang) => {
    setLang(selectedLang);
    const l = LANG_DATA[selectedLang];
    setMessages([
      {
        sender: "bot",
        text: l.welcome(farmerName),
      },
    ]);
  };

  const sendMessage = async (overrideText) => {
    const userMessage = overrideText !== undefined ? overrideText : input;
    
    if (!userMessage.trim()) return;

    const l = LANG_DATA[lang];

    setMessages((prev) => [
      ...prev,
      { sender: "user", text: userMessage },
    ]);
    setInput("");
    setLoading(true);

    try {
      const response = await fetch(
        "http://localhost:5005/webhooks/rest/webhook",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            sender: farmerName || "user",
            message: userMessage,
          }),
        }
      );

      const data = await response.json();

      if (data && data.length > 0) {
        const combined = data.map((d) => d.text || "").join("\n");
        setMessages((prev) => [
          ...prev,
          { sender: "bot", text: combined },
        ]);
      } else {
        setMessages((prev) => [
          ...prev,
          { sender: "bot", text: l.noResponse },
        ]);
      }
    } catch {
      setMessages((prev) => [
        ...prev,
        { sender: "bot", text: l.noRasa },
      ]);
    } finally {
      setLoading(false);
    }
  };

  // Language selection screen
  if (!lang) {
    return (
      <div className="chat-wrapper">
        <div className="chat-container">
          <div className="chat-header">
            <div className="header-left">
              <div className="status-dot" />
              <span className="header-title">AgroConnect</span>
              <span className="header-sub">Fertilizer Retailer Bot</span>
            </div>
            <button className="logout-btn" onClick={onLogout}>
              Logout
            </button>
          </div>

          <div className="messages" style={{ justifyContent: "center", alignItems: "center", display: "flex", flexDirection: "column", gap: "16px", padding: "40px 20px" }}>
            <div className="bubble bot" style={{ textAlign: "center", fontSize: "16px" }}>
              <div>🌐 Select your language</div>
              <div>अपनी भाषा चुनें</div>
              <div>உங்கள் மொழியை தேர்ந்தெடுங்கள்</div>
            </div>
            <div style={{ display: "flex", gap: "12px", flexWrap: "wrap", justifyContent: "center" }}>
              <button
                className="chip action"
                style={{ fontSize: "16px", padding: "12px 24px" }}
                onClick={() => selectLanguage("en")}
              >
                🇬🇧 English
              </button>
              <button
                className="chip action"
                style={{ fontSize: "16px", padding: "12px 24px" }}
                onClick={() => selectLanguage("hi")}
              >
                🇮🇳 हिंदी
              </button>
              <button
                className="chip action"
                style={{ fontSize: "16px", padding: "12px 24px" }}
                onClick={() => selectLanguage("ta")}
              >
                🇮🇳 தமிழ்
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const l = LANG_DATA[lang];

  return (
    <div className="chat-wrapper">
      <div className="chat-container">

        <div className="chat-header">
          <div className="header-left">
            <div className="status-dot" />
            <span className="header-title">AgroConnect</span>
            <span className="header-sub">Fertilizer Retailer Bot</span>
          </div>
          <button className="logout-btn" onClick={onLogout}>
            {l.logout}
          </button>
        </div>

        <div className="messages">
          {messages.map((msg, index) => (
            <div key={index} className={"message-row " + msg.sender}>
              <div className={"avatar " + msg.sender}>
                {msg.sender === "bot"
                  ? "AG"
                  : (farmerName?.[0] || "U").toUpperCase()}
              </div>
              <div className={"bubble " + msg.sender}>
  {msg.text.includes("<table") ? (
    <div
      className="table-wrapper"
      dangerouslySetInnerHTML={{ __html: msg.text }}
    />
  ) : (
    msg.text.split("\n").map((line, i) => (
      <div key={i}>
        {line || <>&nbsp;</>}
      </div>
    ))
  )}
</div>
            </div>
          ))}

          {loading && (
            <div className="message-row bot">
              <div className="avatar bot">AG</div>
              <div className="bubble bot typing">
                <span /><span /><span />
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        <div className="quick-chips">
          <div className="chip-group">
            <span className="chip-label">{l.districts}</span>
            {l.districtChips.map((chip) => (
              <button
                key={chip}
                className="chip district"
                onClick={() => sendMessage(chip)}
                disabled={loading}
              >
                {chip}
              </button>
            ))}
          </div>
          <div className="chip-group">
            <span className="chip-label">{l.products}</span>
            {l.productChips.map((chip) => (
              <button
                key={chip}
                className="chip product"
                onClick={() => sendMessage(chip)}
                disabled={loading}
              >
                {chip}
              </button>
            ))}
          </div>
          <div className="chip-group">
            <span className="chip-label">{l.actions}</span>
            {l.actionChips.map((chip) => (
              <button
                key={chip}
                className="chip action"
                onClick={() => sendMessage(chip)}
                disabled={loading}
              >
                {chip}
              </button>
            ))}
          </div>
        </div>

        <div className="input-area">
          <input
            type="text"
            placeholder={l.placeholder}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !loading) sendMessage();
            }}
            disabled={loading}
          />
          <button onClick={() => sendMessage()} disabled={loading}>
            {loading ? "..." : l.send}
          </button>
        </div>

      </div>
    </div>
  );
}

export default Chatbot;