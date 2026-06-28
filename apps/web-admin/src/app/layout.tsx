import type { Metadata } from "next";
import "./globals.css";
import { AppProviders } from "@/components/providers";

export const metadata: Metadata = {
  title: "振航工业数字生态系统",
  description: "ZhenHang Industrial OS",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="zh-CN" className="h-full antialiased">
      <body className="min-h-full bg-[var(--color-bg)] text-[var(--color-text)]">
        <AppProviders>{children}</AppProviders>
      </body>
    </html>
  );
}
