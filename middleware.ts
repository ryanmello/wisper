import { NextRequest, NextResponse } from "next/server";

// truly public (no auth) pages
const PUBLIC_PATHS = ["/docs"] as const;
const SIGN_IN_PATH  = "/sign-in";

export function middleware(request: NextRequest) {
  const { pathname, searchParams } = request.nextUrl;
  const token = request.cookies.get("github_token")?.value;

  // 1️⃣ Allow the public docs
  if (PUBLIC_PATHS.some((p) => pathname.startsWith(p))) {
    return NextResponse.next();
  }

  // 2️⃣ Handle the sign‑in page itself
  if (pathname.startsWith(SIGN_IN_PATH)) {
    // If already signed in, send them back to where they came from (or /)
    if (token) {
      const dest = searchParams.get("callbackUrl") || "/";
      return NextResponse.redirect(new URL(dest, request.url));
    }
    // otherwise just let them see the sign‑in form
    return NextResponse.next();
  }

  // 3️⃣ Everything else (including "/") is protected
  if (!token) {
    const signInUrl = new URL(SIGN_IN_PATH, request.url);
    signInUrl.searchParams.set("callbackUrl", pathname);
    return NextResponse.redirect(signInUrl);
  }

  // 4️⃣ Authenticated users get free passage
  return NextResponse.next();
}

export const config = {
  matcher: [
    "/((?!api|_next/static|_next/image|favicon.ico|auth/callback).*)",
  ],
};
