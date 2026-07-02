import { createContext, useContext, useState } from "react";
import axios from "axios";

const AuthContext = createContext(null);
const BASE = "/api";

export function AuthProvider({ children }) {
  const [token, setToken] = useState(localStorage.getItem("token"));

  async function login(username, password) {
    const form = new FormData();
    form.append("username", username);
    form.append("password", password);
    // Retry up to 3 times — Render free tier may be waking up
    let lastErr;
    for (let i = 0; i < 3; i++) {
      try {
        const res = await axios.post(`${BASE}/auth/login`, form, { timeout: 15000 });
        const t = res.data.access_token;
        localStorage.setItem("token", t);
        setToken(t);
        return;
      } catch (err) {
        lastErr = err;
        if (err.response?.status === 401) break; // wrong password, don't retry
        await new Promise(r => setTimeout(r, 3000)); // wait 3s before retry
      }
    }
    throw lastErr;
  }

  function logout() {
    localStorage.removeItem("token");
    setToken(null);
  }

  return (
    <AuthContext.Provider value={{ token, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
