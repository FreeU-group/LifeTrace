![LifeTrace Logo](.github/assets/rhn8yu8l.png)

![GitHub stars](https://img.shields.io/github/stars/tangyuanbo1/LifeTrace_app?style=social) ![GitHub forks](https://img.shields.io/github/forks/tangyuanbo1/LifeTrace_app?style=social) ![GitHub issues](https://img.shields.io/github/issues/tangyuanbo1/LifeTrace_app) ![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg) ![Python version](https://img.shields.io/badge/python-3.13+-blue.svg) ![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)

**Language**: [English](README.md) | [中文](README_CN.md)

[📖 Documentation](https://freeyou.club/lifetrace/introduction.html) • [🚀 Quick Start](#deployment-and-configuration) • [💡 Features](#core-features) • [🔧 Development](#development-guide) • [🤝 Contributing](#contributing)

# LifeTrace - Intelligent Life Recording System

## Project Overview

LifeTrace is an AI-based intelligent life recording system that can automatically manage your personal task context. Through technologies such as automatic screenshots, OCR text recognition, vector retrieval, and multimodal search, LifeTrace helps you record, organize, and retrieve daily activity traces.

## Core Features

- **Automatic Screenshot Recording**: Timed automatic screen capture to record user activities
- **Intelligent OCR Recognition**: Uses RapidOCR to extract text content from screenshots
- **Smart Event Management**: Automatically aggregate screenshots into intelligent events based on context
- **Information Retrieval**: Help users trace back and retrieve important information fragments from the past
<!-- - **Multimodal Search**: Supports text, image, and semantic search -->
<!-- - **Vector Database**: Efficient vector storage and retrieval based on ChromaDB -->
- **Web API Service**: Provides complete RESTful API interfaces
- **Frontend Integration**: Supports integration with various frontend frameworks

## Get started

### Environment Requirements
- Python 3.13+
- Supported OS: Windows, macOS
- Optional: CUDA support (for GPU acceleration)

### Install Dependencies

This project uses [uv](https://github.com/astral-sh/uv) for fast and reliable dependency management.

**Install uv:**
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or with pip
pip install uv
```

**Install dependencies and sync environment:**
```bash
# Sync dependencies from pyproject.toml and uv.lock
uv sync

# Activate the virtual environment
# macOS/Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

### Start the Backend Service

**Before starting the server, you need to configure the settings:**

```bash
# Copy the default configuration file
cp lifetrace/config/default_config.yaml lifetrace/config/config.yaml

# Edit config.yaml to customize your settings (optional)
```

**Start the server:**

```bash
python -m lifetrace.server
```

The backend service will start at `http://localhost:8000`.

### Start the Frontend Service

The frontend is required to use LifeTrace. Start the frontend development server:

```bash
cd frontend
pnpm install
pnpm run dev
```

The frontend development server will start at `http://localhost:3000`, with API requests automatically proxied to backend `:8000`.

Once both services are running, open your browser and navigate to `http://localhost:3000` to enjoy LifeTrace! 🎉

For more details, see: [frontend/README.md](frontend/README.md)

<!--
#### Start Web Service Only
```bash
python -m lifetrace_backend.server --port 8000
```

#### Start Individual Services
```bash
# Start recorder
python -m lifetrace_backend.recorder

# Start processor
python -m lifetrace_backend.processor

# Start OCR service
python -m lifetrace_backend.simple_ocr
``` -->

## 📋 TODO & Roadmap

### 🚀 High Priority

- ☐ **User Experience Improvements**
  - ☐ Implement keyboard shortcuts for power users
  - ☐ Create interactive onboarding tutorial

### 💡 Future Ideas

- ☐ **Mobile & Cross-Platform**
  - ☐ Develop mobile companion app
  - ☐ Add tablet-optimized interface
  - ☐ Create web-based version

### ✅ Recently Completed
- ☑ **Core Infrastructure** - Basic screenshot recording and OCR functionality

---

> 💡 **Want to contribute?** Check out our [Contributing Guidelines](#contributing) and pick up any TODO item that interests you!

## Development Guide

### Project Structure

```
├── .github/                    # GitHub repository assets
│   ├── assets/                 # Static assets (images for README)
│   └── ...                     # Other GitHub repository files
├── lifetrace/                  # Core backend modules
│   ├── server.py               # Web API service
│   ├── config/                 # Configuration files
│   │   ├── config.yaml         # Main configuration
│   │   ├── default_config.yaml # Default configuration
│   │   └── rapidocr_config.yaml# OCR configuration
│   ├── routers/                # API route handlers
│   │   ├── screenshot.py       # Screenshot endpoints
│   │   ├── event.py            # Event management endpoints
│   │   ├── chat.py             # Chat interface endpoints
│   │   ├── search.py           # Search endpoints
│   │   ├── ocr.py              # OCR service endpoints
│   │   ├── rag.py              # RAG service endpoints
│   │   ├── plan.py             # Plan management endpoints
│   │   ├── behavior.py         # User behavior endpoints
│   │   ├── config.py           # Configuration endpoints
│   │   ├── health.py           # Health check endpoints
│   │   ├── logs.py             # Log management endpoints
│   │   ├── system.py           # System endpoints
│   │   └── vector.py           # Vector service endpoints
│   ├── schemas/                # Pydantic data models
│   │   ├── screenshot.py       # Screenshot models
│   │   ├── event.py            # Event models
│   │   ├── chat.py             # Chat models
│   │   ├── search.py           # Search models
│   │   ├── plan.py             # Plan models
│   │   ├── config.py           # Config models
│   │   ├── stats.py            # Statistics models
│   │   ├── system.py           # System models
│   │   └── vector.py           # Vector models
│   ├── storage/                # Data storage layer
│   │   ├── database.py         # Database operations
│   │   └── models.py           # SQLAlchemy models
│   ├── llm/                    # LLM and AI services
│   │   ├── llm_client.py       # LLM client wrapper
│   │   ├── event_summary_service.py # Event summarization
│   │   ├── rag_service.py      # RAG service
│   │   ├── retrieval_service.py# Retrieval service
│   │   ├── context_builder.py  # Context building
│   │   ├── vector_service.py   # Vector operations
│   │   ├── vector_db.py        # Vector database
│   │   ├── multimodal_vector_service.py # Multimodal vectors
│   │   └── multimodal_embedding.py # Multimodal embeddings
│   ├── tool/                   # Core tools
│   │   ├── recorder.py         # Screen recording tool
│   │   └── ocr.py              # OCR processing tool
│   ├── util/                   # Utility functions
│   │   ├── config.py           # Configuration utilities
│   │   ├── logging_config.py   # Logging configuration
│   │   ├── utils.py            # General utilities
│   │   ├── app_utils.py        # Application utilities
│   │   ├── query_parser.py     # Query parsing
│   │   └── token_usage_logger.py # Token usage tracking
│   └── models/                 # OCR model files
│       ├── ch_PP-OCRv4_det_infer.onnx
│       ├── ch_PP-OCRv4_rec_infer.onnx
│       └── ch_ppocr_mobile_v2.0_cls_infer.onnx
├── frontend/                   # Frontend application (Next.js)
│   ├── app/                    # Next.js app directory
│   │   ├── page.tsx            # Home page
│   │   ├── layout.tsx          # Root layout
│   │   ├── events/             # Events management page
│   │   ├── chat/               # Chat interface page
│   │   ├── analytics/          # Analytics page
│   │   ├── app-usage/          # App usage page
│   │   ├── plan/               # Plan management page
│   │   └── settings/           # Settings page
│   ├── components/             # React components
│   │   ├── common/             # Common components
│   │   ├── layout/             # Layout components
│   │   ├── screenshot/         # Screenshot components
│   │   ├── search/             # Search components
│   │   └── ui/                 # UI components
│   ├── lib/                    # Utilities and services
│   │   ├── api.ts              # API client
│   │   ├── types.ts            # TypeScript types
│   │   ├── utils.ts            # Utility functions
│   │   ├── context/            # React contexts
│   │   └── store/              # State management
│   ├── public/                 # Static assets
│   ├── package.json            # Frontend dependencies
│   ├── pnpm-lock.yaml          # pnpm lock file
│   ├── next.config.ts          # Next.js configuration
│   └── tsconfig.json           # TypeScript configuration
├── doc/                        # Documentation
│   ├── setup_guide.md          # Setup guide
│   ├── api_configuration_guide.md # API configuration
│   ├── uv_usage_guide.md       # uv package manager guide
│   ├── event_mechanism.md      # Event mechanism docs
│   ├── memory_optimization_guide.md # Memory optimization
│   └── ...                     # Other documentation files
├── deploy/                     # Deployment scripts
│   ├── build_server.bat        # Server build script
│   ├── build_ocr.bat           # OCR build script
│   └── build_recorder.bat      # Recorder build script
├── pyproject.toml              # Python project configuration
├── uv.lock                     # uv lock file
├── LICENSE                     # Apache 2.0 License
├── README.md                   # This file (English)
└── README_CN.md                # Chinese README
```

## Contributing

The LifeTrace community is possible thanks to thousands of kind volunteers like you. We welcome all contributions to the community and are excited to welcome you aboard.

> Please follow these steps to contribute.

**Recent Contributions:**

![GitHub contributors](https://img.shields.io/github/contributors/tangyuanbo1/LifeTrace_app) ![GitHub commit activity](https://img.shields.io/github/commit-activity/m/tangyuanbo1/LifeTrace_app) ![GitHub last commit](https://img.shields.io/github/last-commit/tangyuanbo1/LifeTrace_app)

**How to contribute:**

1. **🍴 Fork the project** - Create your own copy of the repository
2. **🌿 Create a feature branch** - `git checkout -b feature/amazing-feature`
3. **💾 Commit your changes** - `git commit -m 'Add some amazing feature'`
4. **📤 Push to the branch** - `git push origin feature/amazing-feature`
5. **🔄 Create a Pull Request** - Submit your changes for review

**Areas where you can contribute:**

- 🐛 **Bug Reports** - Help us identify and fix issues
- 💡 **Feature Requests** - Suggest new functionality
- 📝 **Documentation** - Improve guides and tutorials
- 🧪 **Testing** - Write tests and improve coverage
- 🎨 **UI/UX** - Enhance the user interface
- 🔧 **Code** - Implement new features and improvements

**Getting Started:**

- Check out our [Contributing Guidelines](CONTRIBUTING.md)
- Look for issues labeled `good first issue` or `help wanted`
- Join our community discussions in Issues and Pull Requests

We appreciate all contributions, no matter how small! 🙏

## Join Our Community

Connect with us and other LifeTrace users! Scan the QR codes below to join our community groups:

<table>
  <tr>
    <th>WeChat Group</th>
    <th>Feishu Group</th>
    <th>Xiaohongshu</th>
  </tr>
  <tr>
    <td align="center">
      <img src=".github/assets/wechat.jpg" alt="WeChat QR Code" width="200"/>
      <br/>
      <em>Scan to join WeChat group</em>
    </td>
    <td align="center">
      <img src=".github/assets/feishu.png" alt="Feishu QR Code" width="200"/>
      <br/>
      <em>Scan to join Feishu group</em>
    </td>
    <td align="center">
      <img src=".github/assets/xhs.jpg" alt="Xiaohongshu QR Code" width="200"/>
      <br/>
      <em>Follow us on Xiaohongshu</em>
    </td>
  </tr>
</table>

## Document

We use deepwiki to manage our docs, please ref to this [**website.**](https://deepwiki.com/tangyuanbo1/LifeTrace_app/6.2-deployment-and-setup)

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=tangyuanbo1/LifeTrace_app&type=Timeline)](https://www.star-history.com/#tangyuanbo1/LifeTrace_app&Timeline)

## License

Copyright © 2025 LifeTrace.org

The content of this repository is bound by the following licenses:

• The computer software is licensed under the [Apache License 2.0](LICENSE).
• The learning resources in the `/doc` directory including their subdirectories thereon are copyright © 2025 LifeTrace.org

### Apache License 2.0

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
