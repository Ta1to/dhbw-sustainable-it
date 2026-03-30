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

# Next-App bauen
COPY next-template/package*.json ./
RUN npm install
COPY next-template/ ./

ENV DATABASE_PATH=/app/database/shop.db
RUN npm run build

EXPOSE 3000
ENV HOSTNAME=0.0.0.0
ENV PORT=3000

CMD ["node", "node_modules/.bin/next", "start"]