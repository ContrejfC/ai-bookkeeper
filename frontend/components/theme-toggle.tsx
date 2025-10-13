"use client";
import { Switch } from "@nextui-org/react";
import { useEffect, useState } from "react";

export default function ThemeToggle() {
  const [dark, setDark] = useState(true);
  useEffect(() => {
    const html = document.documentElement;
    dark ? html.classList.add("dark") : html.classList.remove("dark");
  }, [dark]);

  return (
    <Switch isSelected={dark} onValueChange={setDark} size="sm" aria-label="Toggle dark mode">
      Dark mode
    </Switch>
  );
}

