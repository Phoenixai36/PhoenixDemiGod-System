# Phoenix Hydra: Podman Migration & Operations Guide

This guide provides all necessary instructions to migrate the Phoenix Hydra stack from Docker to a rootless Podman environment, and to operate it using `systemd` and Quadlet files.

## 1. Technical Definitions

-   **Podman:** A daemon-less, OCI-compliant container engine that runs containers in rootless mode for enhanced security.
-   **Podman Compose:** A Python-based wrapper that interprets `compose.yaml` files and deploys containers using the Podman backend.
-   **Quadlet (.container / .pod):** A declarative format for defining containers and pods as native `systemd` services, simplifying lifecycle management.
-   **Rootless Containers:** Containers executed within a user's namespace without requiring root privileges, significantly reducing the potential attack surface.

## 2. Final Architecture with Podman

The architecture consists of multiple containerized services (cells) grouped into a single pod (`phoenix-hydra`). The entire stack is managed by `systemd` at the user level, ensuring services start on boot and restart on failure.

-   **Pod:** `phoenix-hydra.pod`
-   **Services:**
    -   `phoenix-core.container`
    -   `nca-toolkit.container`
    -   `n8n-phoenix.container`
    -   `windmill-phoenix.container`
    -   `revenue-db.container`
-   **Optional Observability Stack:**
    -   `grafana-loki.container` (managed via `observability.compose.yaml`)

## 3. Phase 1: Base Installation & Configuration (Weeks 1-2)

### Prerequisites
1.  **Install Podman:**
    ```bash
    # For Fedora/CentOS/RHEL
    sudo dnf install -y podman podman-docker podman-compose fuse-overlayfs slirp4netns
    ```
2.  **Enable Rootless Socket:**
    ```bash
    systemctl --user enable --now podman.socket
    ```
3.  **Create Quadlet Directory:**
    ```bash
    mkdir -p ~/.config/containers/systemd
    ```
4.  **Enable User Lingering (to keep services running after logout):**
    ```bash
    loginctl enable-linger $USER
    ```

### Validation
1.  **Check Rootless Status:**
    ```bash
    podman info --format '{{.Host.Security.Rootless}}'
    # Expected output: true
    ```
2.  **Test Podman Socket:**
    ```bash
    curl --unix-socket $XDG_RUNTIME_DIR/podman/podman.sock http://localhost/_ping
    # Expected output: OK
    ```

## 4. Phase 2: Deployment with Podman Compose (Weeks 3-4)

This method is ideal for local development and quick testing.

1.  **Navigate to the infrastructure directory:**
    ```bash
    cd infra/podman
    ```
2.  **Start all services:**
    ```bash
    podman-compose up -d
    ```
3.  **Verify service health:**
    ```bash
    podman ps --format '{{.Names}}\t{{.Status}}'
    ```
4.  **Access services:**
    -   **Core:** `http://localhost:8080`
    -   **n8n:** `http://localhost:5678`
    -   **Windmill:** `http://localhost:8000`

## 5. Phase 3: Orchestration with Quadlet & systemd (Months 2-3)

This is the recommended method for production environments.

1.  **Copy Quadlet Files:**
    Copy all `.container` and `.pod` files from `infra/podman/systemd/` to `~/.config/containers/systemd/`.
2.  **Reload systemd Daemon:**
    ```bash
    systemctl --user daemon-reload
    ```
3.  **Enable and Start the Main Target:**
    ```bash
    systemctl --user enable --now phoenix.target
    ```
    The services will now start automatically on boot.

## 6. DevOps Best Practices

### Docker Compatibility
To maintain compatibility with existing scripts, create a shell alias:
```bash
# Add to ~/.bashrc or ~/.zshrc
alias docker=podman
export DOCKER_HOST="unix:///run/user/$(id -u)/podman/podman.sock"
```

### Security
-   **SELinux:** Always use the `:Z` or `:z` label on volume mounts to allow the container to write to the host filesystem.
-   **Rootless Ports:** Rootless containers cannot bind to privileged ports (below 1024) by default. Use port forwarding or `nftables` if required.

### CI/CD with GitOps
-   Use GitHub Actions to build images with `podman build` and push them to a private registry.
-   Deploy updates by replacing the Quadlet files on the host and running `systemctl --user restart phoenix.target`.
