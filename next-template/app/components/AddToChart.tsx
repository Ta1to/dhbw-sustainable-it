"use client";
import { useState } from "react";
import { getCart, saveCart } from "../lib/cart";

export default function AddToCart({ productId }: { productId: number }) {
  const [feedback, setFeedback] = useState(false);

  function handleClick() {
    const cart = getCart();
    const existing = cart.find((item) => item.id === productId);
    if (existing) {
      existing.qty += 1;
    } else {
      cart.push({ id: productId, qty: 1 });
    }
    saveCart(cart);
    setFeedback(true);
    setTimeout(() => setFeedback(false), 2000);
  }

  return (
    <>
      <button className="btn btn-primary" onClick={handleClick}>Add to cart</button>
      {feedback && <p className="feedback">Added to cart</p>}
    </>
  );
}