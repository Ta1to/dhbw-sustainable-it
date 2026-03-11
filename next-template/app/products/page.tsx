import Link from "next/link";
import { getProducts } from "../lib/products";

export default function ProductsPage() {
  const products = getProducts();

  return (
    <>
      <h1>Products</h1>
      <div className="grid">
        {products.map((p) => (
          <Link key={p.id} href={`/products/${p.id}`} className="card">
            <div className="card-img">
              <img src={p.image} alt={p.name} />
            </div>
            <div className="card-body">
              <h2>{p.name}</h2>
              <p className="desc">{p.description}</p>
              <p className="price">{p.price.toFixed(2)}€</p>
            </div>
          </Link>
        ))}
      </div>
    </>
  );
}