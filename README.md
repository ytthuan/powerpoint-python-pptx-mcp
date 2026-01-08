# PowerPoint PPTX Notes Automation

A Python project for building automated processes for PowerPoint speaker notes processing, translation, and management using Azure Foundry Models Response API.

## Features

- **MCP Server**: Model Context Protocol server for PPTX manipulation via AI agents
- **Automated Note Processing**: Process PPTX speaker notes with AI-powered translation and summarization
- **Multi-language Support**: Translate between Vietnamese and English, with automatic language detection
- **Dual Version Generation**: Automatically create both short (30-50% length) and full versions of speaker notes
- **Azure Foundry Integration**: Uses Azure Foundry Models Response API for high-quality AI processing
- **Safe PPTX Editing**: Preserves slide structure, animations, and transitions using zip-based editing
- **Parallel Processing**: Process multiple slides concurrently for faster execution
- **Status Tracking**: Automatic progress tracking with resume capability for interrupted runs
- **Batch Processing**: Process entire presentations or specific slides

## Project Structure

```
.
├── mcp_server/                 # MCP server implementation
│   ├── core/                   # Core PPTX handling and safe editing
│   ├── tools/                  # MCP tools (read, edit, slide, notes)
│   ├── resources/              # MCP resources (PPTX file discovery)
│   └── server.py              # Main MCP server entry point
├── scripts/
│   ├── pptx_notes.py          # Basic PPTX notes dump/apply utilities
│   └── update_notes_format.py  # Automated processing with Azure Foundry Models
├── docker/                     # Docker configuration
│   ├── Dockerfile             # Docker image definition
│   └── docker-compose.yml     # Docker Compose configuration
├── src/
│   ├── deck/                   # PPTX files and JSON dumps
│   ├── notes/                  # Documentation and notes
│   └── references/             # Reference materials
├── requirements.txt            # Python dependencies
├── mcp_config.json            # MCP server metadata
├── AGENTS.md                   # Agent instructions and guidelines
└── README.md                   # This file
```

## Installation

### Prerequisites

- Python 3.8 or higher
- Azure subscription with Foundry Models access (for automated note processing)
- Azure AI Project endpoint and model deployment (for automated note processing)
- Docker and Docker Compose (optional, for Docker setup)

## Setup

### Option 1: Virtual Environment Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd powerpoint-python-pptx-mcp
   ```

2. **Create virtual environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Verify installation**:
   ```bash
   python3 -m mcp_server.server --help
   ```
   
   Or test the server starts correctly:
   ```bash
   python3 -c "from mcp_server.server import server; print('✓ Server ready')"
   ```

5. **Configure Azure credentials** (for automated note processing):
   
   Create a `.env` file in the project root:
   ```bash
   AZURE_AI_PROJECT_ENDPOINT=https://YOUR-RESOURCE-NAME.services.ai.azure.com/api/projects/YOUR_PROJECT_NAME
   MODEL_DEPLOYMENT_NAME=your-deployment-name
   ```
   
   Or set environment variables:
   ```bash
   export AZURE_AI_PROJECT_ENDPOINT="https://YOUR-RESOURCE-NAME.services.ai.azure.com/api/projects/YOUR_PROJECT_NAME"
   export MODEL_DEPLOYMENT_NAME="your-deployment-name"
   ```

   **Note**: The script uses `DefaultAzureCredential()` for authentication, which supports:
   - Azure CLI authentication (`az login`)
   - Managed Identity (when running on Azure)
   - Environment variables
   - Visual Studio Code authentication
   - And more (see [Azure Identity documentation](https://learn.microsoft.com/en-us/python/api/azure-identity/azure.identity.defaultazurecredential))

### Option 2: Docker Setup

1. **Build the Docker image**:
   ```bash
   docker build -f docker/Dockerfile -t pptx-mcp-server:latest .
   ```

2. **Run with Docker Compose** (recommended):
   ```bash
   docker-compose -f docker/docker-compose.yml up -d
   ```

   This will:
   - Build the image if needed
   - Mount `src/deck` directory for PPTX file access
   - Keep the container running for MCP connections

3. **Run standalone Docker container**:
   ```bash
   docker run -it --rm \
     -v $(pwd)/src/deck:/data/pptx:rw \
     pptx-mcp-server:latest
   ```

4. **Verify Docker setup**:
   ```bash
   docker exec pptx-mcp-server python -c "from mcp_server.server import server; print('✓ Server ready')"
   ```

## Connecting to MCP Server

The MCP server exposes PPTX manipulation capabilities as tools and resources that can be used by AI agents (like Cursor, Claude Desktop, VSCode, etc.).

### For VSCode (with Docker Compose)

📖 **See [VSCODE_SETUP.md](VSCODE_SETUP.md) for detailed step-by-step instructions.**

Quick setup:
1. Start Docker Compose: `docker-compose -f docker/docker-compose.yml up -d`
2. Configure VSCode settings (see `VSCODE_SETUP.md`)
3. Restart VSCode and open Copilot Chat

### For Cursor IDE

1. **Open Cursor Settings** → **Features** → **Model Context Protocol**

2. **Add MCP Server Configuration**:

   **For Virtual Environment**:
   ```json
   {
     "mcpServers": {
       "pptx": {
         "command": "python3",
         "args": ["-m", "mcp_server.server"],
         "cwd": "/path/to/powerpoint-python-pptx-mcp",
         "env": {}
       }
     }
   }
   ```

   **For Docker**:
   ```json
   {
     "mcpServers": {
       "pptx": {
         "command": "docker",
         "args": [
           "run", "-i", "--rm",
           "-v", "/path/to/powerpoint-python-pptx-mcp/src/deck:/data/pptx:rw",
           "pptx-mcp-server:latest"
         ],
         "env": {}
       }
     }
   }
   ```

   **For Docker Compose** (requires container to be running):
   ```json
   {
     "mcpServers": {
       "pptx": {
         "command": "docker-compose",
         "args": [
           "-f", "/path/to/powerpoint-python-pptx-mcp/docker/docker-compose.yml",
           "exec", "-T", "pptx-mcp-server",
           "python", "-m", "mcp_server.server"
         ],
         "cwd": "/path/to/powerpoint-python-pptx-mcp",
         "env": {}
       }
     }
   }
   ```

3. **Restart Cursor** to load the MCP server

4. **Verify Connection**: The MCP server should appear in Cursor's MCP status, and you should see available tools like:
   - `read_slide_content`
   - `read_slide_text`
   - `update_slide_text`
   - `read_notes`
   - `update_notes`
   - And more...

### For Claude Desktop

1. **Edit Claude Desktop Configuration**:
   
   **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   
   **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

2. **Add MCP Server** (same JSON format as Cursor above)

3. **Restart Claude Desktop**

### For Other MCP Clients

The server uses the standard MCP protocol over stdio. Any MCP-compatible client can connect by:

1. **Starting the server process** with stdio communication
2. **Sending JSON-RPC messages** over stdin/stdout
3. **Receiving responses** on stdout

Example connection test:
```bash
# The server communicates via stdio, so it's typically launched by the MCP client
# But you can test it manually:
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' | python3 -m mcp_server.server
```

### Available MCP Tools

Once connected, the following tools are available:

**Read Tools**:
- `read_slide_content` - Get comprehensive slide content (text, shapes, images)
- `read_slide_text` - Extract all text from a slide
- `read_slide_images` - Get image information from a slide
- `read_presentation_info` - Get presentation metadata

**Edit Tools**:
- `update_slide_text` - Update text in a shape
- `replace_slide_image` - Replace an image on a slide
- `add_text_box` - Add a new text box
- `add_image` - Add a new image

**Slide Management**:
- `add_slide` - Add a new slide
- `delete_slide` - Delete a slide
- `duplicate_slide` - Duplicate a slide
- `change_slide_layout` - Change slide layout

**Notes Tools**:
- `read_notes` - Read speaker notes from slide(s)
- `update_notes` - Update speaker notes (safe zip-based editing)
- `format_notes_structure` - Format notes into short/original structure

### Available MCP Resources

The server automatically discovers PPTX files in:
- Current working directory
- `src/deck/` directory
- `src/` directory

Resources are exposed with URI format: `pptx:///path/to/file.pptx`

### Testing the MCP Server

To verify the server is working correctly, use the test script:

**Quick test (recommended)**:
```bash
python3 test_mcp_server.py --quick
```

This verifies:
- ✅ All dependencies are installed
- ✅ Server module can be imported
- ✅ All 15 tools are properly registered

**Full test (with MCP communication)**:
```bash
python3 test_mcp_server.py
```

This tests:
- ✅ Server initialization via JSON-RPC
- ✅ Tool listing via MCP protocol
- ✅ Full stdio communication

**Note**: When you run `python3 -m mcp_server.server` directly, you'll see:
```
2026-01-06 21:56:48,938 - __main__ - INFO - Starting PPTX MCP Server..
```

This is **normal** - the server is working correctly! It's waiting for JSON-RPC messages on stdin. The server is designed to be started by MCP clients (like Cursor), not run directly in a terminal.

### Troubleshooting MCP Connection

1. **Server not starting**:
   - Verify Python environment: `python3 -c "from mcp_server.server import server; print('✓ OK')"`
   - Check dependencies: `pip list | grep mcp`
   - Run test script: `python3 test_mcp_server.py --quick`
   - Review logs for errors

2. **Tools not appearing**:
   - Ensure MCP server is properly configured in client settings
   - Restart the client application
   - Check that the server process is running
   - Verify with test script: `python3 test_mcp_server.py --quick`

3. **File access issues**:
   - Verify file paths are correct
   - Check file permissions
   - For Docker: ensure volumes are mounted correctly

4. **Connection timeout**:
   - Ensure the server starts quickly (check for slow imports)
   - Verify stdio communication is working
   - Check for blocking operations in server startup
   - Test with: `python3 test_mcp_server.py`

### Quick Start: Using the MCP Server

Once connected to an MCP client (like Cursor), you can interact with PPTX files using natural language:

**Example interactions**:
- "Read the content of slide 5 from presentation.pptx"
- "Update the notes on slide 3 with this text: ..."
- "Add a new slide after slide 10"
- "List all images in the presentation"
- "Get all speaker notes from the presentation"

The MCP server automatically:
- Discovers PPTX files in common directories
- Provides safe editing that preserves animations and transitions
- Handles errors gracefully with informative messages

For more details on available tools and their parameters, see:
- **[MCP_AGENT_INSTRUCTIONS.md](MCP_AGENT_INSTRUCTIONS.md)** - Comprehensive guide for AI agents using the MCP server
- **[AGENTS.md](AGENTS.md)** - Project-specific agent guidelines and workflows

## Usage

### Basic Operations

#### 1. Dump Notes to JSON

Extract all speaker notes from a PPTX file:

```bash
python3 scripts/pptx_notes.py dump "path/to/presentation.pptx"
```

This creates a JSON file (e.g., `presentation.notes.json`) with all slide notes.

#### 2. Automated Processing with Azure Foundry Models

Process notes with automatic translation and summarization:

```bash
python3 scripts/update_notes_format.py \
  --input "path/to/notes.json" \
  --pptx "path/to/presentation.pptx" \
  --output-language vietnamese
```

**Options**:
- `--input`: Input JSON file (default: `src/deck/current-notes-dump.json`)
- `--output`: Output JSON file (default: same as input)
- `--pptx`: PPTX file to update automatically after processing
- `--output-language`: Target language (`vietnamese` or `english`, default: `vietnamese`)
- `--endpoint`: Azure AI Project endpoint (or use `AZURE_AI_PROJECT_ENDPOINT` env var)
- `--deployment-name`: Model deployment name (or use `MODEL_DEPLOYMENT_NAME` env var)
- `--in-place`: Update PPTX in-place (default: creates new file with `.updated.pptx` suffix)
- `--batch-size`: Number of slides to process in parallel (default: 5)
- `--status-file`: Path to status tracking file (default: `input_file.status.json`)
- `--resume`: Resume from status file, skipping already successful slides
- `--dry-run`: Test processing without making API calls

**Examples**:

First activate the virtual environment:
```bash
source .venv/bin/activate
```
Then run the following commands:
```bash
# Process notes and update PPTX automatically
python3 scripts/update_notes_format.py \
  --input src/deck/current-notes-dump.json \
  --pptx "src/deck/presentation.pptx" \
  --output-language vietnamese \
  --in-place

# Process with parallel batch (10 workers) and update PPTX automatically
python3 scripts/update_notes_format.py \
  --input src/deck/original-notes-backup.json \
  --pptx "src/deck/Microsoft Fabric technical Slide Library.PPTX" \
  --batch-size 10 \
  --output-language vietnamese \
  --in-place

# Resume processing after interruption
python3 scripts/update_notes_format.py \
  --input src/deck/current-notes-dump.json \
  --resume

# Dry run to test without API calls
python3 scripts/update_notes_format.py \
  --input src/deck/current-notes-dump.json \
  --dry-run \
  --batch-size 3
```

#### 3. Manual Note Updates

Apply manually edited notes to PPTX:

```bash
python3 scripts/pptx_notes.py apply \
  "path/to/presentation.pptx" \
  "path/to/updates.json" \
  --in-place \
  --engine zip
```

**Engines**:
- `zip` (default): Safely edits only notes XML parts, preserves everything else
- `python-pptx`: Rewrites entire PPTX (use only if needed)

### Note Format

The automated processing creates notes in this format:

```
- Short version:
[Brief summary covering only key points - 30-50% of original length]

- Original:
[Full translation/explanation with all details, examples, and explanations]
```

## How It Works

### Automated Processing Pipeline

1. **Language Detection**: Automatically detects if notes are in Vietnamese or English
2. **Long Version Creation**:
   - If notes are English and target is Vietnamese → translates to Vietnamese
   - If notes are Vietnamese and target is Vietnamese → skips translation
   - Maintains conversational, speakable tone
3. **Short Version Creation**:
   - Generates concise summary (30-50% of original length)
   - Preserves key points and main ideas
   - Outputs in target language
4. **PPTX Update**: Automatically updates PPTX file with formatted notes

### Parallel Processing & Status Tracking

The script processes slides in parallel batches for improved performance:

- **Parallel Execution**: Multiple slides are processed concurrently (configurable with `--batch-size`)
- **Status Tracking**: A `.status.json` file tracks progress for each slide:
  - `success`: Slide processed successfully
  - `failed`: Processing failed (with error message)
  - `processing`: Currently being processed
  - `skipped`: Empty notes (skipped)
- **Resume Capability**: Use `--resume` to continue from where you left off:
  - Automatically skips already successful slides
  - Retries failed slides
  - Preserves existing output data
- **Thread-Safe**: Status updates are thread-safe for parallel processing

### Azure Foundry Models Integration

The project uses Azure Foundry Models Response API for:
- **Translation**: High-quality translation between Vietnamese and English
- **Summarization**: Intelligent extraction of key points while maintaining context
- **Language Detection**: Automatic detection of input language

The script uses `DefaultAzureCredential()` for authentication, supporting multiple Azure authentication methods.

## Speaker Notes Style Guidelines

When generating speaker notes:

- **Address audience as "anh/chị"** (Vietnamese)
- **Use "chúng ta"** when referring to shared actions/goals
- **Keep sentences short and speakable**
- **Maintain conversational, casual tone**
- **Avoid overly formal or academic phrasing**

## Safety Features

- **Zip-based editing**: Only modifies notes XML parts, preserving slide structure, animations, and transitions
- **In-place updates**: Uses temporary files to safely overwrite PPTX files
- **Backup recommendation**: Always backup large PPTX files before processing
- **Error handling**: Falls back gracefully if API calls fail
- **Status tracking**: Progress is saved continuously, allowing safe interruption and resume
- **Dry-run mode**: Test processing logic without making API calls

## Requirements

- `python-pptx>=1.0.0` - PPTX file manipulation
- `lxml>=4.9.0` - XML processing
- `azure-identity` - Azure authentication
- `azure-ai-projects>=2.0.0b1` - Azure Foundry Models integration
- `dotenv` - Environment variable management

## Troubleshooting

### Authentication Issues

If you encounter authentication errors:

1. **Azure CLI**: Run `az login` to authenticate
2. **Environment Variables**: Ensure `AZURE_AI_PROJECT_ENDPOINT` and `MODEL_DEPLOYMENT_NAME` are set
3. **Permissions**: Verify your Azure account has access to the Foundry project

### API Errors

- **Rate Limiting**: The script includes automatic retry with exponential backoff
- **Model Availability**: Ensure your deployment name is correct and the model is available
- **Endpoint Format**: Verify endpoint URL format: `https://YOUR-RESOURCE-NAME.services.ai.azure.com/api/projects/YOUR_PROJECT_NAME`

### PPTX Issues

- **Large Files**: Processing large PPTX files may take time; be patient
- **Corrupted Files**: Always work with backups
- **Empty Notes**: Empty notes are skipped automatically

## Contributing

This project is designed for automated PPTX notes processing. When contributing:

- Follow the style guidelines in `AGENTS.md`
- Test with sample PPTX files before making changes
- Preserve PPTX structure and formatting
- Document any new features or changes

## License

[Add your license information here]

## References

- [Azure Foundry Models Documentation](https://learn.microsoft.com/en-us/azure/ai-foundry/foundry-models/)
- [Azure Identity Documentation](https://learn.microsoft.com/en-us/python/api/azure-identity/)
- [python-pptx Documentation](https://python-pptx.readthedocs.io/)

