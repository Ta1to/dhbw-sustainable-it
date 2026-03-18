FROM node:20-alpine

WORKDIR /app

COPY database/package*.json ./
RUN npm install

COPY database/ ./

# SQLite DB erzeugen
RUN npx tsx seed.ts

# DB-Datei in ein Volume-Verzeichnis kopieren
CMD ["cp", "/app/shop.db", "/data/shop.db"]