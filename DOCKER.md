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

To persist the SQLite database across container restarts:

```bash
docker run -d -p 3000:3000 \
  -v $(pwd)/data:/app \
  --name gateshead-by-bike \
  gateshead-by-bike
```

This mounts a local `data` directory to preserve the `gbb-eli.db` database file.

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

Create a `docker-compose.yml` file for easier management:

```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "3000:3000"
    volumes:
      - ./data:/app
    restart: unless-stopped
    container_name: gateshead-by-bike
```

Then run:

```bash
# Start the application
docker-compose up -d

# Stop the application
docker-compose down

# View logs
docker-compose logs -f
```

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

## Support

For issues or questions, please refer to the main README.md file or create an issue in the repository.
