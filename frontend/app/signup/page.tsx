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
  Checkbox,
} from "@nextui-org/react";
import { motion } from "framer-motion";
import FlowingBackground from "@/components/background/FlowingBackground";

export default function SignupPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [acceptedTerms, setAcceptedTerms] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");

    // Validation
    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    if (password.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }

    if (!acceptedTerms) {
      setError("Please accept the Terms of Service");
      return;
    }

    setLoading(true);

    try {
      // TODO: Implement signup API endpoint
      // For now, show placeholder message
      alert("Signup functionality coming soon! For now, use Dev@dev.com / Dev to login.");
      router.push("/login");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Signup failed. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen relative flex items-center justify-center bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-4 overflow-hidden">
      <FlowingBackground />
      
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
              Create your account
            </h1>
            <p className="text-sm text-slate-400">Start automating your bookkeeping</p>
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
                  label="Full Name"
                  type="text"
                  placeholder="John Doe"
                  value={fullName}
                  onValueChange={setFullName}
                  isRequired
                  size="lg"
                  variant="bordered"
                  autoComplete="name"
                  classNames={{
                    input: "bg-slate-800/50 text-slate-200",
                    inputWrapper: "bg-slate-800/50 border-emerald-500/30 hover:border-emerald-400/50 focus-within:border-emerald-400",
                    label: "text-slate-300"
                  }}
                />
              </motion.div>

              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.2 }}
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

              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.3 }}
              >
                <Input
                  label="Password"
                  type="password"
                  placeholder="At least 8 characters"
                  value={password}
                  onValueChange={setPassword}
                  isRequired
                  size="lg"
                  variant="bordered"
                  autoComplete="new-password"
                  description="Minimum 8 characters"
                  classNames={{
                    input: "bg-slate-800/50 text-slate-200",
                    inputWrapper: "bg-slate-800/50 border-emerald-500/30 hover:border-emerald-400/50 focus-within:border-emerald-400",
                    label: "text-slate-300",
                    description: "text-slate-400"
                  }}
                />
              </motion.div>

              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.4 }}
              >
                <Input
                  label="Confirm Password"
                  type="password"
                  placeholder="Re-enter your password"
                  value={confirmPassword}
                  onValueChange={setConfirmPassword}
                  isRequired
                  size="lg"
                  variant="bordered"
                  autoComplete="new-password"
                  classNames={{
                    input: "bg-slate-800/50 text-slate-200",
                    inputWrapper: "bg-slate-800/50 border-emerald-500/30 hover:border-emerald-400/50 focus-within:border-emerald-400",
                    label: "text-slate-300"
                  }}
                />
              </motion.div>

              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.5 }}
              >
                <Checkbox
                  isSelected={acceptedTerms}
                  onValueChange={setAcceptedTerms}
                  size="sm"
                  classNames={{
                    wrapper: "before:border-emerald-500/30",
                    icon: "text-emerald-500"
                  }}
                >
                  <span className="text-sm text-slate-300">
                    I agree to the{" "}
                    <Link href="#" size="sm" className="text-emerald-400 hover:text-emerald-300">
                      Terms of Service
                    </Link>{" "}
                    and{" "}
                    <Link href="#" size="sm" className="text-emerald-400 hover:text-emerald-300">
                      Privacy Policy
                    </Link>
                  </span>
                </Checkbox>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.6 }}
              >
                <Button
                  type="submit"
                  size="lg"
                  className="w-full font-semibold bg-gradient-to-r from-emerald-500 to-cyan-500 text-white hover:from-emerald-600 hover:to-cyan-600 transition-all duration-300"
                  isLoading={loading}
                  isDisabled={!email || !password || !confirmPassword || !fullName || !acceptedTerms}
                >
                  {loading ? "Creating account..." : "Create account"}
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
              Already have an account?{" "}
              <Link href="/login" size="sm" className="text-emerald-400 hover:text-emerald-300 font-semibold">
                Sign in
              </Link>
            </motion.p>
          </CardFooter>
        </Card>
      </motion.div>
    </div>
  );
}

