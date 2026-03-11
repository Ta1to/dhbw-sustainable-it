FROM node:20-alpine
WORKDIR /app

COPY next-template/package*.json ./
RUN npm install
COPY next-template/ ./
RUN npm run build

EXPOSE 3000
CMD ["npm", "start"]