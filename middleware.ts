import { NextRequest, NextResponse } from 'next/server';

// Routes that require authentication
const protectedRoutes = ['/cipher', '/waypoint', '/veda', '/conscience', '/docs'];

// Routes that should redirect authenticated users
const authRoutes = ['/sign-in'];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  
  // Get the token from cookies (we'll need to set this when user logs in)
  const token = request.cookies.get('github_token')?.value;
  
  // Check if the current path is protected
  const isProtectedRoute = protectedRoutes.some(route => 
    pathname.startsWith(route)
  );
  
  // Check if the current path is an auth route
  const isAuthRoute = authRoutes.some(route => 
    pathname.startsWith(route)
  );

  // If it's a protected route and no token, redirect to sign-in
  if (isProtectedRoute && !token) {
    const signInUrl = new URL('/sign-in', request.url);
    signInUrl.searchParams.set('callbackUrl', pathname);
    return NextResponse.redirect(signInUrl);
  }

  // If it's an auth route and user has token, redirect to tasks
  if (isAuthRoute && token) {
    return NextResponse.redirect(new URL('/cipher', request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    '/((?!api|_next/static|_next/image|favicon.ico).*)',
  ],
}; 