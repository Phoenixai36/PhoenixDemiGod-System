#!/bin/bash

# Test script for nginx Containerfile
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE_NAME="phoenix-hydra/nginx-test"
CONTAINER_NAME="nginx-test-container"

echo "=== Testing Phoenix Hydra Nginx Containerfile ==="

# Cleanup any existing test containers
echo "Cleaning up existing test containers..."
podman rm -f $CONTAINER_NAME 2>/dev/null || true
podman rmi -f $IMAGE_NAME 2>/dev/null || true

# Create a test configuration without external dependencies
echo "Creating test configuration..."
cat > nginx-test.conf << 'EOF'
server {
    listen 8080;
    server_name localhost;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Main location for health checks
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }

    # Default location
    location / {
        return 200 "Phoenix Hydra Nginx Gateway - Test Mode\n";
        add_header Content-Type text/plain;
    }

    # Error pages
    error_page 500 502 503 504 /50x.html;
    location = /50x.html {
        root /usr/share/nginx/html;
    }
}
EOF

# Create test Containerfile
cat > Containerfile.test << 'EOF'
FROM nginx:alpine

# Create non-root user for nginx
RUN addgroup -g 1000 -S nginx-user && \
    adduser -u 1000 -D -S -G nginx-user nginx-user

# Create directories with proper permissions
RUN mkdir -p /var/cache/nginx /var/run /var/log/nginx && \
    chown -R nginx-user:nginx-user /var/cache/nginx /var/run /var/log/nginx && \
    chmod -R 755 /var/cache/nginx /var/run /var/log/nginx

# Create nginx configuration directory
RUN mkdir -p /etc/nginx/conf.d && \
    chown -R nginx-user:nginx-user /etc/nginx/conf.d

# Copy test nginx configuration (without external dependencies)
COPY nginx-test.conf /etc/nginx/conf.d/default.conf
RUN chown nginx-user:nginx-user /etc/nginx/conf.d/default.conf

# Create a custom nginx.conf for rootless execution
RUN mkdir -p /tmp/nginx && \
    chown nginx-user:nginx-user /tmp/nginx && \
    echo 'worker_processes auto;' > /etc/nginx/nginx.conf && \
    echo 'error_log /var/log/nginx/error.log warn;' >> /etc/nginx/nginx.conf && \
    echo 'pid /tmp/nginx/nginx.pid;' >> /etc/nginx/nginx.conf && \
    echo '' >> /etc/nginx/nginx.conf && \
    echo 'events {' >> /etc/nginx/nginx.conf && \
    echo '    worker_connections 1024;' >> /etc/nginx/nginx.conf && \
    echo '}' >> /etc/nginx/nginx.conf && \
    echo '' >> /etc/nginx/nginx.conf && \
    echo 'http {' >> /etc/nginx/nginx.conf && \
    echo '    include /etc/nginx/mime.types;' >> /etc/nginx/nginx.conf && \
    echo '    default_type application/octet-stream;' >> /etc/nginx/nginx.conf && \
    echo '' >> /etc/nginx/nginx.conf && \
    echo '    log_format main '"'"'$remote_addr - $remote_user [$time_local] "$request" '"'"' >> /etc/nginx/nginx.conf && \
    echo '                    '"'"'$status $body_bytes_sent "$http_referer" '"'"' >> /etc/nginx/nginx.conf && \
    echo '                    '"'"'"$http_user_agent" "$http_x_forwarded_for"'"'"';' >> /etc/nginx/nginx.conf && \
    echo '' >> /etc/nginx/nginx.conf && \
    echo '    access_log /var/log/nginx/access.log main;' >> /etc/nginx/nginx.conf && \
    echo '' >> /etc/nginx/nginx.conf && \
    echo '    sendfile on;' >> /etc/nginx/nginx.conf && \
    echo '    keepalive_timeout 65;' >> /etc/nginx/nginx.conf && \
    echo '' >> /etc/nginx/nginx.conf && \
    echo '    include /etc/nginx/conf.d/*.conf;' >> /etc/nginx/nginx.conf && \
    echo '}' >> /etc/nginx/nginx.conf

# Set proper ownership for nginx.conf
RUN chown nginx-user:nginx-user /etc/nginx/nginx.conf

# Switch to non-root user
USER nginx-user

# Expose port 8080 (non-privileged port)
EXPOSE 8080

# Start nginx in foreground
CMD ["nginx", "-g", "daemon off;"]
EOF

# Build the image
echo "Building nginx image..."
cd "$SCRIPT_DIR"
podman build -t $IMAGE_NAME -f Containerfile.test .

# Run the container
echo "Starting nginx container..."
podman run -d --name $CONTAINER_NAME -p 8080:8080 $IMAGE_NAME

# Wait for container to start
echo "Waiting for container to start..."
sleep 5

# Test health endpoint
echo "Testing health endpoint..."
if curl -f http://localhost:8080/health; then
    echo "✓ Health endpoint working"
else
    echo "✗ Health endpoint failed"
    exit 1
fi

# Test default endpoint
echo "Testing default endpoint..."
if curl -f http://localhost:8080/; then
    echo "✓ Default endpoint working"
else
    echo "✗ Default endpoint failed"
    exit 1
fi

# Check if running as non-root user
echo "Checking user context..."
USER_INFO=$(podman exec $CONTAINER_NAME id)
if echo "$USER_INFO" | grep -q "uid=1000"; then
    echo "✓ Running as non-root user: $USER_INFO"
else
    echo "✗ Not running as expected user: $USER_INFO"
    exit 1
fi

# Check nginx configuration
echo "Testing nginx configuration..."
if podman exec $CONTAINER_NAME nginx -t; then
    echo "✓ Nginx configuration is valid"
else
    echo "✗ Nginx configuration is invalid"
    exit 1
fi

# Check file permissions
echo "Checking file permissions..."
podman exec $CONTAINER_NAME ls -la /var/log/nginx/
podman exec $CONTAINER_NAME ls -la /var/cache/nginx/
podman exec $CONTAINER_NAME ls -la /etc/nginx/conf.d/

# Show container logs
echo "Container logs:"
podman logs $CONTAINER_NAME

echo "=== All tests passed! ==="

# Cleanup
echo "Cleaning up..."
podman stop $CONTAINER_NAME
podman rm $CONTAINER_NAME
podman rmi $IMAGE_NAME

# Remove temporary test files
rm -f nginx-test.conf Containerfile.test

echo "Test completed successfully!"