# Snag Shelf

**Everything that snagged — one shelf.**

A Hermes Desktop plugin: cross-session gallery of **failed tool calls** (tool
name, redacted args, error snippet). Pin keepers, insert a fix prompt into the
composer. Not “last failure only” — a lasting snag shelf.

Repo: https://github.com/aydnOktay/hermes-snag-shelf

POWERED BY HERMES AGENT · COMMUNITY PLUGIN · v0.1.0

Disclosure — stores **local failure metadata** under `$HERMES_HOME/plugin-data/snag-shelf/`.
Args with password/token/key-like names are redacted. No network. No API keys.

## What you get

| | |
| --- | --- |
| **Full page** Sidebar **Snag Shelf** at `/snag-shelf`. | **Status chip** `snags N`. |
| **Live capture** `post_tool_call` on failures / blocks / timeouts. | **Insert fix prompt** via `host.composer.insertText`. |
| **Filters** all · terminal · file · web · other | **Slash** `/snag` |

## Install

Requires Hermes **>= 0.21.5** (Desktop SDK `host.composer.insertText`).

```powershell
hermes plugins install https://github.com/aydnOktay/hermes-snag-shelf.git
hermes plugins enable snag-shelf
```

Copy the Desktop package (Hermes 0.21 may skip it):

```powershell
New-Item -ItemType Directory -Force -Path "$env:LOCALAPPDATA\hermes\desktop-plugins\snag-shelf" | Out-Null
Copy-Item "$env:LOCALAPPDATA\hermes\plugins\snag-shelf\desktop\plugin.js" "$env:LOCALAPPDATA\hermes\desktop-plugins\snag-shelf\plugin.js" -Force
```

Restart Hermes. Open **Snag Shelf** in the sidebar.

## Use

1. Let a tool fail (bad path, blocked command, timeout, …).
2. Snag appears on Snag Shelf + chip count.
3. **Insert fix prompt** / **Insert error** / **Pin**.

```
/snag
/snag terminal
/snag clear
```

Tools: `snag_shelf_list`, `snag_shelf_clear`.

## vs debug-desk / command-tray

| | debug-desk | command-tray | Snag Shelf |
| --- | --- | --- | --- |
| Scope | Last terminal fail + git | Session terminal cmds | Cross-session **all** tool fails |
| Surface | Pane | Tray | Full page product |
| Job | Today’s desk | Quick command list | Lasting “what broke” gallery |

## License

MIT
