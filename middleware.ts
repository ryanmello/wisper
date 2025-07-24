import { NextRequest, NextResponse } from "next/server";

// truly public (no auth) pages
const PUBLIC_PATHS = ["/docs"] as const;
const SIGN_IN_PATH = "/sign-in";
const AUTH_PATHS = ["/auth/callback"];

export async function middleware(request: NextRequest) {
  const { pathname, searchParams } = request.nextUrl;
  const sessionId = request.cookies.get("session_id")?.value;

  // Allow public docs
  if (PUBLIC_PATHS.some((p) => pathname.startsWith(p))) {
    return NextResponse.next();
  }

  // Allow auth callback pages
  if (AUTH_PATHS.some((p) => pathname.startsWith(p))) {
    return NextResponse.next();
  }

  // Handle the sign-in page itself
  if (pathname.startsWith(SIGN_IN_PATH)) {
    // If already signed in, check with backend and redirect if valid
    if (sessionId) {
      try {
        const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const response = await fetch(`${backendUrl}/auth/status`, {
          headers: {
            Cookie: `session_id=${sessionId}`,
          },
        });
        
        if (response.ok) {
          const data = await response.json();
          if (data.authenticated) {
            const dest = searchParams.get("callbackUrl") || "/";
            return NextResponse.redirect(new URL(dest, request.url));
          }
        }
      } catch (error) {
        // If backend check fails, continue to sign-in page
        console.log("Backend auth check failed in middleware:", error);
      }
    }
    // Otherwise let them see the sign-in form
    return NextResponse.next();
  }

  // Everything else (including "/") is protected
  if (!sessionId) {
    const signInUrl = new URL(SIGN_IN_PATH, request.url);
    signInUrl.searchParams.set("callbackUrl", pathname);
    return NextResponse.redirect(signInUrl);
  }

  // For authenticated users, optionally verify session with backend
  // (This is optional as the backend APIs will validate the session)
  return NextResponse.next();
}

export const config = {
  matcher: [
    "/((?!api|_next/static|_next/image|favicon.ico|auth/callback).*)",
  ],
};
