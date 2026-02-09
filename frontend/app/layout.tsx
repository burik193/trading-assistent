import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Financial Assistant",
  description: "Stock analysis and financial advice",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-[var(--background)] text-[var(--foreground)] antialiased">
        {children}
      </body>
    </html>
  );
}
