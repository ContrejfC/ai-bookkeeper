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
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary/10 to-success/10 p-4">
      <Card className="w-full max-w-md rounded-2xl">
        <CardHeader className="flex flex-col gap-2 items-center pt-8 pb-4">
          <div className="text-4xl mb-2">📒</div>
          <h1 className="text-2xl font-bold">Create your account</h1>
          <p className="text-sm opacity-60">Start automating your bookkeeping</p>
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
              label="Full Name"
              type="text"
              placeholder="John Doe"
              value={fullName}
              onValueChange={setFullName}
              isRequired
              size="lg"
              variant="bordered"
              autoComplete="name"
            />

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
            />

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
            />

            <Checkbox
              isSelected={acceptedTerms}
              onValueChange={setAcceptedTerms}
              size="sm"
            >
              <span className="text-sm">
                I agree to the{" "}
                <Link href="#" size="sm">
                  Terms of Service
                </Link>{" "}
                and{" "}
                <Link href="#" size="sm">
                  Privacy Policy
                </Link>
              </span>
            </Checkbox>

            <Button
              type="submit"
              color="primary"
              size="lg"
              className="w-full font-semibold"
              isLoading={loading}
              isDisabled={!email || !password || !confirmPassword || !fullName || !acceptedTerms}
            >
              {loading ? "Creating account..." : "Create account"}
            </Button>
          </CardBody>
        </form>

        <Divider />

        <CardFooter className="flex flex-col gap-2 py-4">
          <p className="text-sm opacity-60 text-center">
            Already have an account?{" "}
            <Link href="/login" size="sm" className="font-semibold">
              Sign in
            </Link>
          </p>
        </CardFooter>
      </Card>
    </div>
  );
}

