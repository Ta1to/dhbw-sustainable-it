import { getProductById } from "$lib/products";

export function load() {
  return { featured: getProductById(3) };
}