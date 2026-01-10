# Copilot Configuration Documentation

This document explains the GitHub Copilot configuration set up for this repository, following [GitHub's best practices](https://docs.github.com/en/copilot/how-tos/configure-custom-instructions).

## Overview

The repository is configured with comprehensive Copilot instructions to guide AI agents in:
- Understanding the project context and architecture
- Following coding conventions and best practices
- Using specialized agent personas for different tasks
- Applying path-specific guidelines for different parts of the codebase

## Configuration Files

### 1. Repository-wide Instructions
**File**: `.github/copilot-instructions.md` (296 lines)

Provides global context and guidelines for the entire repository:

- **Project context**: MCP server for PPTX manipulation, focus on speaker notes
- **Tech stack**: Python 3.11+, python-pptx, lxml, MCP, pytest, mypy, black
- **Build/test/lint commands**: Complete setup and testing workflows
- **Coding conventions**: Python style, architecture patterns, file organization
- **Boundaries**: Security requirements, performance requirements, what NOT to do
- **Development guidelines**: Adding features, fixing bugs, refactoring
- **PPTX notes processing**: Detailed guidelines for speaker notes work
  - Vietnamese style requirements (pronouns, tone, format)
  - Required two-version structure (short/original)
  - Recommended workflows with code examples
  - Safety guidelines

### 2. Agent Personas
**File**: `.github/agents/AGENTS.md` (306 lines)

Defines 5 specialized agent personas with specific expertise and boundaries:

#### PPTX Notes Specialist
- Expert in speaker notes processing and Vietnamese translation
- Uses MCP server tools and batch operations
- Boundaries: Never modify slide content, keep empty notes empty

#### Python Code Maintainer
- Expert in Python 3.11+ with strict typing
- Focuses on code quality, testing, and type safety
- Boundaries: Never use `any` type, never skip tests

#### MCP Server Developer
- Expert in MCP protocol and async Python servers
- Focuses on tool design and validation
- Boundaries: Never skip input validation, handle all errors

#### Test Engineer
- Specialist in pytest, coverage, and test patterns
- Writes comprehensive unit and integration tests
- Boundaries: Never skip tests for new features

#### Documentation Writer
- Technical writer for developer documentation
- Maintains README, guides, architecture docs
- Boundaries: Only modify documentation files

### 3. Path-specific Instructions

Three instruction files with YAML frontmatter to scope guidance to specific code areas:

#### Tools Instructions
**File**: `.github/instructions/tools.instructions.md` (126 lines)  
**Scope**: `src/mcp_server/tools/**/*.py`

Guidelines for MCP tool implementations:
- Critical requirements (validation, async, error handling)
- Tool structure pattern with example code
- Input validation checklist
- Error handling and logging patterns
- Performance considerations
- Testing requirements

#### Tests Instructions
**File**: `.github/instructions/tests.instructions.md` (213 lines)  
**Scope**: `tests/**/*.py`

Testing guidelines and best practices:
- Testing principles (behavior over implementation)
- Test structure pattern with examples
- Pytest markers usage
- Fixture patterns
- Coverage requirements (85%+)
- Async testing patterns
- Mocking and parametrization
- Common anti-patterns to avoid

#### Core Services Instructions
**File**: `.github/instructions/core.instructions.md` (314 lines)  
**Scope**: `src/mcp_server/core/**/*.py`  
**Exclude**: `documentation-writer` agent

Guidelines for core PPTX services:
- Critical requirements (no data loss, safe operations)
- PPTX handler patterns
- Safe file operations with backups
- Zip-based editing for notes (preserves animations)
- Error handling with specific exceptions
- Memory management for large files
- Performance optimization techniques

## How Copilot Uses These Instructions

### Instruction Priority
When Copilot processes a request, instructions are combined in this order:
1. **User instructions** (if provided)
2. **Path-specific instructions** (matching the file being edited)
3. **Repository instructions** (global .github/copilot-instructions.md)
4. **Agent instructions** (if using a specific agent persona)
5. **Organization instructions** (if configured at org level)

### Scoping Rules
- Path-specific instructions use glob patterns in YAML frontmatter
- `applyTo: "src/mcp_server/tools/**/*.py"` matches all Python files in tools/
- `excludeAgent: "documentation-writer"` prevents specific agents from using instructions

## Usage Examples

### Working on MCP Tools
When editing `src/mcp_server/tools/notes_tools.py`:
- Repository instructions apply (coding conventions, tech stack)
- Tools-specific instructions apply (validation patterns, error handling)
- Agent instructions apply if using MCP Server Developer persona

### Writing Tests
When editing `tests/unit/test_notes_tools.py`:
- Repository instructions apply (coding conventions)
- Tests-specific instructions apply (testing patterns, markers)
- Agent instructions apply if using Test Engineer persona

### Working on Speaker Notes
When processing PPTX speaker notes:
- Repository instructions apply (Vietnamese style, two-version format)
- Agent instructions apply if using PPTX Notes Specialist persona
- Core instructions apply if editing core/pptx_handler.py

## Maintaining Instructions

### When to Update

Update instructions when:
- Adding new conventions or patterns to the codebase
- Changing build/test/deployment processes
- Adding new security requirements
- Identifying common mistakes that should be prevented
- New features require specific handling patterns

### Best Practices

1. **Be specific and actionable**: Provide concrete examples, not vague advice
2. **Include code examples**: Show the pattern you want followed
3. **Document boundaries**: Clearly state what NOT to do
4. **Keep it up-to-date**: Review and update as project evolves
5. **Test the instructions**: Verify Copilot follows them correctly

### Review Process

1. Make changes in a PR
2. Test with actual Copilot usage
3. Get review from team
4. Monitor Copilot behavior after merge
5. Iterate based on results

## Verification

To verify the configuration is working:

1. **Check files exist**:
   ```bash
   ls -la .github/copilot-instructions.md
   ls -la .github/agents/AGENTS.md
   ls -la .github/instructions/*.md
   ```

2. **Validate YAML frontmatter**:
   ```bash
   grep -A 2 "^---$" .github/instructions/*.md
   ```

3. **Test with Copilot**:
   - Ask Copilot to create a new MCP tool
   - Verify it follows the patterns from tools.instructions.md
   - Check it includes proper validation, error handling, etc.

## Resources

- [GitHub Copilot Custom Instructions](https://docs.github.com/en/copilot/how-tos/configure-custom-instructions)
- [Best Practices for Copilot Coding Agent](https://docs.github.com/en/copilot/tutorials/coding-agent/get-the-best-results)
- [How to Write a Great agents.md](https://github.blog/ai-and-ml/github-copilot/how-to-write-a-great-agents-md-lessons-from-over-2500-repositories/)
- [Path-specific Instructions](https://github.blog/changelog/2025-07-23-github-copilot-coding-agent-now-supports-instructions-md-custom-instructions/)

## Summary

This comprehensive Copilot configuration provides:
- ✅ Clear project context and tech stack documentation
- ✅ Detailed coding conventions and patterns
- ✅ Specialized agent personas for different roles
- ✅ Path-specific guidelines for tools, tests, and core services
- ✅ Security boundaries and performance requirements
- ✅ Vietnamese speaker notes formatting rules
- ✅ Code examples and workflows throughout

Total: **1,255 lines** of guidance to help Copilot generate high-quality, consistent code.
