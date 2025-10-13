"use client";
import { Navbar, NavbarBrand, NavbarContent, NavbarItem, Link, Button } from "@nextui-org/react";
import ThemeToggle from "../theme-toggle";

export default function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-dvh grid grid-cols-1 lg:grid-cols-[240px_1fr]">
      {/* Sidebar */}
      <aside className="hidden lg:flex flex-col gap-2 p-4 border-r border-divider">
        <div className="text-sm font-semibold opacity-60">AI Bookkeeper</div>
        <nav className="flex flex-col gap-1">
          <Link href="/" color="foreground">Dashboard</Link>
          <Link href="/transactions" color="foreground">Transactions</Link>
          <Link href="/vendors" color="foreground">Vendors</Link>
          <Link href="/compliance" color="foreground">Compliance</Link>
        </nav>
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
          </NavbarContent>
        </Navbar>
        <div className="p-4">{children}</div>
      </main>
    </div>
  );
}

