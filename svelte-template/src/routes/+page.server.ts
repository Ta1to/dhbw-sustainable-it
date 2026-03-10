import { getProducts } from "$lib/products";

export function load() {
  const products = getProducts();
  return { featured: products[2] };
}