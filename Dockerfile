# Stage 1: Build Next.js frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app
COPY scripts ./scripts
COPY version.json ./version.json
COPY shared ./shared
RUN cd shared && npm install && npm run build

COPY server ./server
WORKDIR /app/server
RUN npm install
RUN npm run build:next

# Stage 2: Production Runner with Ubuntu 24.04 (glibc, same as Crafty 4)
FROM ubuntu:24.04 AS runner

ENV DEBIAN_FRONTEND="noninteractive"
ENV NODE_ENV=production
ENV PORT=22313
ENV TZ=UTC
ENV DATA_DIR=/data

# Install Python 3, OpenJDK 17, 21, 25, and system utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    openjdk-17-jre-headless \
    openjdk-21-jre-headless \
    openjdk-25-jre-headless \
    curl \
    psmisc \
    tzdata \
    libcurl4 \
    udev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Java Environment Variables for Warden
ENV JAVA_17_PATH=/usr/lib/jvm/java-17-openjdk-amd64/bin/java
ENV JAVA_21_PATH=/usr/lib/jvm/java-21-openjdk-amd64/bin/java
ENV JAVA_25_PATH=/usr/lib/jvm/java-25-openjdk-amd64/bin/java
ENV JAVA_PATH=/usr/lib/jvm/java-25-openjdk-amd64/bin/java

WORKDIR /app
COPY server_py/requirements.txt ./requirements.txt
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

COPY server_py/app ./app
COPY --from=frontend-builder /app/server/out ./static

# Ensure persistent data directory exists
RUN mkdir -p /data

EXPOSE 22313

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD curl -f http://localhost:${PORT}/api/health || exit 1

CMD ["python3", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "22313"]
