# Use dev container base image
FROM mcr.microsoft.com/devcontainers/python:1-3.12-bookworm

# ✅ Trust Zscaler cert early (use .crt extension for update-ca-certificates)
COPY ZscalerRootCertificate-2048-SHA256.pem /usr/local/share/ca-certificates/zscaler.crt
RUN apt-get update && apt-get install -y ca-certificates && update-ca-certificates

# ✅ Make pip, curl, and Node respect custom certs
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
ENV NODE_EXTRA_CA_CERTS=/etc/ssl/certs/ca-certificates.crt
ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt
ENV PIP_CERT=/etc/ssl/certs/ca-certificates.crt

# ✅ Install AWS CLI (auto-detect architecture)
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl unzip && \
    ARCH=$(uname -m) && \
    if [ "$ARCH" = "x86_64" ]; then \
    CLI_URL="https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip"; \
    else \
    CLI_URL="https://awscli.amazonaws.com/awscli-exe-linux-aarch64.zip"; \
    fi && \
    curl "$CLI_URL" -o "awscliv2.zip" && \
    unzip -o awscliv2.zip && \
    ./aws/install && \
    rm -rf awscliv2.zip aws && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# ✅ Install git and configure safe directory
RUN apt-get update && apt-get install -y git && \
    git config --global --add safe.directory /workspaces/oxford-genai-capstone

# ✅ Install Python dependencies (using trusted cert explicitly)
COPY requirements.txt requirements.txt
RUN pip3 install --cert /etc/ssl/certs/ca-certificates.crt -r requirements.txt

# ✅ Final cleanup
RUN rm -rf /var/lib/apt/lists/*