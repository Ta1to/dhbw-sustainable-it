import Link from "next/link";
import { notFound } from "next/navigation";
import { getProductById } from "../../lib/products";
import AddToCart from "../../components/AddToChart";

export default async function ProductPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const product = getProductById(Number(id));
  if (!product) notFound();

  return (
    <>
      <Link href="/products" className="btn btn-outline back-link">Products</Link>
      <div className="detail">
        <div className="detail-img">
          <img src={product.image} alt={product.name} />
        </div>
        <div className="info">
          <h1>{product.name}</h1>
          <p className="desc">{product.description}</p>
          <p className="price">{product.price.toFixed(2)}€</p>
          <AddToCart productId={product.id} />
        </div>
      </div>
    </>
  );
}