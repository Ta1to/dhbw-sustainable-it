export interface CartItem {
  id: number;
  qty: number;
}

export function getCart(): CartItem[] {
  try {
    return JSON.parse(sessionStorage.getItem("cart") || "[]");
  } catch {
    return [];
  }
}

export function saveCart(cart: CartItem[]): void {
  sessionStorage.setItem("cart", JSON.stringify(cart));
  window.dispatchEvent(new Event("cart-updated"));
}