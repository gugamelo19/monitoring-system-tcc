import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "InfraGuard",
  description: "Sistema inteligente de monitoramento de infraestrutura de TI",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  );
}