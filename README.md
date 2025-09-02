# Video Danmu Management API

A video danmu (弹幕) management system built with Robyn and PostgreSQL.

## Features

- Store and manage video metadata with multiple sources
- Query video information by URL
- Batch upload video data
- Delete video sources
- Fetch danmu (bullet screen comments) for videos

## Prerequisites

- Docker and Docker Compose
- Python 3.13+ (for local development)
- PostgreSQL (or use Docker)

## Quick Start with Docker

### 1. Build and Run with Docker Compose

```bash
# Build and start the services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Stop and remove volumes (clean database)
docker-compose down -v
```

### 2. Build Docker Image Only

```bash
# Build the image
docker build -t video-danmu-api .

# Run with external PostgreSQL
docker run -d \
  -p 8080:8080 \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_HOST=your-postgres-host \
  -e POSTGRES_PORT=5432 \
  -e POSTGRES_DB=video_database \
  video-danmu-api
```

## Environment Variables

Configure the following environment variables for PostgreSQL connection:

- `POSTGRES_USER`: PostgreSQL username (default: `postgres`)
- `POSTGRES_PASSWORD`: PostgreSQL password (default: `password`)
- `POSTGRES_HOST`: PostgreSQL host (default: `localhost`)
- `POSTGRES_PORT`: PostgreSQL port (default: `5432`)
- `POSTGRES_DB`: Database name (default: `video_database`)

## API Endpoints

### GET /url
Query video information and fetch danmu by URL.

```bash
curl "http://localhost:8080/url?url=https://example.com/video.mp4"
```

### POST /upload
Batch upload video data with sources and episodes.

```bash
curl -X POST http://localhost:8080/upload \
  -H "Content-Type: application/json" \
  -d '{
    "title": "视频标题",
    "list": {
      "源1": {
        "1": "https://example.com/ep1.mp4",
        "2": "https://example.com/ep2.mp4"
      }
    }
  }'
```

### DELETE /video
Delete all URLs for a specific video source.

```bash
curl -X DELETE "http://localhost:8080/video?title=视频标题&source=源1"
```

## Local Development

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables

```bash
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=password
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DB=video_database
```

### 3. Run the Application

```bash
python app.py
```

## Database Schema

The application uses three models:

- **Video**: Stores video titles
- **VideoSource**: Links videos to their sources (1:N relationship)
- **PlayLink**: Stores episode URLs with source and video references

## Fetching Data from ZYPlayer

Use the `fetch_data.py` script to fetch video data from ZYPlayer:

```bash
python fetch_data.py -s "视频源名称" -f "影片名称" [-j "播放源"]
```

## Health Check

The Docker container includes a health check that verifies the API is responding:

```bash
curl http://localhost:8080/url?url=test
```

## Troubleshooting

### Database Connection Issues

1. Ensure PostgreSQL is running and accessible
2. Check environment variables are correctly set
3. Verify network connectivity between containers (if using Docker)

### Port Already in Use

Change the port mapping in `docker-compose.yml` or when running Docker:

```yaml
ports:
  - "8081:8080"  # Map to different host port
```

## License

This project is for educational purposes.