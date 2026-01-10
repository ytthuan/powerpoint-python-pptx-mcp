# PowerPoint MCP Server Agent Skill

This directory contains the Agent Skill for the PowerPoint MCP Server, following the VS Code Agent Skills format described in the [VS Code Agent Skills documentation](https://code.visualstudio.com/docs/copilot/customization/agent-skills).

## What is an Agent Skill?

Agent Skills are folders of instructions, scripts, and resources that AI agents can load on-demand when relevant, to improve performance in specialized tasks.

## Structure

```
.github/skills/pptx-mcp-server/
├── SKILL.md          # Main skill file with instructions
└── README.md         # This file
```

## Usage

### For GitHub Copilot in VS Code

When working in this repository, GitHub Copilot in VS Code can discover and use this skill when you ask about PPTX manipulation or speaker notes workflows.

Example prompts:
- "Translate all speaker notes to Vietnamese"
- "Read the notes from slides 1-10"
- "Update the notes on slide 5 with this content..."

Notes:
- Agent Skills support in VS Code is preview and typically requires enabling the `chat.useAgentSkills` setting (see the VS Code docs above).

### For Other Agents / Personal Skills

### Personal Skills

To use this skill across all your projects, copy it to your personal skills directory:

```bash
# macOS/Linux
mkdir -p ~/.github/skills
cp -r .github/skills/pptx-mcp-server ~/.github/skills/

# Legacy / other agents may use different locations (example: Claude Desktop)
mkdir -p ~/.claude/skills
cp -r .github/skills/pptx-mcp-server ~/.claude/skills/
```

## Skill Contents

The `SKILL.md` file contains:

1. **Metadata** (YAML frontmatter)
   - `name`: Unique identifier for the skill
   - `description`: What the skill does and when to use it
   - (Optional fields may be used by other clients; VS Code only requires `name` and `description`)

2. **Instructions** (Markdown body)
   - Overview of the MCP server
   - Available tools reference
   - Common workflows with code examples
   - Vietnamese speaker notes guidelines
   - Best practices and error handling
   - Performance tips

## Key Features

- **Comprehensive tool reference** for all MCP server operations
- **Batch operation workflows** for efficient multi-slide processing
- **Vietnamese speaker notes guidelines** for proper translation
- **Error handling patterns** with structured exceptions
- **Performance optimization tips** (50-100x faster with batch ops)

## Learn More

- [Use Agent Skills in VS Code](https://code.visualstudio.com/docs/copilot/customization/agent-skills)
- [Agent Skills standard](https://agentskills.io/)
- [Model Context Protocol Specification](https://modelcontextprotocol.io/)
- [Project README](../../../README.md)

## Implementation Status

Done
Added `.github/skills/pptx-mcp-server/SKILL.md` with VS Code Agent Skills-compliant frontmatter and an authoritative tool/workflow guide.
Updated `AGENTS.md` and this README to keep always-on rules minimal and move detailed guidance into the skill.
