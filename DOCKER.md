# Docker Deployment Guide for Gateshead By Bike

This guide explains how to build and deploy the Gateshead By Bike application using Docker.

## Prerequisites

- Docker installed on your system ([Install Docker](https://docs.docker.com/get-docker/))
- Basic knowledge of Docker commands

## Building the Docker Image

To build the Docker image, run the following command from the project root directory:

```bash
docker build -t gateshead-by-bike .
```

This command will:
1. Use Python 3.11 slim as the base image
2. Install all required dependencies from `requirements.txt`
3. Copy the application code and database CSV files
4. Configure the application to listen on all network interfaces

## Running the Container

### Basic Usage

To run the application in a Docker container:

```bash
docker run -d -p 3000:3000 --name gateshead-by-bike gateshead-by-bike
```

The application will be accessible at `http://localhost:3000`

### With Custom Port

To run on a different port (e.g., 8080):

```bash
docker run -d -p 8080:3000 --name gateshead-by-bike gateshead-by-bike
```

The application will be accessible at `http://localhost:8080`

### With Volume for Persistent Data

To persist the SQLite database across container restarts, use a named Docker volume:

```bash
docker volume create gateshead-data
docker run -d -p 3000:3000 \
  -v gateshead-data:/app \
  --name gateshead-by-bike \
  gateshead-by-bike
```

This creates and mounts a named volume to preserve the `gbb-eli.db` database file and uploaded data.

**Note:** The entire `/app` directory is mounted to preserve the runtime-modified main.py and database state. The application modifies main.py at startup to configure network binding for Docker containers.

## Managing the Container

### View Logs

```bash
docker logs gateshead-by-bike
```

### View Real-time Logs

```bash
docker logs -f gateshead-by-bike
```

### Stop the Container

```bash
docker stop gateshead-by-bike
```

### Start the Container

```bash
docker start gateshead-by-bike
```

### Remove the Container

```bash
docker rm gateshead-by-bike
```

### Remove the Image

```bash
docker rmi gateshead-by-bike
```

## Docker Compose (Optional)

A `docker-compose.yml` file is provided for easier management. To use it:

```bash
# Build and start the application
docker compose up -d

# Stop the application
docker compose down

# View logs
docker compose logs -f

# Rebuild the image
docker compose build
```

**Note:** If you're using an older version of Docker, you may need to use `docker-compose` (with hyphen) instead of `docker compose` (space).

## Deployment to Web Servers

### Cloud Platforms

The Docker image can be deployed to various cloud platforms:

- **AWS ECS/Fargate**: Use the image with AWS Elastic Container Service
- **Google Cloud Run**: Deploy directly from the Docker image
- **Azure Container Instances**: Run the container on Azure
- **DigitalOcean App Platform**: Deploy using the Dockerfile
- **Heroku**: Use container registry for deployment

### Example: Deploying to Docker Hub

1. Tag the image:
   ```bash
   docker tag gateshead-by-bike your-dockerhub-username/gateshead-by-bike:latest
   ```

2. Push to Docker Hub:
   ```bash
   docker push your-dockerhub-username/gateshead-by-bike:latest
   ```

3. Deploy on your server:
   ```bash
   docker pull your-dockerhub-username/gateshead-by-bike:latest
   docker run -d -p 3000:3000 your-dockerhub-username/gateshead-by-bike:latest
   ```

## Environment Configuration

The application is configured with the following defaults:
- **Port**: 3000
- **Host**: 0.0.0.0 (all interfaces)
- **Debug Mode**: Enabled

## Troubleshooting

### Port Already in Use

If port 3000 is already in use, either:
1. Stop the service using that port
2. Use a different port mapping: `-p 8080:3000`

### Container Won't Start

Check the logs for errors:
```bash
docker logs gateshead-by-bike
```

### Database Issues

The SQLite database is created automatically on first run. If you encounter issues:
1. Stop the container
2. Remove the `gbb-eli.db` file
3. Restart the container to recreate the database

## Security Considerations

For production deployments:
1. Disable debug mode by modifying `main.py`
2. Use environment variables for sensitive configuration
3. Implement proper authentication and authorization
4. Use HTTPS/TLS encryption
5. Keep the Docker image and dependencies updated

## Technical Notes

### Network Binding Configuration

The application's main.py file is configured to bind to `localhost` by default. For Docker containers to accept external connections, the Dockerfile uses a runtime modification to change the host binding to `0.0.0.0`. This approach was chosen to:
- Avoid modifying the working source code
- Maintain compatibility with local development
- Enable Docker deployment without code changes

For production deployments, consider updating main.py to use environment variables for host configuration.

### Database Persistence

The SQLite database (`gbb-eli.db`) is created at runtime from CSV seed data. When using volumes for persistence:
- The entire `/app` directory is mounted to preserve both the database and runtime modifications
- Initial data is loaded from CSV files only on first run
- Subsequent runs use the persisted database

## Support

For issues or questions, please refer to the main README.md file or create an issue in the repository.
