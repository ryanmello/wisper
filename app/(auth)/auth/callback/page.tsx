"use client";

import { useEffect, useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/context/auth-context";
import { CheckCircle, AlertCircle, Loader2, Sparkles } from "lucide-react";

function GitHubCallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login } = useAuth();
  const [status, setStatus] = useState<"loading" | "success" | "error">(
    "loading"
  );
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const handleCallback = async () => {
      try {
        const code = searchParams.get("code");
        const error = searchParams.get("error");

        if (error) {
          setError(`GitHub authorization failed: ${error}`);
          setStatus("error");
          return;
        }

        if (!code) {
          setError("No authorization code received from GitHub");
          setStatus("error");
          return;
        }

        // Exchange authorization code for access token via our API route
        const tokenResponse = await fetch("/api/auth/github", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            code: code,
          }),
        });

        if (!tokenResponse.ok) {
          const errorData = await tokenResponse.json();
          throw new Error(
            errorData.error || "Failed to exchange authorization code for token"
          );
        }

        const tokenData = await tokenResponse.json();

        // Use auth context to properly set authentication state
        try {
          await login(tokenData.access_token);
          setStatus("success");

          // Redirect back to main app after a short delay
          setTimeout(() => {
            router.push("/");
          }, 2000);
        } catch (loginError) {
          console.error(loginError);
          throw new Error("Failed to authenticate with GitHub");
        }
      } catch (err) {
        console.error("OAuth callback error:", err);
        setError(
          err instanceof Error ? err.message : "An unknown error occurred"
        );
        setStatus("error");
      }
    };

    handleCallback();
  }, [searchParams, router]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <Card className="w-full max-w-md border-0 shadow-lg py-8">
        <CardHeader className="text-center">
          <div className="mx-auto mb-6 w-14 h-14 bg-gray-900 rounded-xl flex items-center justify-center">
            <Sparkles className="w-7 h-7 text-white" />
          </div>
          <CardTitle className="text-xl font-semibold text-gray-900">
            {status === "loading" && "Connecting to GitHub"}
            {status === "success" && "Successfully Connected!"}
            {status === "error" && "Connection Failed"}
          </CardTitle>
          <CardDescription className="text-gray-600 text-sm">
            {status === "loading" && "Processing your GitHub authorization..."}
            {status === "success" && "Redirecting you back to Conscience..."}
            {status === "error" &&
              "There was an issue connecting your GitHub account."}
          </CardDescription>
        </CardHeader>
        <CardContent className="text-center">
          {status === "loading" && (
            <div className="flex items-center justify-center">
              <Loader2 className="w-8 h-8 animate-spin text-gray-900" />
            </div>
          )}

          {status === "success" && (
            <div className="text-center">
              <div className="w-16 h-16 mx-auto bg-green-100 rounded-full flex items-center justify-center">
                <CheckCircle className="w-8 h-8 text-green-600" />
              </div>
            </div>
          )}

          {status === "error" && (
            <div className="text-center">
              <div className="w-16 h-16 mx-auto mb-4 bg-red-100 rounded-full flex items-center justify-center">
                <AlertCircle className="w-8 h-8 text-red-600" />
              </div>
              <p className="text-gray-700 mb-6 text-sm leading-relaxed bg-gray-50 p-4 rounded-lg">
                {error}
              </p>
              <Button className="bg-gray-900 hover:bg-gray-800 text-white px-6 py-2 rounded-lg transition-colors">
                Return to Conscience
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default function GitHubCallback() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
          <Card className="w-full max-w-md border-0 shadow-lg py-8">
            <CardHeader className="text-center">
              <div className="mx-auto mb-6 w-14 h-14 bg-gray-900 rounded-xl flex items-center justify-center">
                <Sparkles className="w-7 h-7 text-white" />
              </div>
              <CardTitle className="text-xl font-semibold text-gray-900">
                Loading...
              </CardTitle>
            </CardHeader>
            <CardContent className="text-center">
              <Loader2 className="w-8 h-8 animate-spin text-gray-900 mx-auto" />
            </CardContent>
          </Card>
        </div>
      }
    >
      <GitHubCallbackContent />
    </Suspense>
  );
}
