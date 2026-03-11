import Link from "next/link";
import { getProducts } from "./lib/products";

export default function Home() {
  const products = getProducts();
  const featured = products[2];

  return (
    <div className="hero">
      <div className="hero-text">
        <h1>New Arrivals</h1>
        <p>Shop the latest trends — carefully curated products for your lifestyle.</p>
        <Link href="/products" className="btn btn-primary">Shop Now</Link>
      </div>
      <div className="hero-img">
        {featured && <img src={featured.image} alt={featured.name} />}
      </div>
    </div>
  );
}