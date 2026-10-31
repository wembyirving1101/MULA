import type { Metadata } from "next";
import "@/common/styles/globals.css";

export const metadata: Metadata = {
  title: "Mula · Your workspace",
  description: "A little clarity for your everyday operations.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
