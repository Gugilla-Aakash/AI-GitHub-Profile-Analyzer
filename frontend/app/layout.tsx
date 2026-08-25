import type { Metadata } from "next";
import QueryProvider from "@/providers/QueryProvider";
import Sidebar from "components/SideBar";
import "./globals.css";
import { Suspense } from "react";

export const metadata: Metadata = {
  title: "GitHub Profile Analyzer",
  description: "Analyze, score, and chat with GitHub developer profiles.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark" data-scroll-behavior="smooth">
      <body className="bg-neo-light dark:bg-neo-dark text-gray-800 dark:text-gray-200 antialiased h-screen flex overflow-hidden">
        <QueryProvider>
          {/* Wrapped Sidebar in Suspense to prevent CSR bailout on 404 pages */}
          <Suspense
            fallback={
              <div className="w-64 h-screen flex-shrink-0 bg-neo-light dark:bg-neo-dark hidden md:block border-r border-gray-200/50 dark:border-gray-800/50" />
            }
          >
            <Sidebar />
          </Suspense>
          <div className="flex-1 h-full overflow-y-auto scrollbar-none">
            {children}
          </div>
        </QueryProvider>
      </body>
    </html>
  );
}
