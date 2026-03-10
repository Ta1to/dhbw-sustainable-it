import { getProductById } from "$lib/products";
import { redirect } from "@sveltejs/kit";
import type { PageServerLoad } from "./$types";

export const load: PageServerLoad = ({ params }) => {
  const product = getProductById(Number(params.id));
  if (!product) redirect(302, "/");
  return { product };
};