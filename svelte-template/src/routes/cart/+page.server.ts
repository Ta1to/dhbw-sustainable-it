import { getProducts } from "$lib/products";
import type { PageServerLoad } from "./$types";

export const load: PageServerLoad = () => {
  return { products: getProducts() };
};