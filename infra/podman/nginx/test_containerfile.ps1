# Test script for nginx Containerfile (PowerShell)
param(
    [switch]$SkipCleanup
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ImageName = "phoenix-hydra/nginx-test"
$ContainerName = "nginx-test-container"

Write-Host "=== Testing Phoenix Hydra Nginx Containerfile ===" -ForegroundColor Green

# Cleanup any existing test containers
Write-Host "Cleaning up existing test containers..." -ForegroundColor Yellow
try {
    podman rm -f $ContainerName 2>$null
    podman rmi -f $ImageName 2>$null
} catch {
    # Ignore cleanup errors
}

# Create a test configuration without external dependencies
Write-Host "Creating test configuration..." -ForegroundColor Yellow
@"
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
"@ | Out-File -FilePath "nginx-test.conf" -Encoding UTF8

# Create test Containerfile
@"
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
    echo '    log_format main '"'"'`$remote_addr - `$remote_user [`$time_local] "`$request" '"'"' >> /etc/nginx/nginx.conf && \
    echo '                    '"'"'`$status `$body_bytes_sent "`$http_referer" '"'"' >> /etc/nginx/nginx.conf && \
    echo '                    '"'"'"`$http_user_agent" "`$http_x_forwarded_for"'"'"';' >> /etc/nginx/nginx.conf && \
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
"@ | Out-File -FilePath "Containerfile.test" -Encoding UTF8

# Build the image
Write-Host "Building nginx image..." -ForegroundColor Yellow
Set-Location $ScriptDir
podman build -t $ImageName -f Containerfile.test .

# Run the container
Write-Host "Starting nginx container..." -ForegroundColor Yellow
podman run -d --name $ContainerName -p 8080:8080 $ImageName

# Wait for container to start
Write-Host "Waiting for container to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

try {
    # Test health endpoint
    Write-Host "Testing health endpoint..." -ForegroundColor Yellow
    $healthResponse = Invoke-WebRequest -Uri "http://localhost:8080/health" -UseBasicParsing
    if ($healthResponse.StatusCode -eq 200) {
        Write-Host "✓ Health endpoint working" -ForegroundColor Green
    } else {
        throw "Health endpoint returned status: $($healthResponse.StatusCode)"
    }

    # Test default endpoint
    Write-Host "Testing default endpoint..." -ForegroundColor Yellow
    $defaultResponse = Invoke-WebRequest -Uri "http://localhost:8080/" -UseBasicParsing
    if ($defaultResponse.StatusCode -eq 200) {
        Write-Host "✓ Default endpoint working" -ForegroundColor Green
    } else {
        throw "Default endpoint returned status: $($defaultResponse.StatusCode)"
    }

    # Check if running as non-root user
    Write-Host "Checking user context..." -ForegroundColor Yellow
    $userInfo = podman exec $ContainerName id
    if ($userInfo -match "uid=1000") {
        Write-Host "✓ Running as non-root user: $userInfo" -ForegroundColor Green
    } else {
        throw "Not running as expected user: $userInfo"
    }

    # Check nginx configuration
    Write-Host "Testing nginx configuration..." -ForegroundColor Yellow
    $configTest = podman exec $ContainerName nginx -t
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Nginx configuration is valid" -ForegroundColor Green
    } else {
        throw "Nginx configuration is invalid"
    }

    # Check file permissions
    Write-Host "Checking file permissions..." -ForegroundColor Yellow
    podman exec $ContainerName ls -la /var/log/nginx/
    podman exec $ContainerName ls -la /var/cache/nginx/
    podman exec $ContainerName ls -la /etc/nginx/conf.d/

    # Show container logs
    Write-Host "Container logs:" -ForegroundColor Yellow
    podman logs $ContainerName

    Write-Host "=== All tests passed! ===" -ForegroundColor Green

} catch {
    Write-Host "✗ Test failed: $_" -ForegroundColor Red
    
    # Show container logs for debugging
    Write-Host "Container logs for debugging:" -ForegroundColor Yellow
    podman logs $ContainerName
    
    throw $_
} finally {
    if (-not $SkipCleanup) {
        # Cleanup
        Write-Host "Cleaning up..." -ForegroundColor Yellow
        try {
            podman stop $ContainerName
            podman rm $ContainerName
            podman rmi $ImageName
            
            # Remove temporary test files
            Remove-Item -Path "nginx-test.conf" -Force -ErrorAction SilentlyContinue
            Remove-Item -Path "Containerfile.test" -Force -ErrorAction SilentlyContinue
        } catch {
            Write-Host "Warning: Cleanup failed: $_" -ForegroundColor Yellow
        }
    }
}

Write-Host "Test completed successfully!" -ForegroundColor Green