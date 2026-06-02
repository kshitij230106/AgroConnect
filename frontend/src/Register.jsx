import { useState } from "react";
import "./styles.css";

function Register({ setPage }) {
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");

  const handleRegister = async () => {
    if (!name || !phone || !password) {
      alert("Please fill all fields");
      return;
    }

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/register",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            name,
            phone,
            password,
          }),
        }
      );

      const data = await response.json();

      alert(data.message);

      if (data.message === "Registration successful") {
        setPage("login");
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
          Create Account
        </p>

        <input
          type="text"
          placeholder="Full Name"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />

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
            if (e.key === "Enter") handleRegister();
          }}
        />

        <button className="primary-btn" onClick={handleRegister}>
          Register
        </button>

        <button
          className="secondary-btn"
          onClick={() => setPage("login")}
        >
          Already have account? Login
        </button>
      </div>
    </div>
  );
}

export default Register;