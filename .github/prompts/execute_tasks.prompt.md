---
description: Instructions for AI agents to execute tasks from task breakdown documents
---

# Task Execution Guidelines for AI Agents

## Overview

This document provides comprehensive instructions for AI agents executing tasks from task breakdown documents created for the Daily Scribe project. These guidelines ensure consistent, high-quality implementation while maintaining project standards and user collaboration.

## Project Context

You are working on the Daily Scribe project, a news aggregation and summarization application with:
- **Backend**: Python with FastAPI, SQLite database, local LLM integration
- **Frontend**: React application with modern JavaScript
- **Architecture**: Monorepo with clear separation of concerns
- **Quality Standards**: High test coverage, comprehensive documentation, security-first approach

## Task Execution Protocol

### 1. Pre-Execution Preparation

**Before starting any task:**

1. **Read the complete task breakdown document** to understand the full scope
2. **Identify the current task** - always work on the next uncompleted task in dependency order
3. **Review dependencies** - ensure all prerequisite tasks are completed
4. **Understand acceptance criteria** - know exactly what constitutes task completion
5. **Check existing codebase** - understand current implementation and integration points

### 2. Task Implementation Rules

**Critical Implementation Rules:**

- ✅ **One task at a time**: Complete the current task fully before moving to the next
- ✅ **Sequential execution**: Follow dependency order strictly
- ✅ **User approval required**: Stop after each task and wait for explicit user permission to continue
- ✅ **Mark completion**: Update task status immediately upon completion
- ✅ **Quality first**: Meet all acceptance criteria before considering a task complete

### 3. Task Completion Protocol

**When you finish a task:**

1. **Verify all acceptance criteria** are met
2. **Update the task file** - mark the task as completed: `[ ]` → `[x]`
3. **Update the "Relevant Files" section** with any new or modified files
4. **Test your implementation** to ensure it works as expected
5. **Stop and request permission** before proceeding to the next task

**Format for requesting permission:**
```
Task [X] completed successfully. All acceptance criteria met:
- [List key achievements]
- [Note any files created/modified]

Ready to proceed to Task [Y]: [Brief Title]?
Please respond with "yes" or "y" to continue.
```

## Implementation Standards

### Code Quality Requirements

**Python Backend Code:**
- Follow PEP 8 style guidelines
- Use type hints for all function parameters and return values
- Implement proper error handling with specific exception types
- Write docstrings for all public functions and classes
- Use dependency injection and proper separation of concerns
- Follow existing project patterns and architecture

**React Frontend Code:**
- Use functional components with hooks
- Implement proper state management (useState, useReducer, Context API)
- Follow component composition patterns
- Use proper prop types with TypeScript (if applicable)
- Implement error boundaries and loading states
- Follow existing component structure and naming conventions

**Testing Requirements:**
- Write unit tests for all new functions and components
- Implement integration tests for API endpoints
- Use appropriate testing frameworks (pytest for Python, Jest/RTL for React)
- Aim for >90% test coverage on new code
- Test both happy path and error scenarios

### File Organization

**When creating new files:**
- Follow existing project structure and naming conventions
- Place files in appropriate directories based on their purpose
- Use clear, descriptive file names
- Include proper imports and exports
- Add file headers with brief descriptions when appropriate

**When modifying existing files:**
- Understand the existing code structure before making changes
- Maintain consistency with existing patterns
- Preserve existing functionality unless explicitly changing it
- Update related tests and documentation

### API Development Guidelines

**When implementing FastAPI endpoints:**
- Use proper HTTP status codes and error responses
- Implement request/response validation with Pydantic models
- Add comprehensive error handling
- Include proper CORS configuration
- Document endpoints with clear descriptions and examples
- Follow RESTful conventions where applicable

**When integrating with existing services:**
- Use existing database connections and session management
- Leverage existing utility functions and helpers
- Maintain consistency with existing API patterns
- Handle database transactions properly

## Error Handling and Debugging

### When Things Go Wrong

**If you encounter errors during implementation:**

1. **Analyze the error** - understand the root cause
2. **Check dependencies** - ensure all required packages/modules are available
3. **Review existing code** - understand how similar functionality is implemented
4. **Test incrementally** - build and test small pieces at a time
5. **Ask for help** - if stuck, explain the issue and ask for guidance

**Common Issues and Solutions:**

- **Import errors**: Check Python path and package structure
- **Database errors**: Verify database schema and connection setup
- **Frontend errors**: Check component dependencies and prop passing
- **API errors**: Verify endpoint configuration and request/response format

### Quality Assurance Checklist

**Before marking a task complete, verify:**

- [ ] All acceptance criteria are met
- [ ] Code follows project style guidelines
- [ ] Tests are written and passing
- [ ] No new linting or type errors introduced
- [ ] Integration with existing code works correctly
- [ ] Performance requirements are met (if specified)
- [ ] Error handling is implemented
- [ ] Documentation is updated (if required)

## Task File Maintenance

### Updating Task Status

**Task completion format:**
```markdown
- [x] Task 1: Brief Title ✓ Completed
  - [x] Subtask 1.1: Specific requirement ✓
  - [x] Subtask 1.2: Another requirement ✓
```

**Adding new tasks or modifications:**
- If scope changes or new requirements emerge, add them to the task file
- Use clear task numbering and maintain dependency relationships
- Update timeline estimates if significant changes occur

### Relevant Files Section

**Maintain an up-to-date "Relevant Files" section:**
```markdown
## Relevant Files

### Backend Files
- `src/api.py` - Added new digest simulation endpoints
- `src/components/digest_builder.py` - Enhanced for simulation support
- `tests/test_api.py` - Added tests for new endpoints

### Frontend Files  
- `frontend/src/components/DigestSimulator.js` - Main simulator component
- `frontend/src/components/DigestDatePicker.js` - Date selection interface
- `frontend/src/App.js` - Added routing for simulator page
```

## Communication with User

### Progress Updates

**Regular communication should include:**
- Clear description of what was completed
- Any challenges encountered and how they were resolved
- Files that were created or modified
- Next steps and dependencies

### Asking for Help

**When you need assistance:**
- Describe the specific issue or blocker
- Explain what you've tried already
- Provide relevant error messages or context
- Suggest possible approaches if you have ideas

### Requesting Clarification

**When requirements are unclear:**
- Reference the specific acceptance criteria in question
- Explain your understanding and ask for confirmation
- Propose alternative approaches if multiple interpretations exist

## Testing and Validation

### Testing Strategy

**For each task implementation:**
1. **Unit tests**: Test individual functions and components in isolation
2. **Integration tests**: Test API endpoints and component interactions
3. **Manual testing**: Verify functionality works as expected in the UI
4. **Edge case testing**: Test error conditions and boundary cases

### Validation Process

**Before requesting to proceed:**
1. Run all existing tests to ensure no regressions
2. Test your new functionality manually
3. Verify performance requirements are met
4. Check that error handling works correctly
5. Validate that the implementation matches acceptance criteria exactly

## Success Metrics

### Task-Level Success
- All acceptance criteria are verifiably met
- Code quality standards are maintained
- No regressions introduced to existing functionality
- Proper testing coverage implemented

### Project-Level Success
- User story requirements are fully satisfied
- Implementation integrates seamlessly with existing codebase
- Performance and security requirements are met
- Documentation is comprehensive and up-to-date

---

## Example Task Execution Flow

```
1. Read Task 1: "Implement Digest Simulation API Endpoint"
2. Review acceptance criteria and technical details
3. Check existing DigestBuilder and DatabaseService implementations
4. Implement the new endpoint in src/api.py
5. Add proper error handling and validation
6. Write unit tests for the endpoint
7. Test manually with different date parameters
8. Update task file: mark Task 1 as [x] completed
9. Update Relevant Files section
10. Request permission: "Task 1 completed. Ready for Task 2?"
```

**Remember**: Quality and accuracy are more important than speed. Take time to implement tasks correctly the first time, following all project standards and guidelines.
# Task List Management

Guidelines for managing task lists in markdown files to track progress on completing a PRD

## Task Implementation
- **One sub-task at a time:** Do **NOT** start the next sub‑task until you ask the user for permission and they say “yes” or "y"
- **Completion protocol:**  
  1. When you finish a **sub‑task**, immediately mark it as completed by changing `[ ]` to `[x]`.  
  2. If **all** subtasks underneath a parent task are now `[x]`, also mark the **parent task** as completed.  
- Stop after each sub‑task and wait for the user’s go‑ahead.

## Task List Maintenance

1. **Update the task list as you work:**
   - Mark tasks and subtasks as completed (`[x]`) per the protocol above.
   - Add new tasks as they emerge.

2. **Maintain the “Relevant Files” section:**
   - List every file created or modified.
   - Give each file a one‑line description of its purpose.

## AI Instructions

When working with task lists, the AI must:

1. Regularly update the task list file after finishing any significant work.
2. Follow the completion protocol:
   - Mark each finished **sub‑task** `[x]`.
   - Mark the **parent task** `[x]` once **all** its subtasks are `[x]`.
3. Add newly discovered tasks.
4. Keep “Relevant Files” accurate and up to date.
5. Before starting work, check which sub‑task is next.
6. After implementing a sub‑task, update the file and then pause for user approval.