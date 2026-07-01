import { createContext, useContext, useState } from "react";
import axios from "axios";

const AuthContext = createContext(null);
const BASE = import.meta.env.VITE_API_URL ? `${import.meta.env.VITE_API_URL}/api` : "/api";

export function AuthProvider({ children }) {
  const [token, setToken] = useState(localStorage.getItem("token"));

  async function login(username, password) {
    const form = new FormData();
    form.append("username", username);
    form.append("password", password);
    const res = await axios.post(`${BASE}/auth/login`, form);
    const t = res.data.access_token;
    localStorage.setItem("token", t);
    setToken(t);
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
