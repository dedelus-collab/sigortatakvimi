"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { supabase } from "@/lib/supabase";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  async function handleLogin(e: any) {
    e.preventDefault();
    setError("");

    const { error } = await supabase.auth.signInWithPassword({
      email: email.trim().toLowerCase(),
      password,
    });

    if (error) {
      setError(error.message);
      return;
    }

    router.push("/dashboard");
  }

  return (
    <div style={s.page}>
      <form onSubmit={handleLogin} style={s.card}>
        <h1 style={s.title}>Giriş Yap</h1>

        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          style={s.input}
          required
        />

        <input
          type="password"
          placeholder="Şifre"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          style={s.input}
          required
        />

        {error && <p style={s.error}>{error}</p>}

        <button type="submit" style={s.button}>
          Giriş Yap
        </button>

        {/* 👇 SIGN UP GEÇİŞ */}
        <p style={s.text}>
          Hesabın yok mu?{" "}
          <Link href="/signup" style={s.link}>
            Kayıt ol
          </Link>
        </p>
      </form>
    </div>
  );
}

const s: any = {
  page: {
    minHeight: "100vh",
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    background: "#f1f5f9",
  },
  card: {
    width: 360,
    background: "#fff",
    padding: 32,
    borderRadius: 24,
    boxShadow: "0 20px 40px rgba(0,0,0,0.12)",
    display: "flex",
    flexDirection: "column",
    gap: 14,
  },
  title: { fontSize: 26, fontWeight: 800 },
  input: {
    padding: 14,
    borderRadius: 14,
    border: "1px solid #e5e7eb",
    background: "#f8fafc",
  },
  button: {
    marginTop: 8,
    padding: 14,
    borderRadius: 14,
    background: "linear-gradient(135deg,#7c3aed,#2563eb)",
    color: "#fff",
    fontWeight: 800,
    border: "none",
    cursor: "pointer",
  },
  text: {
    marginTop: 10,
    fontSize: 14,
    textAlign: "center",
    color: "#64748b",
  },
  link: {
    color: "#2563eb",
    fontWeight: 700,
    textDecoration: "none",
  },
  error: {
    color: "#dc2626",
    fontSize: 14,
  },
};
