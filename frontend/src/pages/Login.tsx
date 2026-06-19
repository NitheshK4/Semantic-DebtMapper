import React, { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { api } from "../api/client";
import { ShieldAlert, LogIn, Lock, Mail } from "lucide-react";
import { motion } from "framer-motion";

export const Login: React.FC = () => {
  const [email, setEmail] = useState("admin@sdm.com");
  const [password, setPassword] = useState("admin");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      // In a real app we might want to automatically register if not found, 
      // but for this demo let's assume we just need to try logging in.
      // Or we can hit a register endpoint first if it's a new system.
      // Let's just login and catch if needed.
      try {
        const res = await api.login(email, password);
        login(res.access_token);
      } catch {
        // Fallback to register for demo purposes if user doesn't exist
        const res = await fetch(`${import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1"}/register`, {
          method: "POST",
          headers: { "Content-Type": "application/json", "X-API-Key": import.meta.env.VITE_API_KEY },
          body: JSON.stringify({ email, password }),
        });
        if (res.ok) {
          const loginRes = await api.login(email, password);
          login(loginRes.access_token);
        } else {
          setError("Failed to login or register.");
        }
      }
    } catch (err) {
      setError("Invalid credentials or server error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-[#030408] relative overflow-hidden">
      {/* Vibe Background */}
      <div className="bg-glow-blobs">
        <div className="glow-blob blob-1"></div>
        <div className="glow-blob blob-2"></div>
      </div>

      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: "easeOut" }}
        className="glass-panel p-8 rounded-2xl w-full max-w-md relative z-10"
      >
        <div className="text-center mb-8">
          <div className="flex items-center justify-center space-x-2 mb-4">
            <span className="w-2 h-2 rounded-full bg-indigo-500 shadow-[0_0_12px_rgba(99,102,241,0.8)] animate-pulse"></span>
            <span className="font-bold text-white tracking-widest uppercase">
              Debt Mapper
            </span>
          </div>
          <h1 className="text-2xl font-bold text-white mb-2">Secure Access</h1>
          <p className="text-xs text-gray-400 font-medium">
            Authenticate to manage semantic policies and rules
          </p>
        </div>

        <form onSubmit={handleLogin} className="space-y-5">
          {error && (
            <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-3 rounded-xl text-xs flex items-center space-x-2">
              <ShieldAlert className="w-4 h-4" />
              <span>{error}</span>
            </div>
          )}

          <div className="space-y-1">
            <label className="text-[10px] font-bold text-gray-500 uppercase tracking-wider pl-1">
              Email Address
            </label>
            <div className="relative">
              <Mail className="w-4 h-4 text-gray-500 absolute left-3.5 top-3" />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full bg-[#0a0d16]/50 border border-white/5 rounded-xl py-2.5 pl-10 pr-4 text-sm text-white focus:outline-none focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/50 transition-all"
                placeholder="admin@sdm.com"
              />
            </div>
          </div>

          <div className="space-y-1">
            <label className="text-[10px] font-bold text-gray-500 uppercase tracking-wider pl-1">
              Password
            </label>
            <div className="relative">
              <Lock className="w-4 h-4 text-gray-500 absolute left-3.5 top-3" />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full bg-[#0a0d16]/50 border border-white/5 rounded-xl py-2.5 pl-10 pr-4 text-sm text-white focus:outline-none focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/50 transition-all"
                placeholder="••••••••"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-bold py-2.5 rounded-xl text-sm transition-all flex items-center justify-center space-x-2 shadow-[0_0_20px_rgba(99,102,241,0.2)] hover:shadow-[0_0_25px_rgba(99,102,241,0.4)] disabled:opacity-50"
          >
            {loading ? (
              <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
            ) : (
              <>
                <LogIn className="w-4 h-4" />
                <span>Authenticate Session</span>
              </>
            )}
          </button>
        </form>
      </motion.div>
    </div>
  );
};
