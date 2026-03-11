<script setup lang="ts">
import { ref, computed } from 'vue';
import { getCart, saveCart } from '../lib/cart';
import type { Product } from '../lib/products';

const props = defineProps<{ products: Product[] }>();

const cart = ref(getCart());

const cartItems = computed(() =>
  cart.value
    .map(item => {
      const product = props.products.find(p => p.id === item.id);
      return product ? { ...item, product } : null;
    })
    .filter(Boolean) as Array<{ id: number; qty: number; product: Product }>
);

const total = computed(() =>
  cartItems.value.reduce((sum, item) => sum + item.product.price * item.qty, 0)
);

const totalItems = computed(() =>
  cart.value.reduce((sum, item) => sum + item.qty, 0)
);

function formatPrice(n: number) {
  return n.toFixed(2) + '€';
}

function changeQty(id: number, delta: number) {
  const updated = cart.value
    .map(i => i.id === id ? { ...i, qty: i.qty + delta } : i)
    .filter(i => i.qty > 0);
  saveCart(updated);
  cart.value = updated;
}

function remove(id: number) {
  const updated = cart.value.filter(i => i.id !== id);
  saveCart(updated);
  cart.value = updated;
}

function checkout() {
  alert('Checkout is not implemented in this demo.');
}
</script>

<template>
  <div class="cart-header">
    <h1>Shopping Cart</h1>
    <span v-if="totalItems > 0" class="cart-count">
      {{ totalItems }} item{{ totalItems !== 1 ? 's' : '' }} in your cart
    </span>
  </div>

  <div v-if="cartItems.length === 0">
    <p class="muted">Your cart is empty. <a href="/products">Continue shopping</a></p>
  </div>

  <div v-else>
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
        <tr v-for="item in cartItems" :key="item.id">
          <td>
            <a :href="`/products/${item.product.id}`" class="product-link">
              <img :src="item.product.image" :alt="item.product.name" class="thumb" />
              <span class="product-name">{{ item.product.name }}</span>
            </a>
          </td>
          <td>{{ formatPrice(item.product.price) }}</td>
          <td>
            <div class="qty-ctrl">
              <button class="qty-btn" @click="changeQty(item.id, -1)">−</button>
              <span>{{ item.qty }}</span>
              <button class="qty-btn" @click="changeQty(item.id, 1)">+</button>
            </div>
          </td>
          <td>{{ formatPrice(item.product.price * item.qty) }}</td>
          <td>
            <button class="btn btn-danger remove-btn" @click="remove(item.id)">Remove</button>
          </td>
        </tr>
      </tbody>
    </table>

    <div class="summary">
      <span>Total</span>
      <strong>{{ formatPrice(total) }}</strong>
    </div>

    <div class="actions">
      <a href="/products" class="btn btn-outline">Continue shopping</a>
      <button class="btn btn-primary" @click="checkout">Proceed to checkout</button>
    </div>
  </div>
</template>
