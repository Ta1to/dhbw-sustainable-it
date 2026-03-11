"use client";
import Link from "next/link";
import { useState, useEffect } from "react";
import type { Product } from "../lib/products";
import type { CartItem } from "../lib/cart";
import { getCart, saveCart } from "../lib/cart";

function formatPrice(n: number) {
  return n.toFixed(2) + "€";
}

export default function CartPage({ products }: { products: Product[] }) {
  const [cart, setCart] = useState<CartItem[]>([]);

  useEffect(() => {
    setCart(getCart());
  }, []);

  function updateCart(newCart: CartItem[]) {
    saveCart(newCart);
    setCart([...newCart]);
  }

  function remove(id: number) {
    updateCart(cart.filter((i) => i.id !== id));
  }

  function changeQty(id: number, action: "inc" | "dec") {
    const updated = cart
      .map((i) => i.id === id ? { ...i, qty: i.qty + (action === "inc" ? 1 : -1) } : i)
      .filter((i) => i.qty > 0);
    updateCart(updated);
  }

  const totalItems = cart.reduce((s, i) => s + i.qty, 0);
  const total = cart.reduce((s, item) => {
    const product = products.find((p) => p.id === item.id);
    return s + (product ? product.price * item.qty : 0);
  }, 0);

  return (
    <>
      <div className="cart-header">
        <h1>Shopping Cart</h1>
        {totalItems > 0 && (
          <span className="cart-count">{totalItems} item{totalItems !== 1 ? "s" : ""} in your cart</span>
        )}
      </div>

      {cart.length === 0 ? (
        <p className="muted">Your cart is empty. <Link href="/products">Continue shopping</Link></p>
      ) : (
        <>
          <table>
            <thead>
              <tr>
                <th>Product</th><th>Price</th><th>Quantity</th><th>Total</th><th></th>
              </tr>
            </thead>
            <tbody>
              {cart.map((item) => {
                const product = products.find((p) => p.id === item.id);
                if (!product) return null;
                return (
                  <tr key={item.id}>
                    <td>
                      <Link href={`/products/${product.id}`} className="product-link">
                        <img src={product.image} alt={product.name} className="thumb" />
                        <span className="product-name">{product.name}</span>
                      </Link>
                    </td>
                    <td>{formatPrice(product.price)}</td>
                    <td>
                      <div className="qty-ctrl">
                        <button className="qty-btn" onClick={() => changeQty(item.id, "dec")}>−</button>
                        <span>{item.qty}</span>
                        <button className="qty-btn" onClick={() => changeQty(item.id, "inc")}>+</button>
                      </div>
                    </td>
                    <td>{formatPrice(product.price * item.qty)}</td>
                    <td>
                      <button className="btn btn-danger" onClick={() => remove(item.id)}>Remove</button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          <div className="summary">
            <span>Total</span>
            <strong>{formatPrice(total)}</strong>
          </div>
          <div className="actions">
            <Link href="/products" className="btn btn-outline">Continue shopping</Link>
            <button className="btn btn-primary" onClick={() => alert("Checkout is not implemented in this demo.")}>
              Proceed to checkout
            </button>
          </div>
        </>
      )}
    </>
  );
}