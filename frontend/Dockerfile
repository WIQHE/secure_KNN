FROM node:18-alpine

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install

# Copy source
COPY . .

# Expose Vite default port
EXPOSE 5173

# Start dev server with --host to bind to all interfaces
CMD ["npm", "run", "dev", "--", "--host"]
