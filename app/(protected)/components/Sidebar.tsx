"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  FileText,
  CalendarDays,
  LogOut,
} from "lucide-react";

export default function Sidebar() {
  const path = usePathname();

  return (
    <aside style={s.sidebar}>
      {/* Logo */}
      <div style={s.logo}>
        <div style={s.logoIcon}>📅</div>
        <span>SigortaTakvimi</span>
      </div>

      {/* Menü */}
      <nav style={s.nav}>
        <MenuItem
          href="/dashboard"
          label="Dashboard"
          icon={<LayoutDashboard size={18} />}
          path={path}
        />
        <MenuItem
          href="/policies"
          label="Poliçeler"
          icon={<FileText size={18} />}
          path={path}
        />
        <MenuItem
          href="/calendar"
          label="Takvim"
          icon={<CalendarDays size={18} />}
          path={path}
        />
      </nav>

      {/* Alt Menü */}
      <div style={s.footer}>
        <button style={s.logout}>
          <LogOut size={16} />
          Çıkış
        </button>
      </div>
    </aside>
  );
}

function MenuItem({ href, label, icon, path }: any) {
  const active = path === href;

  return (
    <Link href={href} style={{ ...s.item, ...(active ? s.active : {}) }}>
      <span style={s.icon}>{icon}</span>
      <span>{label}</span>
    </Link>
  );
}

const s: any = {
  sidebar: {
    width: 250,
    background: "linear-gradient(180deg,#4f46e5,#6366f1)",
    color: "#fff",
    padding: "24px 16px",
    display: "flex",
    flexDirection: "column",
  },
  logo: {
    display: "flex",
    alignItems: "center",
    gap: 10,
    fontSize: 20,
    fontWeight: 700,
    marginBottom: 40,
  },
  logoIcon: {
    background: "rgba(255,255,255,0.2)",
    borderRadius: 10,
    padding: 6,
  },
  nav: {
    display: "flex",
    flexDirection: "column",
    gap: 10,
  },
  item: {
    display: "flex",
    alignItems: "center",
    gap: 12,
    padding: "12px 14px",
    borderRadius: 12,
    textDecoration: "none",
    color: "#fff",
    transition: "all .2s",
  },
  active: {
    background: "rgba(255,255,255,0.22)",
  },
  icon: {
    opacity: 0.9,
  },
  footer: {
    marginTop: "auto",
  },
  logout: {
    width: "100%",
    display: "flex",
    alignItems: "center",
    gap: 10,
    padding: "12px 14px",
    borderRadius: 12,
    background: "rgba(255,255,255,0.15)",
    border: "none",
    color: "#fff",
    cursor: "pointer",
  },
};
