import type { ReactNode } from "react";

export const metadata = {
  title: "Agencia Automatizada",
  description: "Trading department, XAU/USD Market Analysis (MVP-0 foundation)",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
