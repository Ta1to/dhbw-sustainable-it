<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { getCart } from '../lib/cart';

const count = ref(0);
function update() {
  count.value = getCart().reduce((sum, item) => sum + item.qty, 0);
}
onMounted(() => {
  update();
  window.addEventListener('cart-updated', update);
});
</script>

<template>
  <a href="/cart" class="cart-link">
    cart<span v-if="count > 0" class="badge">{{ count }}</span>
  </a>
</template>