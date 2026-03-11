import { getProducts } from "../lib/products";
import CartPage from "../components/CartPage";

export default function Cart() {
  const products = getProducts();
  return <CartPage products={products} />;
}