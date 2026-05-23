---
approval_id: {{approval_id}}
plan_ref: {{plan_ref}}
action_type: email_reply
status: pending
created_at: {{created_at}}
to: {{to}}
subject: "{{subject}}"
gmail_reply_to_id: {{gmail_reply_to_id}}
---

# Approval Request: Reply to {{sender_name}}

## Action Requested

{{action_description}}

## Recipient

**To:** {{to}}
**Subject:** {{subject}}

## Draft Reply

---

{{body}}

---

## Approval Instructions

- Move this file to `/Approved/` to send the reply
- Move this file to `/Rejected/` to discard without sending

## References

- Plan: /Plans/{{plan_ref}}.md
- Source: /Needs_Action/{{source_file}}
