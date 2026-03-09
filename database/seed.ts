import Database from "better-sqlite3";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const db = new Database(path.resolve(__dirname, "shop.db"));

db.exec(`
  CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    price REAL NOT NULL,
    description TEXT NOT NULL,
    image TEXT NOT NULL,
    category TEXT NOT NULL
  )
`);

const insert = db.prepare(`
  INSERT OR REPLACE INTO products (id, name, price, description, image, category)
  VALUES (@id, @name, @price, @description, @image, @category)
`);

const products = [
  {
    id: 1,
    name: "Mechanical Keyboard",
    price: 89.99,
    description: "Compact TKL mechanical keyboard with Cherry MX switches. Great tactile feedback for everyday use.",
    image: "https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=600&h=400&fit=crop",
    category: "Electronics",
  },
  {
    id: 2,
    name: "Wireless Mouse",
    price: 34.99,
    description: "Ergonomic wireless mouse with 3-month battery life and silent click technology.",
    image: "https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?w=600&h=400&fit=crop",
    category: "Electronics",
  },
  {
    id: 3,
    name: "Monitor Stand",
    price: 49.99,
    description: "Adjustable aluminum monitor stand with built-in USB hub. Raises your screen to eye level.",
    image: "https://images.unsplash.com/photo-1593642632559-0c6d3fc62b89?w=600&h=400&fit=crop",
    category: "Accessories",
  },
  {
    id: 4,
    name: "USB-C Hub",
    price: 29.99,
    description: "7-in-1 USB-C hub with HDMI 4K, 3x USB-A, SD card reader and 100W PD passthrough.",
    image: "https://images.unsplash.com/photo-1625895197185-efcec01cffe0?w=600&h=400&fit=crop",
    category: "Accessories",
  },
  {
    id: 5,
    name: "Desk Lamp",
    price: 44.99,
    description: "LED desk lamp with adjustable color temperature and brightness. Eye-care mode included.",
    image: "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=600&h=400&fit=crop",
    category: "Accessories",
  },
  {
    id: 6,
    name: "Webcam HD",
    price: 64.99,
    description: "1080p webcam with built-in microphone, auto-focus and privacy cover.",
    image: "https://images.unsplash.com/photo-1587825140708-dfaf72ae4b04?w=600&h=400&fit=crop",
    category: "Electronics",
  },
];

for (const product of products) {
  insert.run(product);
}

console.log(`shop.db seeded with ${products.length} products.`);
db.close();
