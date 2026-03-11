<script setup lang="ts">
import { ref } from 'vue';
import { getCart, saveCart } from '../lib/cart';

const props = defineProps<{ productId: number }>();
const feedback = ref(false);

function addToCart() {
  const cart = getCart();
  const existing = cart.find(i => i.id === props.productId);
  if (existing) existing.qty += 1;
  else cart.push({ id: props.productId, qty: 1 });
  saveCart(cart);
  feedback.value = true;
  setTimeout(() => (feedback.value = false), 2000);
}
</script>

<template>
  <button class="btn btn-primary" @click="addToCart">Add to cart</button>
  <p v-if="feedback" class="feedback">Added to cart</p>
</template>