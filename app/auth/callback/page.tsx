"use client";

import { useEffect, useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

function GitHubCallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");
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
          throw new Error(errorData.error || "Failed to exchange authorization code for token");
        }

        const tokenData = await tokenResponse.json();

        // Store the access token (in production, use secure HTTP-only cookies)
        localStorage.setItem("github_token", tokenData.access_token);

        setStatus("success");

        // Redirect back to main app after a short delay
        setTimeout(() => {
          router.push("/");
        }, 2000);

      } catch (err) {
        console.error("OAuth callback error:", err);
        setError(err instanceof Error ? err.message : "An unknown error occurred");
        setStatus("error");
      }
    };

    handleCallback();
  }, [searchParams, router]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 w-12 h-12 bg-black rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-xl">W</span>
          </div>
          <CardTitle className="text-2xl">
            {status === "loading" && "Connecting to GitHub..."}
            {status === "success" && "Successfully Connected!"}
            {status === "error" && "Connection Failed"}
          </CardTitle>
          <CardDescription>
            {status === "loading" && "Processing your GitHub authorization..."}
                            {status === "success" && "Redirecting you back to Whisper..."}
            {status === "error" && "There was an issue connecting your GitHub account."}
          </CardDescription>
        </CardHeader>
        <CardContent className="text-center">
          {status === "loading" && (
            <div className="flex items-center justify-center">
              <div className="animate-spin w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full"></div>
            </div>
          )}
          
          {status === "success" && (
            <div className="text-green-600">
              <svg className="w-16 h-16 mx-auto mb-4" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <p className="text-gray-600">Your GitHub account has been successfully connected!</p>
            </div>
          )}
          
          {status === "error" && (
            <div className="text-red-600">
              <svg className="w-16 h-16 mx-auto mb-4" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
              <p className="text-gray-600 mb-4">{error}</p>
              <Button 
                onClick={() => router.push("/")}
                className="transition-colors"
              >
                Return to Whisper
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
    <Suspense fallback={
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center p-4">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <div className="mx-auto mb-4 w-12 h-12 bg-black rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-xl">W</span>
            </div>
            <CardTitle className="text-2xl">Loading...</CardTitle>
          </CardHeader>
          <CardContent className="text-center">
            <div className="animate-spin w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full mx-auto"></div>
          </CardContent>
        </Card>
      </div>
    }>
      <GitHubCallbackContent />
    </Suspense>
  );
} 