FROM node:20-alpine

WORKDIR /app

COPY database/package*.json ./database/
RUN cd database && npm install

COPY database/ ./database/
RUN cd database && npx tsx seed.ts

COPY ../../astro-template/package*.json ./
RUN npm install

COPY ../../astro-template/ ./

ENV DATABASE_PATH=/app/database/shop.db

RUN npm run build

EXPOSE 4321
CMD ["node", "./dist/server/entry.mjs"]