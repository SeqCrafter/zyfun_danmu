# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a video danmu (弹幕/barrage) management system built with Python 3.13+ that integrates with ZYPlayer to fetch video data and provides danmu (bullet screen comments) functionality.

## Key Dependencies

- **Robyn**: Asynchronous web framework for the API server
- **Tortoise ORM**: Async ORM for SQLite database operations
- **httpx**: Async HTTP client for external API calls

## Development Commands

### Running the Application
```bash
python app.py  # Starts the Robyn server on port 8080
```

### Fetching Video Data from ZYPlayer
```bash
python fetch_data.py -s "视频源名称" -f "影片名称" [-j "播放源"]
```

### Installing Dependencies
```bash
pip install -r requirements.txt
```

## Architecture

### API Server (app.py)
- Main entry point running on port 8080 with CORS enabled
- Endpoints:
  - `GET /url?url=<video_url>`: Queries video info by URL and fetches danmu
  - `POST /upload`: Batch uploads video data with sources and episodes

### Database Layer
- **models.py**: Defines three Tortoise ORM models:
  - `Video`: Stores video titles
  - `VideoSource`: Links videos to their sources (1:N relationship)
  - `PlayLink`: Stores episode URLs with source and video references
- **db_operations.py**: Provides async database operations:
  - `query_by_url()`: Finds video info by play URL
  - `batch_insert_videos()`: Bulk inserts video data
  - `get_all_videos()`: Retrieves all videos with statistics

### External Integrations
- **fetch_data.py**: Integrates with ZYPlayer API (http://127.0.0.1:9978/api/v1)
  - Fetches video sources, searches films, and retrieves episode links
  - Automatically posts data to remote server
- **function.py**: Integrates with danmu API (http://localhost:7768/api/v1)
  - Fetches episode IDs and danmu comments
  - Parses barrage data into standard format

### Data Flow
1. Video data is fetched from ZYPlayer using `fetch_data.py`
2. Data is posted to the `/upload` endpoint
3. Video information is stored in SQLite database (`video_database.sqlite3`)
4. When querying by URL, the system fetches corresponding danmu data
5. Danmu is returned in a standardized format for video players

## Important Notes
- Database uses SQLite with file `video_database.sqlite3`
- All database operations are async using Tortoise ORM
- API responses are JSON with proper error handling
- Logging is configured for debugging (check console output)