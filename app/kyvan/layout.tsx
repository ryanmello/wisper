import Navbar from "@/components/kyvan/Navbar";

export default function VedaLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-white">
      <Navbar />
      <main className="pl-0">
        {children}
      </main>
    </div>
  );
} 