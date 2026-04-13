# Build stage
FROM node:20-alpine as build-stage

WORKDIR /app

# Copy package files and install dependencies
COPY package*.json ./
RUN npm install

# Copy source files
COPY . .

# Set placeholders as environment variables so Vite bakes them into the build
# These placeholders will be replaced at runtime by entrypoint.sh using values from the mounted .env file.
ENV VITE_API_URL=BUILD_TIME_PLACEHOLDER_VITE_API_URL
ENV VITE_CUBEJS_API_URL=BUILD_TIME_PLACEHOLDER_VITE_CUBEJS_API_URL
ENV VITE_CUBEJS_TOKEN=BUILD_TIME_PLACEHOLDER_VITE_CUBEJS_TOKEN
ENV VITE_KEYCLOAK_URL=BUILD_TIME_PLACEHOLDER_VITE_KEYCLOAK_URL
ENV VITE_KEYCLOAK_REALM=BUILD_TIME_PLACEHOLDER_VITE_KEYCLOAK_REALM
ENV VITE_KEYCLOAK_CLIENT_ID=BUILD_TIME_PLACEHOLDER_VITE_KEYCLOAK_CLIENT_ID

# Build the application
RUN npm run build

# Production stage
FROM nginx:stable-alpine as production-stage

# Copy the build output to Nginx's default public directory
COPY --from=build-stage /app/dist /usr/share/nginx/html

# Copy the custom Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy the entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose port 80
EXPOSE 80

# Use the entrypoint script to inject runtime environment variables
ENTRYPOINT ["/entrypoint.sh"]
