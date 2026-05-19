"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { logout, getUser } from "@/lib/auth";
import { Home, Wallet, PieChart, TrendingUp, LogOut, Menu, Bot, Moon, Sun } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { useTheme } from "next-themes";

const navItems = [
  { href: "/", label: "Dashboard", icon: Home },
  { href: "/transactions", label: "Transactions", icon: Wallet },
  { href: "/categories", label: "Categories", icon: PieChart },
  { href: "/budgets", label: "Budgets", icon: TrendingUp },
  { href: "/analytics", label: "Analytics", icon: TrendingUp },
  { href: "/chat", label: "AI Assistant", icon: Bot },
];

export function Sidebar() {
  const pathname = usePathname();
  const [userName, setUserName] = useState<string>("");

  const { theme, setTheme } = useTheme();

  useEffect(() => {
    const user = getUser();
    if (user?.name) {
      setUserName(user.name.charAt(0).toUpperCase());
    }
  }, []);

  return (
    <aside className="w-64 border-r bg-muted/10 h-screen fixed left-0 top-0 flex flex-col z-40">
      <div className="p-4 border-b">
        <h1 className="text-xl font-bold tracking-tight">FinTrack</h1>
      </div>
      <nav className="flex-1 p-4 space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                isActive ? "bg-primary text-primary-foreground" : "hover:bg-muted"
              }`}
            >
              <Icon className="h-4 w-4" />
              {item.label}
            </Link>
          );
        })}
      </nav>
      <div className="p-4 border-t space-y-2">
        <Button
          variant="ghost"
          className="w-full justify-start gap-3"
          onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
        >
          {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          <span className="text-sm font-medium">
            {theme === "dark" ? "Light Mode" : "Dark Mode"}
          </span>
        </Button>
        <Button variant="ghost" className="w-full justify-start gap-3" onClick={logout}>
          <Avatar className="h-8 w-8">
            <AvatarFallback>{userName || "U"}</AvatarFallback>
          </Avatar>
          <span className="text-sm font-medium">Log out</span>
        </Button>
      </div>
    </aside>
  );
}
