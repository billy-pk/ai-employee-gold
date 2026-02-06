# Social Poster Skill

## Purpose

Draft and schedule tweets for @IrshadBilal with human approval workflow.

## When to Use

Use this skill when:
- Drafting tweets about business updates, achievements, or announcements
- Scheduling tweets for optimal posting times
- Responding to mentions or engaging with the community
- Creating tweet threads on specific topics

## Instructions

### Drafting a Tweet

1. **Check character limit**: Tweets must be 280 characters or less
2. **Draft content** that is:
   - Professional but personable
   - Relevant to the account's audience
   - Free of typos and grammatical errors
3. **Create approval request**: Generate `Pending_Approval/TWEET_[id].md`
4. **Wait for human approval** before posting

### Tweet Approval Workflow

```
1. Claude drafts tweet content
2. Create approval file in Pending_Approval/
3. Human reviews:
   - Move to Approved/ to approve
   - Move to Done/ to reject
4. If approved, Claude posts via Twitter MCP
5. Log to Social/Twitter/posted.md
```

### Scheduling Tweets

1. Determine optimal posting time (consider timezone, audience activity)
2. Use `schedule_tweet(content, scheduled_time)` from Twitter MCP
3. Scheduled tweets still require approval before actual posting
4. Check `Social/Twitter/scheduled_posts.md` for current schedule

### Best Practices

- **Voice**: Professional, insightful, occasionally witty
- **Topics**: Business insights, tech trends, professional updates
- **Frequency**: 1-3 tweets per day maximum
- **Engagement**: Reply to relevant mentions within 24 hours
- **Hashtags**: Use sparingly (1-2 per tweet max)
- **Links**: Include when sharing valuable content

### Example Tweet Formats

**Business Update:**
```
Excited to share: [achievement].

This means [benefit for followers].

#relevanthashtag
```

**Insight:**
```
Observation from working on [topic]:

[Key insight in 1-2 sentences]

What's your experience?
```

**Thread Starter:**
```
Thread: [Topic]

Here's what I've learned about [subject]:

1/n
```

## Approval Request Template

When creating a tweet approval, the file should contain:

```markdown
---
type: tweet_approval
tweet_id: TWEET_abc123
status: pending
created_at: 2026-02-05T10:30:00Z
character_count: 142
---

# Tweet Approval Request

## Content

[The actual tweet text here]

## Details

- **Characters**: 142/280
- **Created**: 2026-02-05 10:30
- **Post immediately upon approval**

## Instructions

To approve this tweet:
1. Review the content above
2. Move this file to `Approved/` folder

To reject:
1. Move this file to `Done/` folder
```

## Engagement Tracking

After posting, engagement metrics are tracked in:
- `Social/Twitter/engagement.md` - Overall account metrics
- `Social/Twitter/posted.md` - Log of all posted tweets

Review engagement weekly to optimize content strategy.

## Tips

- Draft multiple tweet options for important announcements
- Consider time zones when scheduling
- Avoid posting during off-hours unless time-sensitive
- Always proofread before creating approval request
- Include a call-to-action when appropriate
- Engage authentically - avoid overly promotional content

---
*Managed by Twitter MCP*
