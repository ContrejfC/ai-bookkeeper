"use client";
import { Navbar, NavbarBrand, NavbarContent, NavbarItem, Link, Button, Dropdown, DropdownTrigger, DropdownMenu, DropdownItem, Avatar } from "@nextui-org/react";
import ThemeToggle from "../theme-toggle";
import { useAuth } from "@/hooks/useAuth";

export default function AppShell({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-dvh grid grid-cols-1 lg:grid-cols-[240px_1fr]">
      {/* Sidebar */}
      <aside className="hidden lg:flex flex-col gap-2 p-4 border-r border-divider">
        <div className="text-sm font-semibold opacity-60">AI Bookkeeper</div>
        <nav className="flex flex-col gap-1">
          <Link href="/dashboard" color="foreground">Dashboard</Link>
          <Link href="/transactions" color="foreground">Transactions</Link>
          <Link href="/vendors" color="foreground">Vendors</Link>
          <Link href="/compliance" color="foreground">Compliance</Link>
        </nav>
        
        {user && (
          <div className="mt-auto pt-4 border-t border-divider">
            <div className="text-xs opacity-60 mb-1">Signed in as</div>
            <div className="text-sm font-medium truncate">{user.email}</div>
            <div className="text-xs opacity-40 capitalize">{user.role}</div>
          </div>
        )}
      </aside>

      {/* Main */}
      <main className="flex flex-col">
        <Navbar maxWidth="full" className="border-b border-divider">
          <NavbarBrand>📒 AI Bookkeeper</NavbarBrand>
          <NavbarContent justify="end">
            <NavbarItem><ThemeToggle /></NavbarItem>
            <NavbarItem>
              <Button as={Link} href="/new" color="primary" size="sm">New</Button>
            </NavbarItem>
            {user && (
              <NavbarItem>
                <Dropdown placement="bottom-end">
                  <DropdownTrigger>
                    <Avatar
                      as="button"
                      size="sm"
                      name={user.email}
                      className="cursor-pointer"
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
            )}
          </NavbarContent>
        </Navbar>
        <div className="p-4">{children}</div>
      </main>
    </div>
  );
}
