---
name: claude-workflows
description: Common workflows and patterns for Claude Code usage - productivity best practices
---

# Common Workflows

Learn about common workflows with Claude Code. Each task includes clear instructions, example commands, and best practices to help you get the most from Claude Code.

## Understand new codebases

### Get a quick codebase overview

Suppose you've just joined a new project and need to understand its structure quickly.

**Steps:**
1. Navigate to the project root directory: `cd /path/to/project`
2. Start Claude Code: `claude`
3. Ask for a high-level overview: `> give me an overview of this codebase`
4. Dive deeper into specific components:
   - `> explain the main architecture patterns used here`
   - `> what are the key data models?`
   - `> how is authentication handled?`

**Tips:**
- Start with broad questions, then narrow down to specific areas
- Ask about coding conventions and patterns used in the project
- Request a glossary of project-specific terms

### Find relevant code

Suppose you need to locate code related to a specific feature or functionality.

**Steps:**
1. Ask Claude to find relevant files: `> find the files that handle user authentication`
2. Get context on how components interact: `> how do these authentication files work together?`
3. Understand the execution flow: `> trace the login process from front-end to database`

**Tips:**
- Be specific about what you're looking for
- Use domain language from the project

---

## Fix bugs efficiently

Suppose you've encountered an error message and need to find and fix its source.

**Steps:**
1. Share the error with Claude: `> I'm seeing an error when I run npm test`
2. Ask for fix recommendations: `> suggest a few ways to fix the @ts-ignore in user.ts`
3. Apply the fix: `> update user.ts to add the null check you suggested`

**Tips:**
- Tell Claude the command to reproduce the issue and get a stack trace
- Mention any steps to reproduce the error
- Let Claude know if the error is intermittent or consistent

---

## Refactor code

Suppose you need to update old code to use modern patterns and practices.

**Steps:**
1. Identify legacy code for refactoring: `> find deprecated API usage in our codebase`
2. Get refactoring recommendations: `> suggest how to refactor utils.js to use modern JavaScript features`
3. Apply the changes safely: `> refactor utils.js to use ES2024 features while maintaining the same behavior`
4. Verify the refactoring: `> run tests for the refactored code`

**Tips:**
- Ask Claude to explain the benefits of the modern approach
- Request that changes maintain backward compatibility when needed
- Do refactoring in small, testable increments

---

## Use specialized subagents

Suppose you want to use specialized AI subagents to handle specific tasks more effectively.

**Steps:**
1. View available subagents: `> /agents`
   - This shows all available subagents and lets you create new ones
2. Use subagents automatically - Claude Code will automatically delegate appropriate tasks:
   - `> review my recent code changes for security issues`
   - `> run all tests and fix any failures`
3. Explicitly request specific subagents:
   - `> use the code-reviewer subagent to check the auth module`
   - `> have the debugger subagent investigate why users can't log in`
4. Create custom subagents for your workflow: `> /agents`
   - Select "Create New subagent" and follow the prompts to define:
   - Subagent type (e.g., `api-designer`, `performance-optimizer`)
   - When to use it
   - Which tools it can access
   - Its specialized system prompt

**Tips:**
- Create project-specific subagents in `.claude/agents/` for team sharing
- Use descriptive `description` fields to enable automatic delegation
- Limit tool access to what each subagent actually needs
- Check the subagents documentation for detailed examples

---

## Use Plan Mode for safe code analysis

Plan Mode instructs Claude to create a plan by analyzing the codebase with read-only operations, perfect for exploring codebases, planning complex changes, or reviewing code safely.

### When to use Plan Mode

- **Multi-step implementation**: When your feature requires making edits to many files
- **Code exploration**: When you want to research the codebase thoroughly before changing anything
- **Interactive development**: When you want to iterate on the direction with Claude

### How to use Plan Mode

**Turn on Plan Mode during a session:**
- Use **Shift+Tab** to cycle through permission modes
- First Shift+Tab switches to Auto-Accept Mode (indicated by `⏵⏵ accept edits on`)
- Next Shift+Tab switches to Plan Mode (indicated by `⏸ plan mode on`)

**Start a new session in Plan Mode:**
```bash
claude --permission-mode plan
```

**Run "headless" queries in Plan Mode:**
```bash
claude --permission-mode plan -p "Analyze the authentication system and suggest improvements"
```

### Example: Planning a complex refactor

```bash
claude --permission-mode plan
```

```
> I need to refactor our authentication system to use OAuth2. Create a detailed migration plan.
```

Claude will analyze the current implementation and create a comprehensive plan. Refine with follow-ups:
- `> What about backward compatibility?`
- `> How should we handle database migration?`

### Configure Plan Mode as default

```json
// .claude/settings.json
{
  "permissions": {
    "defaultMode": "plan"
  }
}
```

---

## Work with tests

Suppose you need to add tests for uncovered code.

**Steps:**
1. Identify untested code: `> find functions in NotificationsService.swift that are not covered by tests`
2. Generate test scaffolding: `> add tests for the notification service`
3. Add meaningful test cases: `> add test cases for edge conditions in the notification service`
4. Run and verify tests: `> run the new tests and fix any failures`

**Tips:**
- Ask for tests that cover edge cases and error conditions
- Request both unit and integration tests when appropriate
- Have Claude explain the testing strategy

---

## Create pull requests

Suppose you need to create a well-documented pull request for your changes.

**Steps:**
1. Summarize your changes: `> summarize the changes I've made to the authentication module`
2. Generate a PR with Claude: `> create a pr`
3. Review and refine: `> enhance the PR description with more context about the security improvements`
4. Add testing details: `> add information about how these changes were tested`

**Tips:**
- Ask Claude directly to make a PR for you
- Review Claude's generated PR before submitting
- Ask Claude to highlight potential risks or considerations

---

## Handle documentation

Suppose you need to add or update documentation for your code.

**Steps:**
1. Identify undocumented code: `> find functions without proper JSDoc comments in the auth module`
2. Generate documentation: `> add JSDoc comments to the undocumented functions in auth.js`
3. Review and enhance: `> improve the generated documentation with more context and examples`
4. Verify documentation: `> check if the documentation follows our project standards`

**Tips:**
- Specify the documentation style you want (JSDoc, docstrings, etc.)
- Ask for examples in the documentation
- Request documentation for public APIs, interfaces, and complex logic

---

## Work with images

Suppose you need to work with images in your codebase, and you want Claude's help analyzing image content.

**Steps:**
1. Add an image to the conversation using any of these methods:
   - Drag and drop an image into the Claude Code window
   - Copy an image and paste it into the CLI with ctrl+v
   - Provide an image path to Claude (e.g., "Analyze this image: /path/to/your/image.png")

2. Ask Claude to analyze the image:
   - `> What does this image show?`
   - `> Describe the UI elements in this screenshot`
   - `> Are there any problematic elements in this diagram?`

3. Use images for context:
   - `> Here's a screenshot of the error. What's causing it?`
   - `> This is our current database schema. How should we modify it for the new feature?`

4. Get code suggestions from visual content:
   - `> Generate CSS to match this design mockup`
   - `> What HTML structure would recreate this component?`

**Tips:**
- Use images when text descriptions would be unclear or cumbersome
- Include screenshots of errors, UI designs, or diagrams for better context
- You can work with multiple images in a conversation
- Image analysis works with diagrams, screenshots, mockups, and more

---

## Reference files and directories

Use @ to quickly include files or directories without waiting for Claude to read them.

**Steps:**
1. Reference a single file: `> Explain the logic in @src/utils/auth.js`
   - This includes the full content of the file in the conversation

2. Reference a directory: `> What's the structure of @src/components?`
   - This provides a directory listing with file information

3. Reference MCP resources: `> Show me the data from @github:repos/owner/repo/issues`
   - This fetches data from connected MCP servers using the format @server:resource

**Tips:**
- File paths can be relative or absolute
- @ file references add CLAUDE.md in the file's directory and parent directories to context
- Directory references show file listings, not contents
- You can reference multiple files in a single message

---

## Use extended thinking

Suppose you're working on complex architectural decisions, challenging bugs, or planning multi-step implementations that require deep reasoning.

**Note:** Extended thinking is disabled by default in Claude Code. You can enable it on-demand by using `Tab` to toggle Thinking on, or by using prompts like "think" or "think hard".

**Steps:**
1. Provide context and ask Claude to think: `> I need to implement a new authentication system using OAuth2. Think deeply about the best approach for implementing this in our codebase.`

2. Refine the thinking with follow-up prompts:
   - `> think about potential security vulnerabilities in this approach`
   - `> think hard about edge cases we should handle`

**Tips for extended thinking:**
- Extended thinking is most valuable for complex tasks such as:
  - Planning complex architectural changes
  - Debugging intricate issues
  - Creating implementation plans for new features
  - Understanding complex codebases
  - Evaluating tradeoffs between different approaches

- Use `Tab` to toggle Thinking on and off during a session
- Prompting variations result in different thinking depths:
  - "think" triggers basic extended thinking
  - "think hard", "think more", "think a lot", or "think longer" trigger deeper thinking

---

## Resume previous conversations

Suppose you've been working on a task with Claude Code and need to continue where you left off in a later session.

Claude Code provides two options for resuming previous conversations:

### Continue the most recent conversation

```bash
claude --continue
```

This immediately resumes your most recent conversation without any prompts.

**Continue in non-interactive mode:**
```bash
claude --continue --print "Continue with my task"
```

Use `--print` with `--continue` to resume the most recent conversation in non-interactive mode, perfect for scripts or automation.

### Show conversation picker

```bash
claude --resume
```

This displays an interactive conversation selector with a clean list view showing:
- Session summary (or initial prompt)
- Metadata: time elapsed, message count, and git branch

Use arrow keys to navigate and press Enter to select a conversation. Press Esc to exit.

**Tips:**
- Conversation history is stored locally on your machine
- Use `--continue` for quick access to your most recent conversation
- Use `--resume` when you need to select a specific past conversation
- When resuming, you'll see the entire conversation history before continuing
- The resumed conversation starts with the same model and configuration as the original

---

## Run parallel Claude Code sessions with Git worktrees

Suppose you need to work on multiple tasks simultaneously with complete code isolation between Claude Code instances.

**Steps:**
1. **Understand Git worktrees:**
   - Git worktrees allow you to check out multiple branches from the same repository into separate directories
   - Each worktree has its own working directory with isolated files, while sharing the same Git history

2. **Create a new worktree:**
   ```bash
   # Create a new worktree with a new branch
   git worktree add ../project-feature-a -b feature-a

   # Or create a worktree with an existing branch
   git worktree add ../project-bugfix bugfix-123
   ```

3. **Run Claude Code in each worktree:**
   ```bash
   # Navigate to your worktree
   cd ../project-feature-a

   # Run Claude Code in this isolated environment
   claude
   ```

4. **Run Claude in another worktree:**
   ```bash
   cd ../project-bugfix
   claude
   ```

5. **Manage your worktrees:**
   ```bash
   # List all worktrees
   git worktree list

   # Remove a worktree when done
   git worktree remove ../project-feature-a
   ```

**Tips:**
- Each worktree has its own independent file state, making it perfect for parallel Claude Code sessions
- Changes made in one worktree won't affect others, preventing Claude instances from interfering with each other
- All worktrees share the same Git history and remote connections
- For long-running tasks, you can have Claude working in one worktree while you continue development in another
- Use descriptive directory names to easily identify which task each worktree is for
- Remember to initialize your development environment in each new worktree according to your project's setup

---

## Use Claude as a unix-style utility

### Add Claude to your verification process

Suppose you want to use Claude Code as a linter or code reviewer.

**Add Claude to your build script:**

```json
// package.json
{
    ...
    "scripts": {
        ...
        "lint:claude": "claude -p 'you are a linter. please look at the changes vs. main and report any issues related to typos. report the filename and line number on one line, and a description of the issue on the second line. do not return any other text.'"
    }
}
```

**Tips:**
- Use Claude for automated code review in your CI/CD pipeline
- Customize the prompt to check for specific issues relevant to your project
- Consider creating multiple scripts for different types of verification

### Pipe in, pipe out

Suppose you want to pipe data into Claude, and get back data in a structured format.

**Pipe data through Claude:**

```bash
cat build-error.txt | claude -p 'concisely explain the root cause of this build error' > output.txt
```

**Tips:**
- Use pipes to integrate Claude into existing shell scripts
- Combine with other Unix tools for powerful workflows
- Consider using --output-format for structured output

### Control output format

**Use text format (default):**
```bash
cat data.txt | claude -p 'summarize this data' --output-format text > summary.txt
```
This outputs just Claude's plain text response (default behavior).

**Use JSON format:**
```bash
cat code.py | claude -p 'analyze this code for bugs' --output-format json > analysis.json
```
This outputs a JSON array of messages with metadata including cost and duration.

**Use streaming JSON format:**
```bash
cat log.txt | claude -p 'parse this log file for errors' --output-format stream-json
```
This outputs a series of JSON objects in real-time as Claude processes the request.

**Tips:**
- Use `--output-format text` for simple integrations where you just need Claude's response
- Use `--output-format json` when you need the full conversation log
- Use `--output-format stream-json` for real-time output of each conversation turn

---

## Create custom slash commands

Claude Code supports custom slash commands that you can create to quickly execute specific prompts or tasks.

### Create project-specific commands

Suppose you want to create reusable slash commands for your project that all team members can use.

**Steps:**
1. Create a commands directory in your project: `mkdir -p .claude/commands`

2. Create a Markdown file for each command:
   ```bash
   echo "Analyze the performance of this code and suggest three specific optimizations:" > .claude/commands/optimize.md
   ```

3. Use your custom command in Claude Code: `> /optimize`

**Tips:**
- Command names are derived from the filename
- You can organize commands in subdirectories
- Project commands are available to everyone who clones the repository
- The Markdown file content becomes the prompt sent to Claude when the command is invoked

### Add command arguments with $ARGUMENTS

Suppose you want to create flexible slash commands that can accept additional input from users.

**Steps:**
1. Create a command file with the $ARGUMENTS placeholder:
   ```bash
   echo 'Find and fix issue #$ARGUMENTS. Follow these steps: 1. Understand the issue described in the ticket 2. Locate the relevant code in our codebase 3. Implement a solution that addresses the root cause 4. Add appropriate tests 5. Prepare a concise PR description' > .claude/commands/fix-issue.md
   ```

2. Use the command with an issue number: `> /fix-issue 123`
   - This will replace $ARGUMENTS with "123" in the prompt

**Tips:**
- The $ARGUMENTS placeholder is replaced with any text that follows the command
- You can position $ARGUMENTS anywhere in your command template
- Other useful applications: generating test cases for specific functions, creating documentation for components, reviewing code in particular files, or translating content to specified languages

### Create personal slash commands

Suppose you want to create personal slash commands that work across all your projects.

**Steps:**
1. Create a commands directory in your home folder: `mkdir -p ~/.claude/commands`

2. Create a Markdown file for each command:
   ```bash
   echo "Review this code for security vulnerabilities, focusing on:" > ~/.claude/commands/security-review.md
   ```

3. Use your personal custom command: `> /security-review`

**Tips:**
- Personal commands show "(user)" in their description when listed with `/help`
- Personal commands are only available to you and not shared with your team
- Personal commands work across all your projects
- You can use these for consistent workflows across different codebases

---

## Ask Claude about its capabilities

Claude has built-in access to its documentation and can answer questions about its own features and limitations.

### Example questions

- `> can Claude Code create pull requests?`
- `> how does Claude Code handle permissions?`
- `> what slash commands are available?`
- `> how do I use MCP with Claude Code?`
- `> how do I configure Claude Code for Amazon Bedrock?`
- `> what are the limitations of Claude Code?`

**Note:** Claude provides documentation-based answers to these questions. For executable examples and hands-on demonstrations, refer to the specific workflow sections above.

**Tips:**
- Claude always has access to the latest Claude Code documentation, regardless of the version you're using
- Ask specific questions to get detailed answers
- Claude can explain complex features like MCP integration, enterprise configurations, and advanced workflows
