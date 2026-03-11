<script lang="ts">
  import { onMount } from "svelte";
  import { getCart } from "$lib/cart";
  import "../app.css";

  let { children } = $props();
  let cartCount = $state(0);

  function updateBadge() {
    const cart = getCart();
    cartCount = cart.reduce((sum, item) => sum + item.qty, 0);
  }

  onMount(() => {
    updateBadge();
    window.addEventListener("cart-updated", updateBadge);
    return () => window.removeEventListener("cart-updated", updateBadge);
  });
</script>

<svelte:head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta name="description" content="Shop the latest trends — carefully curated products for your lifestyle." />
  <link rel="icon" type="image/png" href="/favicon.png" />
</svelte:head>

<nav>
  <a href="/" class="brand">svelte</a>
  <div class="nav-links">
    <a href="/">home</a>
    <a href="/products">products</a>
  </div>
  <a href="/cart" class="cart-link">
    cart{#if cartCount > 0}<span class="badge">{cartCount}</span>{/if}
  </a>
</nav>

<main>
  {@render children()}
</main>