---
name: semi-design-guide
description: A complete guide to using Semi Design components, including MCP tool workflows, common patterns, and best practices. Use this skill when you need to query Semi Design components, generate component code, or resolve usage issues.
user-invocable: false
---

# Semi Design User Guide

This skill helps you efficiently use the Semi Design component library for common development tasks.

## File Description

This skill consists of the following files, each focusing on specific aspects of guidance:

### WORKFLOWS.md

**Content**: Complete workflows for using Semi MCP tools.

**Includes**:

- MCP Tool Overview: Introduction to the four tools `get_semi_document`, `get_component_file_list`, `get_file_code`, and `get_function_code` with their functions and use cases
- Basic Query Flow: A four-step process of finding components → querying details → viewing source code → viewing function implementations
- Complete Task Examples: Detailed steps for common scenarios including Table filtering, form validation, cascading selectors, drag-and-drop sorting, etc.
- Common Query Tips: Version-specific queries, getting complete code, error troubleshooting processes, etc.

**When to Use**: When you need to query component documentation, understand component APIs, or implement a specific feature but are unsure how to start.

### BEST_PRACTICES.md

**Content**: Best practices and considerations for using Semi Design components.

**Includes**:

- Component Import Methods: Recommended ways to directly import components, icons, and styles
- Theme Customization Guide: Directing AI to consult official customization documentation
- React 19 Compatibility: Instructions on how to get React 19-related component usage guidelines
- Component Extension Methods: How to extend Semi components through inheritance and modify internal UI when props cannot meet requirements

**When to Use**: When you need to ensure code follows best practices or resolve difficult component usage issues.

## Quick Navigation

| Need                                     | See                                  |
| ---------------------------------------- | ------------------------------------ |
| How to use MCP tools to query components | [workflow.md](workflow.md)           |
| Best practices for component usage       | [best-practice.md](best-practice.md) |

## Overview

Semi Design is an enterprise-level UI component library developed by ByteDance. This skill works with [Semi MCP](/start/ai-mcp) tools to provide:

- **Workflows**: Complete processes for querying components and generating code using MCP tools
- **Practices**: Best practices to avoid common pitfalls
