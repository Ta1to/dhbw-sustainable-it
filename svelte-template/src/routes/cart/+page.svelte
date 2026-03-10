<script lang="ts">
  import { onMount } from "svelte";
  import { getCart, saveCart } from "$lib/cart";
  import type { Product } from "$lib/products";

  let { data } = $props();

  type CartItem = { id: number; qty: number };
  let cart = $state<CartItem[]>([]);

  onMount(() => {
    cart = getCart();
    const sync = () => { cart = getCart(); };
    window.addEventListener("cart-updated", sync);
    return () => window.removeEventListener("cart-updated", sync);
  });

  function getProduct(id: number): Product | undefined {
    return data.products.find((p) => p.id === id);
  }

  function formatPrice(n: number) {
    return n.toFixed(2) + "€";
  }

  function remove(id: number) {
    saveCart(cart.filter((i) => i.id !== id));
    cart = getCart();
  }

  function changeQty(id: number, action: "inc" | "dec") {
    const updated = cart
      .map((i) => i.id === id ? { ...i, qty: i.qty + (action === "inc" ? 1 : -1) } : i)
      .filter((i) => i.qty > 0);
    saveCart(updated);
    cart = getCart();
  }

  let totalItems = $derived(cart.reduce((s, i) => s + i.qty, 0));
  let total = $derived(
    cart.reduce((s, i) => {
      const p = getProduct(i.id);
      return s + (p ? p.price * i.qty : 0);
    }, 0)
  );
</script>

<div class="cart-header">
  <h1>Shopping Cart</h1>
  {#if totalItems > 0}
    <span class="cart-count">{totalItems} item{totalItems !== 1 ? "s" : ""} in your cart</span>
  {/if}
</div>

{#if cart.length === 0}
  <p class="muted">Your cart is empty. <a href="/products">Continue shopping</a></p>
{:else}
  <table>
    <thead>
      <tr>
        <th>Product</th>
        <th>Price</th>
        <th>Quantity</th>
        <th>Total</th>
        <th></th>
      </tr>
    </thead>
    <tbody>
      {#each cart as item}
        {@const product = getProduct(item.id)}
        {#if product}
          <tr>
            <td>
              <a href="/products/{product.id}" class="product-link">
                <img src={product.image} alt={product.name} class="thumb" />
                <span class="product-name">{product.name}</span>
              </a>
            </td>
            <td>{formatPrice(product.price)}</td>
            <td>
              <div class="qty-ctrl">
                <button class="qty-btn" onclick={() => changeQty(item.id, "dec")}>−</button>
                <span>{item.qty}</span>
                <button class="qty-btn" onclick={() => changeQty(item.id, "inc")}>+</button>
              </div>
            </td>
            <td>{formatPrice(product.price * item.qty)}</td>
            <td>
              <button class="btn btn-danger remove-btn" onclick={() => remove(item.id)}>Remove</button>
            </td>
          </tr>
        {/if}
      {/each}
    </tbody>
  </table>

  <div class="summary">
    <span>Total</span>
    <strong>{formatPrice(total)}</strong>
  </div>

  <div class="actions">
    <a href="/products" class="btn btn-outline">Continue shopping</a>
    <button class="btn btn-primary" onclick={() => alert("Checkout is not implemented in this demo.")}>
      Proceed to checkout
    </button>
  </div>
{/if}

<style>
  .cart-header {
    display: flex;
    align-items: baseline;
    gap: 1rem;
    margin-bottom: 1.5rem;
  }

  .cart-header h1 { 
    margin: 0; 
  }

  .cart-count { 
    font-size: 0.85rem; 
    color: var(--muted); 
  }

  .muted { 
    color: var(--muted); 
    font-size: 0.9rem; 
  }

  .muted a { 
    color: var(--text); 
  }

  table { 
    width: 100%; 
    border-collapse: collapse; 
  }

  th, td {
    padding: 1rem 0.75rem;
    text-align: left;
    border-bottom: 1px solid var(--border);
    font-size: 0.88rem;
    vertical-align: middle;
  }

  th { 
    font-weight: 500; 
    font-size: 0.78rem; 
    color: var(--muted); 
  }

  tbody tr:last-child td { 
    border-bottom: none; 
  }

  .product-link {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    text-decoration: none;
    color: inherit;
  }

  .product-link:hover .product-name { 
    color: var(--muted);
  }

  .thumb {
    width: 36px;
    height: 36px;
    object-fit: cover;
    border-radius: 4px;
    flex-shrink: 0;
    background: var(--surface);
  }

  .product-name {
    font-weight: 500;
    font-size: 0.88rem;
    max-width: 220px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .qty-ctrl { 
    display: flex; 
    align-items: center; 
    gap: 0.6rem; 
    font-size: 0.88rem; 
  }

  .qty-btn {
    width: 24px;
    height: 24px;
    border: 1px solid var(--border);
    border-radius: 4px;
    background: transparent;
    color: var(--text);
    cursor: pointer;
    font-size: 0.9rem;
    line-height: 1;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .qty-btn:hover { 
    border-color: var(--muted); 
  }

  .summary {
    display: flex;
    justify-content: flex-end;
    align-items: center;
    gap: 0.75rem;
    margin-top: 1.5rem;
    padding-top: 1.25rem;
    border-top: 1px solid var(--border);
    font-size: 0.9rem;
    color: var(--muted);
  }

  .summary strong { 
    font-size: 1.2rem; 
    color: var(--text); 
    font-weight: 600; 
  }

  .actions {
    display: flex;
    gap: 1rem;
    margin-top: 1.5rem;
    justify-content: flex-end;
  }

  .remove-btn { 
    font-size: 0.78rem; 
    padding: 0.3rem 0.75rem; 
  }
</style>