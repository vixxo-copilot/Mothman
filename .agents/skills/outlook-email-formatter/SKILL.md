---
name: outlook-email-formatter
description: >-
  Renders email or Teams message drafts as a clean HTML file and opens it in the
  browser so the user can copy-paste into Outlook or Teams without dark-background
  artifacts or lost hyperlinks. Use when the user asks to write, draft, or compose
  an email or Teams message, or when the user needs to copy formatted text with links
  into Outlook or Teams.
---

# Outlook Email Formatter

## Why this exists

Copying rich text from Cursor's dark-themed chat into Outlook carries the dark
background color. Pasting as plain text strips hyperlinks. This skill renders the
message as a standalone HTML page with a white background and Outlook-friendly
styling, then opens it in the browser so Cmd+A / Cmd+C / Cmd+V into Outlook works
cleanly.

## When to use

Automatically apply this skill whenever you draft an email or Teams message for
the user. Don't wait to be asked -- just produce the HTML file as part of the
drafting step.

## Workflow

1. **Draft the message** in the conversation (markdown) so the user can review it.
2. **Convert to HTML** using the template below.
3. **Write** the HTML to a temp file: `{workspace}/tmp-email.html`
4. **Open** it in the default browser: `open {workspace}/tmp-email.html`
5. Tell the user: "Opened in your browser. Select all, copy, and paste into Outlook."
6. When the user confirms they're done (or moves on), **delete** `tmp-email.html`.

## HTML template

```html
<!DOCTYPE html>
<html><body style="font-family: Calibri, Arial, sans-serif; font-size: 11pt; color: #000; background: #fff; max-width: 800px; margin: 0 auto; padding: 20px;">

<!-- message content here -->

</body></html>
```

### Conversion rules

| Markdown | HTML |
|----------|------|
| `**bold**` | `<b>` |
| `[text](url)` | `<a href="url">text</a>` |
| `- item` | `<ul><li>` |
| `1. item` | `<ol><li>` |
| Blank line | `<p>` break |
| `# Heading` | `<b style="font-size: 14pt">` (avoid actual heading tags -- Outlook mangles them) |

### Styling constraints

- Font: Calibri 11pt (Outlook default -- blends with the user's other emails)
- Background: `#fff` always
- Link color: leave as browser default blue
- No CSS classes, no external stylesheets, no `<style>` blocks (Outlook strips them)
- All styling inline
- No emojis unless the user explicitly included them

## Cleanup

Always delete `tmp-email.html` when:
- The user says they're done, confirms it worked, or moves to a different topic
- The user explicitly asks to clean up
