import "./globals.css";
import { DM_Sans } from "next/font/google";
import type { Metadata } from "next";
import type { ReactNode } from "react";

const dmSans = DM_Sans({
  subsets: ["latin"],
  weight: ["300", "400", "500"],
  variable: "--font-dm-sans",
  display: "swap",
});

export const metadata: Metadata = {
  title: "PrismaLab",
  description: "PrismaLab — research synthesis platform.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className={dmSans.variable}>
      <body>{children}</body>
    </html>
  );
}
