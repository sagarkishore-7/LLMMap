# Screenshot Capture Guide

Capture these screenshots from the live deployment at
https://llm-map-mu.vercel.app for use in the README and docs.

Save each as a PNG in this directory (`docs/assets/`).

## Required Screenshots

### 1. `01-landing.png`
- **Page:** Landing page (no scenario selected)
- **Show:** Hero text, feature cards, scenario list
- **Viewport:** 1280x800 desktop
- **Crop:** Full page above the fold

### 2. `02-scenario-select.png`
- **Page:** Landing page, scenarios section
- **Show:** Both scenario cards (Support Bot + Knowledge Assistant)
- **Crop:** Just the scenarios section

### 3. `03-vulnerable-result.png`
- **Page:** Lab view after running a simulation
- **Show:** Attack Configuration, Vulnerable mode active, chat trace with injection payload highlighted in red, verdict card showing "Attack Succeeded"
- **Scenario:** Support Bot
- **Technique:** Rule Addition Prompting
- **Crop:** Left column (chat + verdict)

### 4. `04-defended-result.png`
- **Page:** Same simulation, toggle to Defended mode
- **Show:** Defended mode active, chat trace showing refusal, verdict card showing "Attack Blocked"
- **Crop:** Left column (chat + verdict)

### 5. `05-explanation-panel.png`
- **Page:** Lab view right column
- **Show:** Attack Explanation panel with OWASP tag, "Why This Attack Works", "Mitigation Guidance" sections, plus the Comparison card
- **Crop:** Right column only

### 6. `06-recent-runs.png` (optional)
- **Page:** Lab view after 3+ simulations
- **Show:** Recent Runs panel with multiple entries, verdict dots
- **Crop:** Just the Recent Runs card

## Tips

- Use browser DevTools device toolbar for consistent 1280x800 viewport
- Dark mode is default — no need to change theme
- Use macOS Screenshot (Cmd+Shift+4) or browser extension for clean crops
- Optimize PNGs with `pngquant` or similar before committing

## Optional GIF

A ~10s GIF showing the full flow:
1. Click "Support Bot" scenario
2. Select "Rule Addition Prompting"
3. Click "Run Simulation"
4. Toggle Vulnerable → Defended
5. Scroll explanation panel

Tool: Use [Kap](https://getkap.co/) or screen recording → ffmpeg conversion.
