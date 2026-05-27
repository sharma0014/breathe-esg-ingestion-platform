FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json /app/
RUN npm ci
COPY . /app
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
RUN apk add --no-cache gettext

# Render a runtime Nginx config from env so the frontend can proxy to the backend
COPY nginx.conf.template /etc/nginx/templates/default.conf.template
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

ENV API_UPSTREAM=""
ENTRYPOINT ["/docker-entrypoint.sh"]
EXPOSE 80
