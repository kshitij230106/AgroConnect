import { useState, useRef, useEffect } from "react";
import "./Chatbot.css";

const LANG_DATA = {
  en: {
    detecting: "📍 Detecting your location...",
    locationFound: (location) =>
      `📍 We detected you are in ${location}.\n\nWhich product are you looking for?\n\nSelect a product below or type its name.\n\n(Showing nearest retailers across Andhra Pradesh)`,
    locationFailed: "📍 Could not detect your location.\n\nPlease type your district name.",
    placeholder: "Type product, yes or no...",
    districtPlaceholder: "Type your district name...",
    products: "Products",
    actions: "Actions",
    logout: "Logout",
    send: "Send",
    noResponse: "No response received. Please try again.",
    noRasa: "Cannot connect to Rasa. Make sure it is running on port 5005.",
    productChips: ["Urea", "DAP", "Sulphate", "15-15-15-9", "20-20-0-13"],
    actionChips: ["Yes", "No", "Change District", "Help", "Bye"],
  },
  hi: {
    detecting: "📍 आपका स्थान पता किया जा रहा है...",
    locationFound: (location) =>
      `📍 हमने पता लगाया कि आप ${location} में हैं।\n\nआप कौन सा उत्पाद ढूंढ रहे हैं?\n\nनीचे से उत्पाद चुनें या नाम टाइप करें।\n\n(आंध्र प्रदेश के नजदीकी विक्रेता दिखाए जाएंगे)`,
    locationFailed: "📍 आपका स्थान पता नहीं चला।\n\nकृपया अपना जिला नाम टाइप करें।",
    placeholder: "उत्पाद, हाँ या नहीं टाइप करें...",
    districtPlaceholder: "अपना जिला नाम टाइप करें...",
    products: "उत्पाद",
    actions: "विकल्प",
    logout: "लॉगआउट",
    send: "भेजें",
    noResponse: "कोई जवाब नहीं मिला। कृपया फिर से कोशिश करें।",
    noRasa: "Rasa से कनेक्ट नहीं हो सका। कृपया सर्वर चालू करें।",
    productChips: ["यूरिया", "डीएपी", "सल्फेट", "15-15-15-9", "20-20-0-13"],
    actionChips: ["हाँ", "नहीं", "जिला बदलो", "मदद", "अलविदा"],
  },
};

async function getLocationFromGPS(lat, lon) {
  try {
    const res = await fetch(
      `https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lon}&format=json`,
      { headers: { "Accept-Language": "en" } }
    );
    const data = await res.json();
    const address = data.address || {};

    const location =
      address.county ||
      address.state_district ||
      address.district ||
      address.city ||
      address.town ||
      address.suburb ||
      address.village ||
      address.state ||
      "Unknown Location";

    return location;
  } catch {
    return null;
  }
}

function Chatbot({ onLogout, farmerName }) {
  const [lang, setLang] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [locationStatus, setLocationStatus] = useState("detecting");
  const [detectedLocation, setDetectedLocation] = useState(null);
  const [farmerLocation, setFarmerLocation] = useState(null);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    if (!lang) return;
    detectLocation();
  }, [lang]);

  const detectLocation = () => {
    const l = LANG_DATA[lang];
    setLocationStatus("detecting");
    setMessages([{ sender: "bot", text: l.detecting }]);

    if (!navigator.geolocation) {
      locationFailed();
      return;
    }

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const { latitude, longitude } = position.coords;

        // Save farmer GPS coordinates for tomorrow's distance calculation
        setFarmerLocation({ lat: latitude, lon: longitude });

        const location = await getLocationFromGPS(latitude, longitude);

        if (location) {
          setDetectedLocation(location);
          setLocationStatus("found");
          const l = LANG_DATA[lang];
          setMessages([{
            sender: "bot",
            text: l.locationFound(location),
          }]);
          // Tomorrow — pass lat/lon to Rasa for distance calculation
          // For now just show product chips
        } else {
          locationFailed();
        }
      },
      () => locationFailed(),
      { timeout: 8000 }
    );
  };

  const locationFailed = () => {
    const l = LANG_DATA[lang];
    setLocationStatus("failed");
    setMessages([{ sender: "bot", text: l.locationFailed }]);
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
            metadata: {
              farmer_lat: farmerLocation?.lat || null,
              farmer_lon: farmerLocation?.lon || null,
            },
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
            </div>
            <div style={{ display: "flex", gap: "12px", flexWrap: "wrap", justifyContent: "center" }}>
              <button
                className="chip action"
                style={{ fontSize: "16px", padding: "12px 24px" }}
                onClick={() => setLang("en")}
              >
                🇬🇧 English
              </button>
              <button
                className="chip action"
                style={{ fontSize: "16px", padding: "12px 24px" }}
                onClick={() => setLang("hi")}
              >
                🇮🇳 हिंदी
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
            <span className="header-sub">
              {detectedLocation
                ? `📍 ${detectedLocation}`
                : "Fertilizer Retailer Bot"}
            </span>
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
                    <div key={i}>{line || <>&nbsp;</>}</div>
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

        {locationStatus !== "detecting" && (
          <div className="quick-chips">
            {locationStatus === "found" && (
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
            )}
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
        )}

        <div className="input-area">
          <input
            type="text"
            placeholder={
              locationStatus === "failed"
                ? l.districtPlaceholder
                : l.placeholder
            }
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !loading) sendMessage();
            }}
            disabled={loading || locationStatus === "detecting"}
          />
          <button
            onClick={() => sendMessage()}
            disabled={loading || locationStatus === "detecting"}
          >
            {loading ? "..." : l.send}
          </button>
        </div>

      </div>
    </div>
  );
}

export default Chatbot;