import "./globals.css";
import { ReactNode } from "react";
import { Providers } from "@/app/providers";

export const metadata = {
  title: "InterviewAI",
  description: "AI-powered pre-selection interviews",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <Providers>
          <div className="min-h-dvh bg-background text-foreground">
            <main className="container py-8">{children}</main>
          </div>
        </Providers>
      </body>
    </html>
  );
}
