# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LifeTrace is an intelligent life recording system based on screen screenshots. It automatically captures screen content, uses AI technology for intelligent understanding and data compression, and provides users with a convenient personal digital life archive query platform.

## Development Environment Setup

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
venv\Scripts\activate

# Activate virtual environment (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Core Commands

### Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

### System Management
```bash
# Initialize the system
lifetrace init

# Start all services
lifetrace start

# Check status
lifetrace status

# View statistics
lifetrace stats

# Stop all services  
lifetrace stop
```

### Individual Services
```bash
# Start individual services
lifetrace record    # Screenshot recording
lifetrace process   # File processing  
lifetrace serve     # Web server only

# Web interface
http://localhost:8840
```

### Development Workflow
```bash
# Test OCR functionality with reference implementation
python reference_source/pad_ocr.py

# Run services in debug mode
lifetrace record --debug
lifetrace process --debug  
lifetrace serve --debug
```

## Architecture Overview

This is currently an early-stage project with the following planned architecture:

### Core Modules (Planned Structure)
- **lifetrace/recorder/**: Screen capture module for automated screenshot taking
- **lifetrace/processor/**: Data processing pipeline for OCR, image analysis, and content understanding
- **lifetrace/storage/**: Data storage layer with SQLite/PostgreSQL backend
- **lifetrace/query/**: Query interface for searching and retrieving recorded data
- **lifetrace/ui/**: User interface components (Web/Desktop - to be determined)

### Technology Stack
- **Screen Capture**: Python PIL/OpenCV
- **OCR Recognition**: PaddleOCR (Chinese language support enabled)
- **Image Processing**: OpenCV, PIL
- **AI Understanding**: Natural language processing models
- **Data Storage**: SQLite/PostgreSQL
- **Backend**: Python Flask/FastAPI (planned)

## Current Implementation Status

LifeTrace is now fully implemented with the following components:

### Core Modules
- **lifetrace/recorder.py**: Screen recording module using MSS library
- **lifetrace/processor.py**: File monitoring and processing with watchdog
- **lifetrace/ocr.py**: OCR processing using PaddleOCR with Chinese support
- **lifetrace/storage.py**: SQLite database management with SQLAlchemy
- **lifetrace/server.py**: FastAPI web server with REST API
- **lifetrace/config.py**: Configuration management system
- **lifetrace/commands.py**: Command-line interface using Typer

### Three-Process Architecture
Following Pensieve's proven architecture:
1. `lifetrace record` - Screenshot capture (1-second intervals)
2. `lifetrace process` - File monitoring and database insertion
3. `lifetrace serve` - Web interface and API server

### Web Interface
- HTML/CSS/JavaScript frontend in `lifetrace/templates/index.html`
- Real-time screenshot search and viewing
- Statistics dashboard
- OCR result display

## Key Development Notes

### OCR Processing
- The reference OCR implementation uses PaddleOCR with Chinese language support
- Processes screenshots from a monitored directory every 0.5 seconds
- Generates corresponding .txt files with extracted text
- Includes timing information for performance monitoring

### File Structure
- Core application code should go in the `lifetrace/` directory following the modular structure
- Reference implementations and experiments go in `reference_source/`
- Screenshot data and OCR results stored in `screenshot/` directory
- Configuration files planned for `config/` directory

### Privacy Considerations
- The system is designed to include privacy content filtering
- Configurable privacy rules need to be implemented
- Consider sensitive information handling in screenshot processing
