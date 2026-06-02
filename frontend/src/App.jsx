import { useState, useEffect } from "react";
import Login from "./Login";
import Register from "./Register";
import Chatbot from "./Chatbot";
import "./App.css";

function App() {
  const [page, setPage] = useState("login");
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [farmerName, setFarmerName] = useState("");

  useEffect(() => {
    const loggedIn = localStorage.getItem("loggedIn");
    const name = localStorage.getItem("farmerName");
    if (loggedIn === "true") {
      setIsLoggedIn(true);
      setFarmerName(name || "");
    }
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("loggedIn");
    localStorage.removeItem("farmerName");
    setIsLoggedIn(false);
    setFarmerName("");
    setPage("login");
  };

  if (isLoggedIn) {
    return (
      <Chatbot
        onLogout={handleLogout}
        farmerName={farmerName}
      />
    );
  }

  if (page === "register") {
    return <Register setPage={setPage} />;
  }

  return (
    <Login
      setIsLoggedIn={setIsLoggedIn}
      setPage={setPage}
      setFarmerName={setFarmerName}
    />
  );
}

export default App;