"use client";
import { useState } from "react";
import { Navbar, NavbarBrand, NavbarContent, NavbarItem, NavbarMenu, NavbarMenuItem, NavbarMenuToggle, Link, Button, Dropdown, DropdownTrigger, DropdownMenu, DropdownItem, Avatar } from "@nextui-org/react";
import { usePathname } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import ThemeToggle from "../theme-toggle";
import { useAuth } from "@/hooks/useAuth";
import { 
  DashboardIcon, 
  TransactionIcon, 
  SettingsIcon, 
  ExportIcon 
} from "../icons";

export default function AppShell({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth();
  const pathname = usePathname();
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  // Core MVP navigation - clear workflow: Upload → Review → Export
  const navItems = [
    { href: "/dashboard", label: "Dashboard", icon: DashboardIcon },
    { href: "/welcome", label: "Upload", icon: TransactionIcon },
    { href: "/transactions", label: "Transactions", icon: TransactionIcon },
    { href: "/export", label: "Export", icon: ExportIcon },
    { href: "/firm", label: "Settings", icon: SettingsIcon },
  ];

  return (
    <div className="min-h-dvh grid grid-cols-1 lg:grid-cols-[240px_1fr]">
      {/* Desktop Sidebar */}
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
        <Navbar 
          maxWidth="full" 
          className="border-b border-divider bg-slate-900/80 backdrop-blur-sm"
          isMenuOpen={isMenuOpen}
          onMenuOpenChange={setIsMenuOpen}
        >
          {/* Mobile Menu Toggle */}
          <NavbarMenuToggle 
            aria-label={isMenuOpen ? "Close menu" : "Open menu"} 
            className="lg:hidden text-emerald-400"
          />
          
          <NavbarBrand>
            <Link 
              href="/" 
              className="flex items-center gap-2 text-emerald-400 hover:opacity-80 transition-opacity"
            >
              <span className="text-xl sm:text-2xl">📒</span>
              <span className="bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent font-bold text-sm sm:text-base">
                AI Bookkeeper
              </span>
            </Link>
          </NavbarBrand>
          
          <NavbarContent justify="end">
            <NavbarItem className="hidden sm:flex"><ThemeToggle /></NavbarItem>
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
                  <DropdownMenu 
                    aria-label="User menu"
                    className="bg-slate-800/95 backdrop-blur-md border border-emerald-500/20"
                  >
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
                  <Button 
                    as={Link} 
                    color="primary" 
                    href="/signup" 
                    variant="flat" 
                    size="sm"
                    className="bg-gradient-to-r from-emerald-500 to-cyan-500 text-white"
                  >
                    Sign Up
                  </Button>
                </NavbarItem>
              </>
            )}
          </NavbarContent>

          {/* Mobile Menu */}
          <NavbarMenu className="bg-slate-900/95 backdrop-blur-md border-r border-emerald-500/20 pt-6">
            {navItems.map((item, index) => {
              const isActive = pathname === item.href;
              const IconComponent = item.icon;
              return (
                <NavbarMenuItem key={item.href}>
                  <motion.div
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.3, delay: index * 0.05 }}
                  >
                    <Link
                      href={item.href}
                      className={`flex items-center gap-3 p-3 rounded-lg transition-all duration-200 w-full ${
                        isActive 
                          ? "bg-gradient-to-r from-emerald-500/20 to-cyan-500/20 text-emerald-400 font-medium" 
                          : "text-slate-300 hover:bg-emerald-500/10 hover:text-emerald-400"
                      }`}
                      onPress={() => setIsMenuOpen(false)}
                    >
                      <IconComponent />
                      <span className="text-base">{item.label}</span>
                    </Link>
                  </motion.div>
                </NavbarMenuItem>
              );
            })}
            
            {/* Mobile User Info */}
            {user && (
              <NavbarMenuItem>
                <motion.div 
                  className="mt-6 pt-6 border-t border-divider px-3"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ duration: 0.3, delay: 0.5 }}
                >
                  <div className="text-xs opacity-60 mb-1">Signed in as</div>
                  <div className="text-sm font-medium text-emerald-400">{user.email}</div>
                  <div className="text-xs opacity-40 capitalize">{user.role}</div>
                  <Button 
                    color="danger" 
                    variant="flat" 
                    size="sm" 
                    onPress={logout}
                    className="mt-4 w-full"
                  >
                    Sign out
                  </Button>
                </motion.div>
              </NavbarMenuItem>
            )}
            
            {/* Mobile Theme Toggle */}
            <NavbarMenuItem className="sm:hidden mt-4">
              <div className="px-3">
                <ThemeToggle />
              </div>
            </NavbarMenuItem>
          </NavbarMenu>
        </Navbar>
        <div className="p-3 sm:p-4 lg:p-6 overflow-x-hidden">{children}</div>
      </main>
    </div>
  );
}
