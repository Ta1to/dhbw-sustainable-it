<script lang="ts">
  import { getCart, saveCart } from "$lib/cart";

  let { data } = $props();
  let feedback = $state(false);

  function addToCart() {
    const cart = getCart();
    const existing = cart.find((item) => item.id === data.product.id);
    if (existing) {
      existing.qty += 1;
    } else {
      cart.push({ id: data.product.id, qty: 1 });
    }
    saveCart(cart);
    feedback = true;
    setTimeout(() => (feedback = false), 2000);
  }
</script>

<a href="/products" class="btn btn-outline back-link">Products</a>

<div class="detail">
  <div class="detail-img">
    <img src={data.product.image} alt={data.product.name} />
  </div>
  <div class="info">
    <h1>{data.product.name}</h1>
    <p class="desc">{data.product.description}</p>
    <p class="price">{data.product.price.toFixed(2)}€</p>
    <button class="btn btn-primary" onclick={addToCart}>Add to cart</button>
    {#if feedback}<p class="feedback">Added to cart</p>{/if}
  </div>
</div>

<style>
  .back-link {
    margin-bottom: 2rem;
    display: inline-block;
  }
  .detail {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 4rem;
    align-items: center;
    min-height: 55vh;
  }
  .detail-img {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 2rem;
  }
  .detail-img img {
    width: 100%;
    aspect-ratio: 1;
    object-fit: cover;
    border-radius: 4px;
    display: block;
  }

  .info {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .info h1 {
    font-size: 1.6rem;
    margin: 0;
    font-weight: 600;
  }

  .desc {
    color: var(--muted);
    line-height: 1.6;
    font-size: 0.9rem;
  }

  .price {
    font-size: 1.8rem;
    font-weight: 700;
  }

  .feedback {
    color: var(--accent);
    font-size: 0.85rem;
  }
</style>