"use client";

import { usePathname, useRouter } from "next/navigation";

export default function Header() {
  const pathname = usePathname();
  const router = useRouter();

  const titles: any = {
    "/dashboard": "Dashboard",
    "/calendar": "Takvim",
    "/policies": "Poliçeler",
  };

  function logout() {
    router.push("/login");
  }

  return (
    <header style={s.header}>
      <h1 style={s.title}>
        {titles[pathname] || "SigortaTakvimi"}
      </h1>

      <div style={s.right}>
        <div style={s.user}>
          <div style={s.avatar}>C</div>
          <span>Can</span>
        </div>

        <button onClick={logout} style={s.logout}>
          Çıkış
        </button>
      </div>
    </header>
  );
}

const s: any = {
  header: {
    height: 64,
    background: "#ffffff",
    borderBottom: "1px solid #e5e7eb",
    padding: "0 24px",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
  },
  title: {
    fontSize: 20,
    fontWeight: 700,
    color: "#065f46",
  },
  right: {
    display: "flex",
    alignItems: "center",
    gap: 16,
  },
  user: {
    display: "flex",
    alignItems: "center",
    gap: 10,
    fontWeight: 600,
    color: "#334155",
  },
  avatar: {
    width: 34,
    height: 34,
    borderRadius: "50%",
    background: "linear-gradient(135deg,#5eead4,#2dd4bf)",
    color: "#064e3b",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontWeight: 800,
  },
  logout: {
    background: "#ecfeff",
    color: "#065f46",
    border: "1px solid #99f6e4",
    padding: "8px 14px",
    borderRadius: 12,
    fontWeight: 600,
    cursor: "pointer",
  },
};
