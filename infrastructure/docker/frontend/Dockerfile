# Build stage: compile the React app into static assets.
FROM node:22-alpine AS build

WORKDIR /app

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./

ARG VITE_API_BASE_URL=/api/v1
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

RUN npm run build

# Serve stage: nginx with SPA fallback routing.
FROM nginx:1.27-alpine

COPY infrastructure/docker/frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY infrastructure/docker/frontend/security-headers.conf /etc/nginx/snippets/security-headers.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
