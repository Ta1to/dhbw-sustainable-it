import { getProducts } from "$lib/products";
export function load() {
  return { products: getProducts() };
}