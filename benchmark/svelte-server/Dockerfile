FROM node:20-alpine
WORKDIR /app

COPY database/package*.json ./database/
RUN cd database && npm install

COPY database/ ./database/
RUN cd database && npx tsx seed.ts

COPY svelte-template/package*.json ./
RUN npm install
COPY svelte-template/ ./

ENV DATABASE_PATH=/app/database/shop.db

RUN npx svelte-kit sync
RUN npm run build

EXPOSE 5173
CMD ["node", "build"]