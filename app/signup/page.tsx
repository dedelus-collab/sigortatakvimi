"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { supabase } from "@/lib/supabase";

export default function SignupPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [agency, setAgency] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSignup(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);

    // 1️⃣ Kullanıcı oluştur
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
    });

    if (error || !data.user) {
      setLoading(false);
      alert(error?.message || "Kayıt başarısız");
      return;
    }

    // 2️⃣ Profil (acente adı) kaydet
    const { error: profileError } = await supabase
      .from("profiles")
      .insert([
        {
          id: data.user.id,
          agency_name: agency,
        },
      ]);

    setLoading(false);

    if (profileError) {
      alert("Profil kaydedilemedi");
      return;
    }

    alert("Kayıt başarılı, giriş yapabilirsiniz");
    router.push("/login");
  }

  return (
    <div style={s.page}>
      <form onSubmit={handleSignup} style={s.card}>
        <h1 style={s.title}>Acenta Kaydı</h1>

        <input
          placeholder="Acente Adı"
          required
          value={agency}
          onChange={(e) => setAgency(e.target.value)}
          style={s.input}
        />

        <input
          type="email"
          placeholder="Email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          style={s.input}
        />

        <input
          type="password"
          placeholder="Şifre"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          style={s.input}
        />

        <button style={s.button} disabled={loading}>
          {loading ? "Oluşturuluyor..." : "Kayıt Ol"}
        </button>
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
    width: 380,
    background: "#fff",
    padding: 32,
    borderRadius: 22,
    boxShadow: "0 20px 40px rgba(0,0,0,0.12)",
    display: "flex",
    flexDirection: "column",
    gap: 14,
  },
  title: {
    fontSize: 26,
    fontWeight: 800,
  },
  input: {
    padding: "14px 16px",
    borderRadius: 14,
    border: "1px solid #e5e7eb",
    fontSize: 15,
  },
  button: {
    marginTop: 10,
    padding: "14px",
    borderRadius: 16,
    border: "none",
    background: "linear-gradient(135deg,#2563eb,#7c3aed)",
    color: "#fff",
    fontWeight: 800,
    cursor: "pointer",
  },
};
