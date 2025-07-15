import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { AuthProvider } from "@/context/auth-context";
import { TaskProvider } from "@/context/task-context";
import { CartProvider } from "@/context/cart-context";
import Sidebar from "@/components/Sidebar";
import { Toaster } from "@/components/ui/sonner";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Cipher",
  description: "AI-powered code analysis and task automation platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <AuthProvider>
          <TaskProvider>
            <CartProvider>
              <Sidebar />
              <main className="pl-16">
                {children}
              </main>
              <Toaster position="bottom-center" />
            </CartProvider>
          </TaskProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
