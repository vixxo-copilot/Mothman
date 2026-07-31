# Outlook email signature (Graph sends)

Graph does not auto-insert Outlook signatures. All Graph sends use the
**compact Reply** signature.

## Canonical file

`reply.compact.html` — mirrors Outlook `Reply (Crystal.Gagner@vixxo.com)`
colors and content, with tightened line spacing (no Word blank paragraphs).

| Element | Style |
| --- | --- |
| Name | Arial 10pt bold `#8E992D` |
| Title / company | Arial 10pt `#3E4442` / `#3E4543` |
| Help Center link | `#37797B` |

## Load for send

```bash
python .cursor/bin/outlook_signature.py --json
```

Preview: open `reply.preview.html` in a browser.

## Refresh raw Outlook copies (optional)

```bash
python .cursor/bin/outlook_signature.py --sync
```

Raw Word HTML is kept under `reply.htm` for reference only; Graph sends
use `reply.compact.html`.
