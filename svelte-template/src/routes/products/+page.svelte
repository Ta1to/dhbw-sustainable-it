<script lang="ts">
  let { data } = $props();
</script>

<h1>Products</h1>
<div class="grid">
  {#each data.products as p}
    <a href="/products/{p.id}" class="card">
      <div class="card-img">
        <img src={p.image} alt={p.name} />
      </div>
      <div class="card-body">
        <h2>{p.name}</h2>
        <p class="desc">{p.description}</p>
        <p class="price">{p.price.toFixed(2)}€</p>
      </div>
    </a>
  {/each}
</div>

<style>
  .grid { 
    display: grid; 
    grid-template-columns: 
    repeat(auto-fill, 
    minmax(220px, 1fr)); 
    gap: 1rem; 
}
  .card { 
    background: var(--surface); 
    border: 1px solid var(--border); 
    border-radius: var(--radius); 
    text-decoration: none; 
    color: inherit; 
    overflow: hidden; 
    display: flex; 
    flex-direction: column; 
    transition: border-color 0.15s; 
  }
  .card:hover { 
    border-color: var(--muted); 
  }
  .card-img { 
    background: var(--surface); 
    display: flex; 
    align-items: center; 
    justify-content: center; 
    padding: 1.25rem; 
  }
  .card-img img { 
    width: 100%; 
    aspect-ratio: 1; 
    object-fit: cover; 
    border-radius: 4px; 
  }
  .card-body { 
    padding: 0.9rem 1rem 1rem; 
    display: flex; 
    flex-direction: column; 
    gap: 0.3rem; 
    flex: 1; 
  }
  .card-body h2 { 
    font-size: 0.9rem; 
    font-weight: 600; 
    margin: 0; 
  }
  .desc { 
    font-size: 0.78rem; 
    color: var(--muted); 
    line-height: 1.4; 
    display: -webkit-box; 
    -webkit-line-clamp: 2; 
    -webkit-box-orient: vertical; 
    overflow: hidden; 
  }
  .price { 
    font-size: 0.95rem; 
    font-weight: 700; 
    margin-top: 0.5rem; 
  }
</style>