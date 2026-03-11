"use client";

import Link from "next/link";
import { useState, useEffect } from "react";
import { getCart } from "../lib/cart";

export default function CartBadge() {
  const [count, setCount] = useState(0);

  function update() {
    const total = getCart().reduce((sum, item) => sum + item.qty, 0);
    setCount(total);
  }

  useEffect(() => {
    update();
    window.addEventListener("cart-updated", update);
    return () => window.removeEventListener("cart-updated", update);
  }, []);

  return (
    <Link href="/cart" className="cart-link">
      cart{count > 0 && <span className="badge">{count}</span>}
    </Link>
  );
}