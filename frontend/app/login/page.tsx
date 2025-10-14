"use client";

import { useState, FormEvent } from "react";
import { useRouter } from "next/navigation";
import {
  Card,
  CardHeader,
  CardBody,
  CardFooter,
  Input,
  Button,
  Divider,
  Link,
} from "@nextui-org/react";
import { login } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [useMagicLink, setUseMagicLink] = useState(true); // Dev mode default
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const result = await login(
        email,
        useMagicLink ? undefined : password,
        useMagicLink ? "dev" : undefined
      );

      if (result.success) {
        // Redirect to dashboard
        router.push("/");
      } else {
        setError("Login failed. Please check your credentials.");
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Login failed. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary/10 to-success/10 p-4">
      <Card className="w-full max-w-md rounded-2xl">
        <CardHeader className="flex flex-col gap-2 items-center pt-8 pb-4">
          <div className="text-4xl mb-2">📒</div>
          <h1 className="text-2xl font-bold">AI Bookkeeper</h1>
          <p className="text-sm opacity-60">Sign in to your account</p>
        </CardHeader>

        <Divider />

        <form onSubmit={handleSubmit}>
          <CardBody className="gap-4 py-6">
            {error && (
              <div className="px-4 py-3 rounded-xl bg-danger/10 text-danger text-sm">
                {error}
              </div>
            )}

            <Input
              label="Email"
              type="email"
              placeholder="you@example.com"
              value={email}
              onValueChange={setEmail}
              isRequired
              size="lg"
              variant="bordered"
              autoComplete="email"
            />

            {!useMagicLink && (
              <Input
                label="Password"
                type="password"
                placeholder="Enter your password"
                value={password}
                onValueChange={setPassword}
                isRequired={!useMagicLink}
                size="lg"
                variant="bordered"
                autoComplete="current-password"
              />
            )}

            <div className="flex items-center justify-between text-sm">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={useMagicLink}
                  onChange={(e) => setUseMagicLink(e.target.checked)}
                  className="w-4 h-4"
                />
                <span className="opacity-60">
                  Dev mode (magic link)
                </span>
              </label>
              {!useMagicLink && (
                <Link href="#" size="sm" className="opacity-60">
                  Forgot password?
                </Link>
              )}
            </div>

            <Button
              type="submit"
              color="primary"
              size="lg"
              className="w-full font-semibold"
              isLoading={loading}
              isDisabled={!email || (!useMagicLink && !password)}
            >
              {loading ? "Signing in..." : "Sign in"}
            </Button>
          </CardBody>
        </form>

        <Divider />

        <CardFooter className="flex flex-col gap-2 py-4">
          <p className="text-sm opacity-60 text-center">
            Don&apos;t have an account?{" "}
            <Link href="#" size="sm">
              Contact your administrator
            </Link>
          </p>
          <p className="text-xs opacity-40 text-center mt-2">
            By signing in, you agree to our Terms of Service and Privacy Policy
          </p>
        </CardFooter>
      </Card>
    </div>
  );
}
