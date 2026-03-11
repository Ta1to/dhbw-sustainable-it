FROM node:20-alpine
WORKDIR /app

COPY svelte-template/package*.json ./
RUN npm install
COPY svelte-template/ ./
RUN npm run build

EXPOSE 5173
CMD ["node", "build"]