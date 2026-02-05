# Ralph Wiggum Task Processor

## Purpose

Process multi-step tasks autonomously until completion using the Ralph Wiggum loop pattern.

## When to Use

Use this skill when:
- A task requires multiple steps to complete
- You need to persist progress across Claude invocations
- The task may require waiting for approvals between steps
- You want to track iteration history for debugging

## Instructions

### Reading a Task

1. Check for task file in `/Tasks/` folder
2. Read the frontmatter for:
   - `task_id`: Unique identifier
   - `status`: Current status (pending, in_progress, blocked, completed)
   - `current_iteration`: How many times we've worked on this
   - `max_iterations`: Maximum allowed iterations
3. Read the body for:
   - **Objective**: What we're trying to accomplish
   - **Steps Required**: Checklist of steps (some may be done)
   - **Completion Criteria**: How to know when we're done
   - **Iteration Log**: History of previous iterations

### Processing a Task

1. **Check if task can continue**
   - If `current_iteration >= max_iterations`: Stop, mark as max_iterations_reached
   - If task file is in `/Done/`: Stop, task is complete
   - If status is completed/failed: Stop

2. **Execute next step**
   - Find first unchecked step in "Steps Required"
   - Perform the action
   - Mark step as done: `- [x] Step description`

3. **Update iteration log**
   Add new row to the iteration table:
   ```markdown
   | 2 | 14:35:22 | Created invoice | Success |
   ```

4. **Check completion**
   - All steps done? → Move file to `/Done/`
   - Blocked by approval? → Create approval request, update status to `blocked`
   - Error? → Log error, decide if recoverable

5. **Save changes**
   - Update frontmatter with new `current_iteration` and `status`
   - Update body with step checkboxes and iteration log

### Example Task Processing

```
Iteration 1:
- Read task: "Generate and send invoice to Client A"
- Step 1: Lookup client in Odoo → Done
- Log: "Looked up client" / "Found: Client A (id: 7)"
- Save and continue

Iteration 2:
- Read task again
- Step 2: Calculate invoice amount → Done
- Log: "Calculated amount" / "$500.00 for January services"
- Save and continue

Iteration 3:
- Read task again
- Step 3: Create invoice in Odoo → Done
- Log: "Created invoice" / "INV/2026/00002"
- Save and continue

Iteration 4:
- Read task again
- Step 4: Draft approval email → Done
- Created: /Pending_Approval/EMAIL_xxx.md
- Log: "Created approval request" / "Waiting for human"
- Status: blocked
- Save and wait

(Human approves, executor sends email)

Iteration 5:
- Read task again
- All steps complete!
- Move task file to /Done/
- Log: "Task complete" / "All steps done"
```

## Task State File Format

```markdown
---
task_id: task_a1b2c3d4
created_at: 2026-02-05T10:30:00Z
status: in_progress
max_iterations: 10
current_iteration: 2
completion_strategy: file_movement
---

# Task: [Objective Description]

## Objective

[Full description of what needs to be accomplished]

## Steps Required

- [x] Step 1 that's already done
- [ ] Step 2 that's pending
- [ ] Step 3 that's pending

## Completion Criteria

Task file moved to /Done/ when:
- All steps complete
- OR explicit completion signal

## Iteration Log

| # | Timestamp | Action | Result |
|---|-----------|--------|--------|
| 1 | 10:30:00 | Started task | In progress |
| 2 | 10:31:15 | Completed step 1 | Success |

---
*Managed by Ralph Wiggum Loop*
```

## Completion Strategies

### File Movement (Default)
- Task is complete when file is moved to `/Done/`
- Most reliable, works with Obsidian workflow

### Promise-Based
- Task is complete when Claude outputs `<promise>TASK_COMPLETE</promise>`
- Simpler but requires Claude to remember

## Error Handling

- **Recoverable errors**: Log and continue to next iteration
- **Blocking errors**: Set status to `blocked`, create error report
- **Fatal errors**: Set status to `failed`, move to `/Done/` with error note

## Tips

- Keep iteration actions short and descriptive
- Update the task file after each meaningful action
- If waiting for approval, set status to `blocked`
- Check `max_iterations` before starting expensive operations
- When in doubt, save progress and let the loop continue
