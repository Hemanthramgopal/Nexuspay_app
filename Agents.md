# NexusPay: AI Agent Master Instructions

You are an expert backend engineer executing a strict Spec-Driven Development protocol. 
Before executing any prompt, you MUST read and abide by the rules defined in the `context/` directory. 

## Context Index
Do not make assumptions. Always reference these files for project rules:
- **What we are building:** Read `context/project-overview.md`
- **Tech stack & folder structure:** Read `context/architecture.md`
- **Python typing & linting rules:** Read `context/code-standards.md`
- **How you must behave:** Read `context/ai-workflow-rules.md`
- **Current status:** Read `context/progress-tracker.md`

## Current Execution Phase
We are currently executing the build plan located at `context/specs/00-build-plan.md`. 
When the user asks you to execute a unit (e.g., "Execute Unit 01"), find the corresponding spec file in `context/specs/` and implement it strictly according to the rules above.