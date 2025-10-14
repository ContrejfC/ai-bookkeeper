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
import { motion } from "framer-motion";
import FlowingBackground from "@/components/background/FlowingBackground";

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
    <div className="min-h-screen relative flex flex-col bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-4 overflow-hidden">
      <FlowingBackground />
      
      {/* Logo Header */}
      <motion.div
        className="absolute top-6 left-6 z-20"
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.5 }}
      >
        <Link 
          href="/" 
          className="flex items-center gap-2 text-emerald-400 hover:opacity-80 transition-opacity"
        >
          <span className="text-2xl">📒</span>
          <span className="text-xl font-bold bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
            AI Bookkeeper
          </span>
        </Link>
      </motion.div>

      <div className="flex-1 flex items-center justify-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="relative z-10 w-full max-w-md"
        >
        <Card className="w-full rounded-2xl bg-slate-900/90 backdrop-blur-xl border border-emerald-500/20 shadow-2xl shadow-emerald-500/10">
          <CardHeader className="flex flex-col gap-2 items-center pt-8 pb-4">
            <motion.div 
              className="text-4xl mb-2"
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ duration: 0.5, delay: 0.2 }}
            >
              📒
            </motion.div>
            <h1 className="text-2xl font-bold bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
              AI Bookkeeper
            </h1>
            <p className="text-sm text-slate-400">Sign in to your account</p>
          </CardHeader>

          <Divider className="bg-emerald-500/20" />

          <form onSubmit={handleSubmit}>
            <CardBody className="gap-4 py-6">
              {error && (
                <motion.div 
                  className="px-4 py-3 rounded-xl bg-red-500/10 text-red-400 text-sm border border-red-500/20"
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ duration: 0.3 }}
                >
                  {error}
                </motion.div>
              )}

              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.1 }}
              >
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
                  classNames={{
                    input: "bg-slate-800/50 text-slate-200",
                    inputWrapper: "bg-slate-800/50 border-emerald-500/30 hover:border-emerald-400/50 focus-within:border-emerald-400",
                    label: "text-slate-300"
                  }}
                />
              </motion.div>

              {!useMagicLink && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, delay: 0.2 }}
                >
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
                    classNames={{
                      input: "bg-slate-800/50 text-slate-200",
                      inputWrapper: "bg-slate-800/50 border-emerald-500/30 hover:border-emerald-400/50 focus-within:border-emerald-400",
                      label: "text-slate-300"
                    }}
                  />
                </motion.div>
              )}

              <motion.div 
                className="flex items-center justify-between text-sm"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.3 }}
              >
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={useMagicLink}
                    onChange={(e) => setUseMagicLink(e.target.checked)}
                    className="w-4 h-4 rounded border-emerald-500/30 bg-slate-800 text-emerald-500 focus:ring-emerald-500/50"
                  />
                  <span className="text-slate-400">
                    Dev mode (magic link)
                  </span>
                </label>
                {!useMagicLink && (
                  <Link href="#" size="sm" className="text-emerald-400 hover:text-emerald-300">
                    Forgot password?
                  </Link>
                )}
              </motion.div>

              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.4 }}
              >
                <Button
                  type="submit"
                  size="lg"
                  className="w-full font-semibold bg-gradient-to-r from-emerald-500 to-cyan-500 text-white hover:from-emerald-600 hover:to-cyan-600 transition-all duration-300"
                  isLoading={loading}
                  isDisabled={!email || (!useMagicLink && !password)}
                >
                  {loading ? "Signing in..." : "Sign in"}
                </Button>
              </motion.div>
            </CardBody>
          </form>

          <Divider className="bg-emerald-500/20" />

          <CardFooter className="flex flex-col gap-2 py-4">
            <motion.p 
              className="text-sm text-slate-400 text-center"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.5, delay: 0.5 }}
            >
              Don&apos;t have an account?{" "}
              <Link href="#" size="sm" className="text-emerald-400 hover:text-emerald-300">
                Contact your administrator
              </Link>
            </motion.p>
            <motion.p 
              className="text-xs text-slate-500 text-center mt-2"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.5, delay: 0.6 }}
            >
              By signing in, you agree to our Terms of Service and Privacy Policy
            </motion.p>
          </CardFooter>
        </Card>
        </motion.div>
      </div>
    </div>
  );
}
