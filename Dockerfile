# syntax=docker/dockerfile:1

# ===================== Stage 1: Build Astro UI =====================
FROM node:22-slim AS ui-builder

WORKDIR /app

# Enable pnpm via corepack
RUN corepack enable && corepack prepare pnpm@11.3.0 --activate

# Copy workspace files for dependency install caching
COPY package.json pnpm-workspace.yaml pnpm-lock.yaml ./
COPY ui/package.json ./ui/
RUN pnpm install --frozen-lockfile

# Copy UI source and build
COPY ui/ ./ui/
RUN pnpm --filter ui build

# ===================== Stage 2: Python API =====================
FROM python:3.12-slim

WORKDIR /app

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY src/ ./src/
COPY api/ ./api/
COPY entrypoint.sh .
COPY data/ ./data/

# Copy built static UI from the Node stage
COPY --from=ui-builder /app/ui/dist ./ui/dist

RUN chmod +x entrypoint.sh

EXPOSE 8501

CMD ["./entrypoint.sh"]
