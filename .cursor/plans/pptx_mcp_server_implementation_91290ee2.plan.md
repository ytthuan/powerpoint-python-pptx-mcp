---
name: PPTX MCP Server Implementation
overview: Build a comprehensive Model Context Protocol (MCP) server in Python that enables AI agents to naturally interact with PPTX files, supporting reading slide content (text and images), editing slides, managing notes, and comprehensive slide operations including formatting, tables, charts, animations, and transitions.
todos:
  - id: setup_mcp_structure
    content: Create MCP server directory structure and initialize with official MCP Python SDK
    status: pending
  - id: implement_core_handler
    content: Implement core PPTX handler with read operations (text, images, shapes, tables, charts)
    status: pending
    dependencies:
      - setup_mcp_structure
  - id: implement_read_tools
    content: Create read tools (read_slide_content, read_slide_text, read_slide_images, read_presentation_info)
    status: pending
    dependencies:
      - implement_core_handler
  - id: implement_edit_tools
    content: Create edit tools (update_slide_text, replace_slide_image, add_text_box, add_image, update_formatting)
    status: pending
    dependencies:
      - implement_core_handler
  - id: implement_slide_management
    content: Create slide management tools (add_slide, delete_slide, reorder_slides, duplicate_slide, change_layout)
    status: pending
    dependencies:
      - implement_core_handler
  - id: implement_image_extraction
    content: Build image extraction module to extract and process images from PPTX files
    status: pending
    dependencies:
      - implement_core_handler
  - id: implement_safe_editor
    content: Create safe XML-based editor to preserve animations and transitions during edits
    status: pending
    dependencies:
      - implement_core_handler
  - id: integrate_notes_tools
    content: Integrate existing notes functionality as MCP tools (read_notes, update_notes, format_notes_structure) - NO Azure integration, AI agent handles content generation
    status: pending
    dependencies:
      - setup_mcp_structure
  - id: implement_resources
    content: Implement PPTX file resources for listing and accessing presentations
    status: pending
    dependencies:
      - setup_mcp_structure
  - id: add_error_handling
    content: Add comprehensive error handling, validation, and logging throughout
    status: pending
    dependencies:
      - implement_read_tools
      - implement_edit_tools
      - implement_slide_management
  - id: update_dependencies
    content: Update requirements.txt with MCP SDK and Pillow dependencies
    status: pending
  - id: create_documentation
    content: Document all tools, resources, and usage examples for AI agents
    status: pending
    dependencies:
      - implement_read_tools
      - implement_edit_tools
      - implement_slide_management
  - id: containerize_mcp_server
    content: Create Dockerfile, docker-compose.yml, and .dockerignore for containerizing MCP server
    status: pending
    dependencies:
      - setup_mcp_structure
      - implement_core_handler
---

# PPTX MCP Server Implementation Plan

## Overview

Build a Model Context Protocol (MCP) server that exposes PPTX manipulation capabilities as tools and resources, allowing AI agents to interact with PowerPoint files through natural language commands.

## Architecture

```mermaid
graph TB
    A[AI Agent with LLM] -->|JSON-RPC over stdio| B[MCP Server]
    B -->|Tools| C[PPTX Handler Module]
    B -->|Resources| D[PPTX File Resources]
    C -->|python-pptx| E[PPTX Files]
    C -->|lxml/zipfile| F[Safe XML Editing]
    C -->|PIL/Pillow| G[Image Processing]
    
    subgraph "AI Agent Responsibilities"
        A
        A1[Content Generation]
        A2[Translation]
        A3[Summarization]
        A --> A1
        A --> A2
        A --> A3
    end
    
    subgraph "MCP Server Components"
        B
        H[Tool Registry]
        I[Resource Provider]
    end
    
    subgraph "PPTX Operations"
        C
        J[Read Operations]
        K[Write Operations]
        L[Slide Management]
        M[Content Editing]
    end
    
    style A fill:#e1f5ff
    style B fill:#fff4e1
    style C fill:#e8f5e9
```



### Content Generation Workflow

```mermaid
sequenceDiagram
    participant AI as AI Agent (LLM)
    participant MCP as MCP Server
    participant PPTX as PPTX File
    
    AI->>MCP: read_notes(pptx_path, slide_number)
    MCP->>PPTX: Read notes content
    PPTX-->>MCP: Return notes text
    MCP-->>AI: Notes content
    
    Note over AI: Generate content using LLM:<br/>- Detect language<br/>- Translate if needed<br/>- Create short version<br/>- Create full version
    
    AI->>MCP: format_notes_structure(short, original)
    MCP-->>AI: Formatted structure
    
    AI->>MCP: update_notes(pptx_path, slide_number, formatted_text)
    MCP->>PPTX: Update notes (safe zip-based edit)
    PPTX-->>MCP: Success
    MCP-->>AI: Notes updated
```



## Technology Stack

- **MCP Framework**: Official `mcp` Python SDK (Anthropic's Model Context Protocol)
- **PPTX Library**: `python-pptx` for high-level operations
- **XML Processing**: `lxml` for safe, targeted edits (preserve animations/transitions)
- **Image Processing**: `Pillow` (PIL) for image extraction and manipulation
- **File Handling**: `zipfile` for direct PPTX zip manipulation when needed

## Project Structure

```javascript
.
├── mcp_server/
│   ├── __init__.py
│   ├── server.py              # Main MCP server entry point
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── read_tools.py      # Tools for reading slide content
│   │   ├── edit_tools.py      # Tools for editing slides
│   │   ├── slide_tools.py     # Tools for slide management
│   │   └── notes_tools.py     # Tools for speaker notes (existing)
│   ├── resources/
│   │   ├── __init__.py
│   │   └── pptx_resources.py  # PPTX file resources
│   ├── core/
│   │   ├── __init__.py
│   │   ├── pptx_handler.py    # Core PPTX operations
│   │   ├── image_extractor.py # Image extraction utilities
│   │   └── safe_editor.py     # Safe XML-based editing
│   └── utils/
│       ├── __init__.py
│       └── validators.py       # Input validation
├── scripts/
│   └── (existing scripts remain)
├── docker/
│   ├── Dockerfile              # Multi-stage Docker build
│   ├── docker-compose.yml     # Docker Compose configuration
│   └── .dockerignore          # Docker ignore patterns
├── requirements.txt           # Updated with mcp, Pillow
├── mcp_config.json            # MCP server configuration
└── README.md                  # Updated documentation
```



## Implementation Details

### 1. MCP Server Setup (`mcp_server/server.py`)

- Initialize MCP server using official SDK
- Register tools and resources
- Handle stdio communication (JSON-RPC)
- Error handling and logging

### 2. Core PPTX Handler (`mcp_server/core/pptx_handler.py`)

**Read Operations:**

- Extract all text from slides (shapes, text boxes, placeholders)
- Extract images with metadata (position, size, format)
- Read slide properties (layout, background, transitions)
- Read notes (existing functionality)
- Extract tables and their content
- Extract charts and their data

**Write Operations:**

- Update text in specific shapes/text boxes
- Replace images
- Add new shapes/text boxes/images
- Modify formatting (fonts, colors, alignment)
- Update tables
- Modify slide properties

**Slide Management:**

- Add new slides
- Delete slides
- Reorder slides
- Duplicate slides
- Change slide layouts

### 3. Tools Implementation

#### Read Tools (`mcp_server/tools/read_tools.py`)

1. **`read_slide_content`**

- Parameters: `pptx_path`, `slide_number` (optional, all if not specified)
- Returns: JSON with text, images (base64 or paths), shapes info

2. **`read_slide_text`**

- Parameters: `pptx_path`, `slide_number`
- Returns: All text content from slide

3. **`read_slide_images`**

- Parameters: `pptx_path`, `slide_number`
- Returns: Image metadata and optionally extracted images

4. **`read_presentation_info`**

- Parameters: `pptx_path`
- Returns: Slide count, layouts, metadata

#### Edit Tools (`mcp_server/tools/edit_tools.py`)

1. **`update_slide_text`**

- Parameters: `pptx_path`, `slide_number`, `shape_id` (or search criteria), `new_text`
- Updates text in specific shape

2. **`replace_slide_image`**

- Parameters: `pptx_path`, `slide_number`, `image_id`, `new_image_path`
- Replaces existing image

3. **`add_text_box`**

- Parameters: `pptx_path`, `slide_number`, `text`, `position`, `size`, `formatting`
- Adds new text box to slide

4. **`add_image`**

- Parameters: `pptx_path`, `slide_number`, `image_path`, `position`, `size`
- Adds new image to slide

5. **`update_formatting`**

- Parameters: `pptx_path`, `slide_number`, `shape_id`, `formatting_options`
- Updates font, color, alignment, etc.

#### Slide Management Tools (`mcp_server/tools/slide_tools.py`)

1. **`add_slide`**

- Parameters: `pptx_path`, `layout_name`, `position` (optional)
- Adds new slide

2. **`delete_slide`**

- Parameters: `pptx_path`, `slide_number`
- Removes slide

3. **`reorder_slides`**

- Parameters: `pptx_path`, `slide_order` (list of slide numbers in new order)
- Reorders slides

4. **`duplicate_slide`**

- Parameters: `pptx_path`, `slide_number`, `position` (optional)
- Duplicates slide

5. **`change_slide_layout`**

- Parameters: `pptx_path`, `slide_number`, `layout_name`
- Changes slide layout

#### Notes Tools (`mcp_server/tools/notes_tools.py`)

**Architecture Decision**: MCP server focuses on PPTX manipulation only. Content generation (translation, summarization) is handled by the calling AI agent using its LLM capabilities.**Tools:**

1. **`read_notes`**

                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - Parameters: `pptx_path`, `slide_number` (optional, all if not specified)
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - Returns: Notes content for specified slide(s)
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - Leverages existing `dump_notes` functionality

2. **`update_notes`**

                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - Parameters: `pptx_path`, `slide_number`, `notes_text`, `in_place` (optional, default: false)
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - Updates notes with provided content (AI agent generates this content)
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - Uses safe zip-based editing by default
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - Leverages existing `apply_notes_zip` functionality

3. **`format_notes_structure`**

                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - Parameters: `notes_text`, `format_type` ("short_original" or "simple")
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - Formats notes into structured format (short/original template)
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - Does NOT generate content - only formats structure
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - AI agent should generate both short and original versions before calling this

**Workflow Example:**

```javascript
1. AI Agent calls: read_notes(pptx_path, slide_number=1)
2. AI Agent uses its LLM to:
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        - Detect language
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        - Translate if needed
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        - Generate short version (30-50% length)
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        - Generate full version
3. AI Agent calls: format_notes_structure(short_text, original_text, format_type="short_original")
4. AI Agent calls: update_notes(pptx_path, slide_number=1, notes_text=formatted_text)
```

**Note**: Existing Azure integration in `scripts/update_notes_format.py` remains available for CLI/batch processing. MCP server does not include Azure dependencies to maintain clean separation of concerns.

### 4. Resources (`mcp_server/resources/pptx_resources.py`)

- Expose PPTX files as resources
- Allow listing available PPTX files
- Provide metadata about presentations

### 5. Image Extraction (`mcp_server/core/image_extractor.py`)

- Extract images from PPTX zip structure
- Convert to common formats (PNG, JPEG)
- Handle embedded vs linked images
- Preserve image metadata

### 6. Safe Editor (`mcp_server/core/safe_editor.py`)

- XML-based editing for targeted changes
- Preserve animations, transitions, and complex formatting
- Similar to existing zip-based editing approach
- Support for both python-pptx and direct XML editing

## Key Features

1. **Natural Language Interface**: Tools designed to be called by AI agents with clear, descriptive names
2. **Safe Editing**: Default to zip/XML-based editing to preserve animations and transitions
3. **Comprehensive Operations**: Support all major PPTX operations
4. **Error Handling**: Robust validation and error messages
5. **Backup Support**: Optional automatic backups before modifications
6. **Batch Operations**: Support for processing multiple slides
7. **Separation of Concerns**: MCP server handles PPTX operations only; AI agent handles content generation using its LLM capabilities

## Dependencies

Add to `requirements.txt`:

- `mcp>=0.1.0` (official MCP Python SDK)
- `Pillow>=10.0.0` (image processing)
- Keep existing: `python-pptx`, `lxml`
- **Note**: Azure dependencies (`azure-identity`, `azure-ai-projects`) remain in requirements.txt for existing CLI scripts but are NOT required for MCP server core functionality

## Configuration

Create `mcp_config.json`:

```json
{
  "name": "pptx-mcp-server",
  "version": "1.0.0",
  "description": "MCP server for PowerPoint PPTX file manipulation",
  "capabilities": {
    "tools": true,
    "resources": true
  }
}
```



## Containerization

### Dockerfile (`docker/Dockerfile`)

Multi-stage build for optimized container size:

```dockerfile
# Stage 1: Build dependencies
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libxml2-dev \
    libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime image
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libxml2 \
    libxslt1.1 \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY mcp_server/ ./mcp_server/
COPY scripts/ ./scripts/
COPY mcp_config.json .

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Set Python path
ENV PYTHONPATH=/app

# Create directory for PPTX files (mounted as volume)
RUN mkdir -p /data/pptx

# MCP servers communicate via stdio, so no exposed ports needed
# But we set up for potential future HTTP transport
EXPOSE 8000

# Entry point for MCP server
ENTRYPOINT ["python", "-m", "mcp_server.server"]
CMD []
```



### Docker Compose (`docker/docker-compose.yml`)

For local development and testing:

```yaml
version: '3.8'

services:
  pptx-mcp-server:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    container_name: pptx-mcp-server
    volumes:
      # Mount PPTX files directory
            - ../src/deck:/data/pptx:rw
      # Optional: mount entire src directory for development
            - ../src:/app/src:ro
    environment:
            - PYTHONUNBUFFERED=1
            - LOG_LEVEL=INFO
    # MCP servers use stdio, but keep container running for development
    stdin_open: true
    tty: true
    # For health checks (optional)
    healthcheck:
      test: ["CMD", "python", "-c", "import mcp_server; print('OK')"]
      interval: 30s
      timeout: 10s
      retries: 3
    # Resource limits
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 256M
```



### Docker Ignore (`docker/.dockerignore`)

```dockerignore
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.so
*.egg
*.egg-info/
dist/
build/
.venv/
venv/
.env
.git/
.gitignore
*.md
.cursor/
.vscode/
*.log
.pytest_cache/
.coverage
htmlcov/
```



### Container Considerations

**MCP Server Communication:**

- MCP servers communicate via **stdio** (stdin/stdout) using JSON-RPC
- No HTTP server needed for standard MCP operation
- Container runs as a process that the AI agent launches and communicates with via stdio

**Volume Mounts:**

- Mount PPTX files directory as read-write volume
- Allows MCP server to read and modify PPTX files
- Path mapping: host paths → container paths handled in tool implementations
- **Important**: Tool implementations must handle path translation between host and container paths, or use consistent mount points

**Security:**

- Run container as non-root user (add to Dockerfile)
- Limit file system access to mounted volumes only
- No network exposure needed (stdio communication)

**Development vs Production:**

- Development: Use Docker Compose with volume mounts for live code changes
- Production: Build optimized image, mount only data directories

### Usage Examples

**Build and Run Locally:**

```bash
# Build image
docker build -f docker/Dockerfile -t pptx-mcp-server:latest .

# Run container (stdio mode for MCP)
docker run -it --rm \
  -v $(pwd)/src/deck:/data/pptx:rw \
  pptx-mcp-server:latest
```

**Docker Compose:**

```bash
# Start service
docker-compose -f docker/docker-compose.yml up

# Run in background
docker-compose -f docker/docker-compose.yml up -d

# View logs
docker-compose -f docker/docker-compose.yml logs -f
```

**Integration with AI Agent:**

The AI agent (e.g., Claude Desktop, custom MCP client) would launch the container:

```json
{
  "mcpServers": {
    "pptx": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-v", "/path/to/pptx:/data/pptx:rw",
        "pptx-mcp-server:latest"
      ]
    }
  }
}
```



### Benefits of Containerization

1. **Isolation**: Dependencies and environment isolated from host
2. **Portability**: Works consistently across different systems
3. **Scalability**: Easy to deploy multiple instances
4. **Security**: Sandboxed execution environment
5. **Versioning**: Tagged images for different versions
6. **CI/CD**: Easy integration with deployment pipelines

## Testing Strategy

1. Unit tests for core operations
2. Integration tests for MCP server communication
3. Test with sample PPTX files
4. Validate preservation of animations/transitions

## Migration Path

- Existing scripts (`pptx_notes.py`, `update_notes_format.py`) remain functional
- MCP server can call existing functions where appropriate
- Gradual migration of functionality to MCP tools

## Architecture Principles

### Separation of Concerns

**MCP Server Responsibilities:**

- PPTX file manipulation (read, write, edit)
- Safe file operations (backup, validation)
- Structure operations (formatting, layout)
- **NOT** content generation (translation, summarization, AI processing)

**AI Agent Responsibilities:**

- Content generation using LLM
- Translation and summarization
- Language detection
- Natural language understanding
- Orchestrating multiple MCP tool calls

### Benefits of This Approach

1. **Flexibility**: AI agent can use any LLM (OpenAI, Anthropic, Azure, local models)
2. **Maintainability**: MCP server is simpler, focused on one domain
3. **Reusability**: MCP server can be used by different AI agents with different LLMs
4. **Testability**: Easier to test PPTX operations without LLM dependencies
5. **Performance**: No LLM overhead in MCP server, faster tool execution
6. **Cost**: LLM costs are managed by the AI agent, not embedded in MCP server

## Next Steps

1. Set up MCP server structure
2. Implement core PPTX handler with read operations
3. Implement basic edit tools
4. Add slide management tools
5. Integrate image extraction
6. Containerize MCP server (Docker setup)
7. Test with AI agents