"use client";
import { Navbar, NavbarBrand, NavbarContent, NavbarItem, Link, Button, Dropdown, DropdownTrigger, DropdownMenu, DropdownItem, Avatar } from "@nextui-org/react";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import ThemeToggle from "../theme-toggle";
import { useAuth } from "@/hooks/useAuth";
import { 
  DashboardIcon, 
  TransactionIcon, 
  ReceiptIcon, 
  RulesIcon, 
  VendorIcon, 
  SettingsIcon, 
  AuditIcon, 
  AnalyticsIcon, 
  ExportIcon 
} from "../icons";

export default function AppShell({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth();
  const pathname = usePathname();

  const navItems = [
    { href: "/dashboard", label: "Dashboard", icon: DashboardIcon },
    { href: "/transactions", label: "Transactions", icon: TransactionIcon },
    { href: "/receipts", label: "Receipts", icon: ReceiptIcon },
    { href: "/rules", label: "Rules", icon: RulesIcon },
    { href: "/vendors", label: "Vendors", icon: VendorIcon },
    { href: "/firm", label: "Firm Settings", icon: SettingsIcon },
    { href: "/audit", label: "Audit", icon: AuditIcon },
    { href: "/analytics", label: "Analytics", icon: AnalyticsIcon },
    { href: "/export", label: "Export", icon: ExportIcon },
  ];

  return (
    <div className="min-h-dvh grid grid-cols-1 lg:grid-cols-[240px_1fr]">
      {/* Sidebar */}
      <aside className="hidden lg:flex flex-col gap-2 p-4 border-r border-divider bg-gradient-to-b from-emerald-500/5 to-cyan-500/5">
        <motion.div 
          className="text-sm font-semibold opacity-60 mb-2"
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 0.6, x: 0 }}
          transition={{ duration: 0.5 }}
        >
          AI Bookkeeper
        </motion.div>
        <nav className="flex flex-col gap-1">
          {navItems.map((item, index) => {
            const isActive = pathname === item.href;
            const IconComponent = item.icon;
            return (
              <motion.div
                key={item.href}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
              >
                <Link 
                  href={item.href} 
                  color={isActive ? "primary" : "foreground"}
                  className={`flex items-center gap-2 p-2 rounded-lg transition-all duration-200 ${
                    isActive 
                      ? "bg-gradient-to-r from-emerald-500/20 to-cyan-500/20 text-emerald-400 font-medium" 
                      : "hover:bg-emerald-500/10"
                  }`}
                >
                  <IconComponent />
                  {item.label}
                </Link>
              </motion.div>
            );
          })}
        </nav>
        
        {user && (
          <motion.div 
            className="mt-auto pt-4 border-t border-divider"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.5 }}
          >
            <div className="text-xs opacity-60 mb-1">Signed in as</div>
            <div className="text-sm font-medium truncate">{user.email}</div>
            <div className="text-xs opacity-40 capitalize">{user.role}</div>
          </motion.div>
        )}
      </aside>

      {/* Main */}
      <main className="flex flex-col bg-gradient-to-br from-slate-900/50 to-slate-800/30">
        <Navbar maxWidth="full" className="border-b border-divider bg-slate-900/80 backdrop-blur-sm">
          <NavbarBrand>
            <Link 
              href="/" 
              className="flex items-center gap-2 text-emerald-400 hover:opacity-80 transition-opacity"
            >
              <span className="text-2xl">📒</span>
              <span className="bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent font-bold">
                AI Bookkeeper
              </span>
            </Link>
          </NavbarBrand>
          <NavbarContent justify="end">
            <NavbarItem><ThemeToggle /></NavbarItem>
            {user ? (
              <NavbarItem>
                <Dropdown placement="bottom-end">
                  <DropdownTrigger>
                    <Avatar
                      as="button"
                      size="sm"
                      name={user.email}
                      className="cursor-pointer bg-gradient-to-r from-emerald-500 to-cyan-500"
                    />
                  </DropdownTrigger>
                  <DropdownMenu aria-label="User menu">
                    <DropdownItem key="profile" className="h-14 gap-2">
                      <p className="font-semibold">{user.email}</p>
                      <p className="text-xs opacity-60 capitalize">{user.role}</p>
                    </DropdownItem>
                    <DropdownItem key="settings">Settings</DropdownItem>
                    <DropdownItem key="logout" color="danger" onPress={logout}>
                      Sign out
                    </DropdownItem>
                  </DropdownMenu>
                </Dropdown>
              </NavbarItem>
            ) : (
              <>
                <NavbarItem className="hidden lg:flex">
                  <Link href="/login" className="text-emerald-400 hover:text-emerald-300">Login</Link>
                </NavbarItem>
                <NavbarItem>
                  <Button as={Link} color="primary" href="/signup" variant="flat" className="bg-gradient-to-r from-emerald-500 to-cyan-500 text-white">
                    Sign Up
                  </Button>
                </NavbarItem>
              </>
            )}
          </NavbarContent>
        </Navbar>
        <div className="p-4 lg:p-6">{children}</div>
      </main>
    </div>
  );
}
