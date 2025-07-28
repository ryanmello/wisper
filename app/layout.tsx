import type { Metadata } from "next";
import { AuthProvider } from "@/context/auth-context";
import { TaskProvider } from "@/context/task-context";
import Sidebar from "@/components/Sidebar";
import { Toaster } from "@/components/ui/sonner";
import "./globals.css";

export const metadata: Metadata = {
  title: "Conscience",
  description: "Agentic Operating System",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`antialiased`}>
        <AuthProvider>
          <TaskProvider>
            <Sidebar />
            <main className="pl-16">{children}</main>
            <Toaster position="bottom-center" />
          </TaskProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
