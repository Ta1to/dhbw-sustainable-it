FROM node:20-alpine
WORKDIR /app

COPY database/package*.json ./database/
RUN cd database && npm install

COPY database/ ./database/
RUN cd database && npx tsx seed.ts

COPY next-template/package*.json ./
RUN npm install
COPY next-template/ ./

ENV DATABASE_PATH=/app/database/shop.db

RUN npm run build

EXPOSE 3000
CMD ["npm", "start"]