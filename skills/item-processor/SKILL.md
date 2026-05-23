# Item Processor Skill

## Purpose

Process items from the Needs_Action folder and generate Plans with reasoning. This skill enables Claude to act as an AI Employee that analyzes incoming items (emails, files) and takes appropriate action.

## Working Directory

This skill operates on the vault at: `/mnt/d/AI_EMPLOYEE_VAULT`

## Instructions

### 1. Read and Analyze Items

For each item in `/Needs_Action/`:

1. Read the item file content
2. Extract the frontmatter metadata (type, from, subject, etc.)
3. Read `/Company_Handbook.md` for processing rules

### 2. Determine Priority and Actions

Based on Company_Handbook.md rules:

- **High Priority:** Contains "urgent", "asap", "important", or marked important
- **Normal Priority:** Standard communications
- **Low Priority:** Newsletters, promotions, automated notifications

Determine required actions:
- Does this need a reply?
- Should it be forwarded?
- Is it informational only?

### 3. Create Plan File

Create a Plan file in `/Plans/` using this format:

```markdown
---
plan_id: PLAN_[unique_id]
source_item: /Needs_Action/[filename]
created_at: [ISO timestamp]
status: pending|completed|requires_approval
action_required: true|false
action_type: email|file_operation|none
---

# Plan: [Brief description]

## Context

- **Source:** [Email/File drop/etc.]
- **From:** [Sender/Origin]
- **Received:** [Timestamp]
- **Priority:** [High/Normal/Low]

## Analysis

[Your analysis of the item based on Company_Handbook.md rules]

## Reasoning

[Why you decided on the proposed actions]

## Proposed Actions

- [x] Read and analyze content
- [x] Classify priority level
- [ ] [Pending action 1]
- [ ] [Pending action 2]

## Approval Required

[If action_required: true]
- **Action Type:** [email/other]
- **Details:** [Brief description]
- **Approval File:** /Pending_Approval/[filename].md
```

### 4. Create Approval Request (If Needed)

If an email needs to be sent, create an approval request in `/Pending_Approval/`:

```markdown
---
approval_id: APPROVAL_[unique_id]
plan_ref: PLAN_[id]
action_type: email_reply
status: pending
created_at: [ISO timestamp]
to: [recipient email]
subject: "[email subject]"
gmail_reply_to_id: [original gmail message id if replying]
---

# Approval Request: Reply to [Sender Name]

## Action Requested

[One sentence describing what the reply does]

## Recipient

**To:** [recipient email]
**Subject:** [email subject]

## Draft Reply

---

[Full email body here — start directly with the greeting, no To/Subject headers]

---

## Approval Instructions

- Move this file to `/Approved/` to send the reply
- Move this file to `/Rejected/` to discard without sending

## References

- Plan: /Plans/PLAN_[id].md
- Source: /Needs_Action/[source_file].md
```

**Important notes on the format:**
- Always quote the `subject` value in frontmatter (e.g. `subject: "Re: Something"`) to avoid YAML parse errors when the subject contains colons
- Place the email body between `---` dividers under `## Draft Reply`
- Do NOT repeat `**To:**` / `**Subject:**` headers inside the `---` body block — those are already in the frontmatter

### 5. Update Dashboard

Update `/Dashboard.md` with:
- Increment items processed count
- Add entry to Today's Activity table
- Update "Last updated" timestamp

### 6. Mark Item as Processed

Update the item's frontmatter from `status: pending` to `status: processed`.

## Rules from Company_Handbook.md

Always consult Company_Handbook.md for:
- Email response guidelines
- Priority definitions
- When to draft replies vs. ignore
- Processing rules for different item types

## Output Quality

- Be concise but thorough in reasoning
- Always explain WHY you're taking an action
- Flag uncertainties for human review
- Use professional tone in draft emails
- Never send emails without creating approval requests

## Important Notes

- ALL email sends require human approval
- Create clear, actionable Plans
- Log your reasoning for auditability
- If uncertain, default to requiring human review
