# Stage 1: Build stage
FROM oven/bun:slim as builder

WORKDIR /app

# Install dependencies
COPY package.json bun.lock ./
RUN bun install --frozen-lockfile

# Copy project files and build
COPY . .
RUN bun x svelte-kit sync
RUN bun run build

# Stage: Development stage
FROM oven/bun:slim as dev
WORKDIR /app
COPY package.json bun.lock ./
RUN bun install
COPY . .
# We run sync to ensure types are generated
RUN bun x svelte-kit sync
EXPOSE 5173
CMD ["bun", "run", "dev", "--host", "0.0.0.0"]

# Stage 2: Production stage
FROM oven/bun:slim as runner

WORKDIR /app

# Set production environment
ENV NODE_ENV=production
ENV PORT=5173

# Copy built files and necessary dependency files
COPY --from=builder /app/build ./build
COPY --from=builder /app/package.json /app/bun.lock ./

# Install only production dependencies
RUN bun install --frozen-lockfile --production

# Use a non-root user for security
USER bun

# Expose the port the app runs on
EXPOSE 5173

# Start the application
CMD ["bun", "./build/index.js"]
