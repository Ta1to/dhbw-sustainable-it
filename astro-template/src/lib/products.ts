import Database from "better-sqlite3";
import path from "path";
import fs from "fs";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const dbPath = process.env.DATABASE_PATH
  ? path.resolve(process.env.DATABASE_PATH)
  : path.resolve("database/shop.db");
const db = new Database(dbPath, { readonly: true });

export interface Product {
  id: number;
  name: string;
  price: number;
  description: string;
  image: string;
  category: string;
}

export function getProducts(): Product[] {
  return db.prepare("SELECT * FROM products").all() as Product[];
}

export function getProductById(id: number): Product | undefined {
  return db.prepare("SELECT * FROM products WHERE id = ?").get(id) as Product | undefined;
}
