#!/usr/bin/env sh
set -eu

: "${API_UPSTREAM:?API_UPSTREAM is required (e.g. https://breatheesg-backend.onrender.com)}"

envsubst '${API_UPSTREAM}' < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf

exec nginx -g 'daemon off;'
