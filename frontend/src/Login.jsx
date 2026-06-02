import { useState } from "react";
import "./styles.css";

function Login({ setIsLoggedIn, setPage }) {
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");

  const handleLogin = async () => {
    if (!phone || !password) {
      alert("Please fill all fields");
      return;
    }

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/login",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            name: "",
            phone,
            password,
          }),
        }
      );

      const data = await response.json();

      if (data.message === "Login successful") {
        localStorage.setItem("loggedIn", "true");
        setIsLoggedIn(true);
      } else {
        alert(data.message);
      }
    } catch (error) {
      alert("Server error. Make sure backend is running.");
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h1>🌱 AgroConnect</h1>
        <p style={{ textAlign: "center", color: "#94a3b8", marginBottom: "20px" }}>
          Farmer Login
        </p>

        <input
          type="text"
          placeholder="Mobile Number"
          value={phone}
          onChange={(e) => setPhone(e.target.value)}
        />

        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") handleLogin();
          }}
        />

        <button className="primary-btn" onClick={handleLogin}>
          Login
        </button>

        <button
          className="secondary-btn"
          onClick={() => setPage("register")}
        >
          Create Account
        </button>
      </div>
    </div>
  );
}

export default Login;