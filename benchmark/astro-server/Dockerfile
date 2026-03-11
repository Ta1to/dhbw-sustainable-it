FROM node:20-alpine

WORKDIR /app

COPY ../../astro-template/package*.json ./
RUN npm install

COPY ../../astro-template/ ./
RUN npm run build

EXPOSE 4321
CMD ["node", "./dist/server/entry.mjs"]