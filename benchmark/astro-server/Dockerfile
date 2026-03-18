FROM node:20-alpine

# Build-Tools für better-sqlite3 (HTTP statt HTTPS wegen Proxy/TLS)
RUN echo "http://dl-cdn.alpinelinux.org/alpine/v3.21/main" > /etc/apk/repositories && \
    echo "http://dl-cdn.alpinelinux.org/alpine/v3.21/community" >> /etc/apk/repositories && \
    apk add --no-cache --allow-untrusted python3 make g++

WORKDIR /app

# DB seeden
COPY database/package*.json ./database/
RUN cd database && npm install
COPY database/ ./database/
RUN cd database && npx tsx seed.ts

# Astro-App bauen
COPY astro-template/package*.json ./
RUN npm install
COPY astro-template/ ./

ENV DATABASE_PATH=/app/database/shop.db
RUN npm run build

EXPOSE 4321
ENV HOST=0.0.0.0
ENV PORT=4321

CMD ["node", "./dist/server/entry.mjs"]