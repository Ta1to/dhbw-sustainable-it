export interface Product {
  id: number;
  name: string;
  price: number;
  description: string;
  image: string;
  category: string;
}

export const products: Product[] = [
  {
    id: 1,
    name: "Mechanical Keyboard",
    price: 89.99,
    description: "Compact TKL mechanical keyboard with Cherry MX switches. Great tactile feedback for everyday use.",
    image: "https://picsum.photos/seed/keyboard/600/400",
    category: "Electronics",
  },
  {
    id: 2,
    name: "Wireless Mouse",
    price: 34.99,
    description: "Ergonomic wireless mouse with 3-month battery life and silent click technology.",
    image: "https://picsum.photos/seed/mouse/600/400",
    category: "Electronics",
  },
  {
    id: 3,
    name: "Monitor Stand",
    price: 49.99,
    description: "Adjustable aluminum monitor stand with built-in USB hub. Raises your screen to eye level.",
    image: "https://picsum.photos/seed/stand/600/400",
    category: "Accessories",
  },
  {
    id: 4,
    name: "USB-C Hub",
    price: 29.99,
    description: "7-in-1 USB-C hub with HDMI 4K, 3x USB-A, SD card reader and 100W PD passthrough.",
    image: "https://picsum.photos/seed/hub/600/400",
    category: "Accessories",
  },
  {
    id: 5,
    name: "Desk Lamp",
    price: 44.99,
    description: "LED desk lamp with adjustable color temperature and brightness. Eye-care mode included.",
    image: "https://picsum.photos/seed/lamp/600/400",
    category: "Accessories",
  },
  {
    id: 6,
    name: "Webcam HD",
    price: 64.99,
    description: "1080p webcam with built-in microphone, auto-focus and privacy cover.",
    image: "https://picsum.photos/seed/webcam/600/400",
    category: "Electronics",
  },
];

export function getProductById(id: number): Product | undefined {
  return products.find((p) => p.id === id);
}
