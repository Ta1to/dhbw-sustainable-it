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

# Svelte-App bauen
COPY svelte-template/package*.json ./
RUN npm install
# adapter-node für Docker-Deployment
RUN npm install @sveltejs/adapter-node
COPY svelte-template/ ./

# svelte.config.js auf adapter-node umstellen
RUN echo 'import adapter from "@sveltejs/adapter-node";' > svelte.config.js && \
    echo 'const config = { kit: { adapter: adapter() } };' >> svelte.config.js && \
    echo 'export default config;' >> svelte.config.js

ENV DATABASE_PATH=/app/database/shop.db

RUN npx svelte-kit sync
RUN npm run build

EXPOSE 5173
ENV HOST=0.0.0.0
ENV PORT=5173
ENV ORIGIN=http://localhost:5173

CMD ["node", "build"]