#!/bin/sh
set -eu

if [ "${DOCS_PUBLIC_ENABLED:-false}" = "true" ]; then
    config=/opt/diddishop-docs/nginx-enabled.conf
else
    config=/opt/diddishop-docs/nginx-disabled.conf
fi

cp "$config" /etc/nginx/conf.d/default.conf
exec nginx -g 'daemon off;'
