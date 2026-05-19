# Tools

One-off utilities and Cursor agent invocation helpers. **Primary interface is the unified CLI** — see `AGENTS.md` in project root.

## Cursor Agent (Headless)

- `cursor_agent_clean.ps1` — Run Cursor agent to orchestrate watermark removal (Windows)
- `cursor_agent_clean.sh` — Same for macOS/Linux

**Requirements:** Cursor Pro, `agent` CLI installed, `CURSOR_API_KEY` set or `agent auth` run once.

```powershell
# Windows
.\src\tools\cursor_agent_clean.ps1 -Image assets/dirty/photo.jpg
```

```bash
# macOS/Linux
./stega/tools/cursor_agent_clean.sh assets/dirty/photo.jpg
```

## One-off Python Scripts

Run from project root: `python -m stega.tools.<script_name>`

| Script | Purpose |
|--------|---------|
| `migrate_assets` | Move assets from legacy layout to unified layout |
| `consolidate_assets_final` | Full asset consolidation (merge + remove legacy dirs) |
| `migrate_to_unified_layout` | Migrate to dirty/processing/clean layout |
| `reorganize_src` | Reorganize src/ directory structure |
| `clean_glass_image` | Clean glass-d2h.png with multiple LSB methods |
| `analyze_watermark` | LSB/watermark pattern analysis |
| `battle_visualization` | Steganography battle simulation |
| `simple_text_remover` | Text watermark removal (no OCR) |
