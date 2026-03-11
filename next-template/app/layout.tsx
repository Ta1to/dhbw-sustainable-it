import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";
import CartBadge from "./components/CartBadge";

export const metadata: Metadata = {
  title: "Shop",
  description: "Shop the latest trends — carefully curated products for your lifestyle.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <nav>
          <Link href="/" className="brand">next</Link>
          <div className="nav-links">
            <Link href="/">home</Link>
            <Link href="/products">products</Link>
          </div>
          <CartBadge />
        </nav>
        <main>{children}</main>
      </body>
    </html>
  );
}