You are gathering evidence for a Vietnamese academic-style report about
the YOLOHome project. The report STRUCTURE is fixed (below). Your job is
NOT to write the report — your job is to investigate the codebase and
produce a structured evidence pack that the report author can paste from.

==================================================================
REPO ROOT: /Users/thienhao.nguyen/Documents/personal/YOLOHome
==================================================================

READ FIRST (do not re-derive what's already there):
- ARCHITECTURE.md — the existing comprehensive architecture report.
  Treat it as ground truth for components, channels, interfaces.
- README.md — repo-level quick start (Vietnamese)
- YOLOHome-Website/backend/API_DOCS.md — REST API docs
- YOLOHome-Gateway/README.md and YOLOHome-Gateway/docs/

==================================================================
REPORT STRUCTURE (the author will write each section from your pack)
==================================================================

1. MỞ ĐẦU
   1.1 Giới thiệu vấn đề (problem statement)
   1.2 Tổng quan hệ thống (one-paragraph system summary)
   1.3 Tổng quan báo cáo (what each section contains)

2. THIẾT KẾ HỆ THỐNG
   2.1 Tổng quan — system-wide diagram + flow + channels
   2.2 Chi tiết — five modules, see below

3. KẾT QUẢ
   3.1 Screenshots of the web app
   3.2 Demo video
   3.3 GitHub link

THE FIVE MODULES (each needs implementation status + evidence):

MODULE 1 — Sensor monitoring & display
  - Measure & display temperature, humidity, light in the home

MODULE 2 — Automation, alerts, mobile push
  - Auto-tune thresholds by day vs night
  - Detect violations of safe thresholds
  - Auto-control devices on violation (e.g. fan when hot, LED when dark)
  - Send status / emergency alerts to user's PHONE via a mobile app

MODULE 3 — UI to turn devices on/off

MODULE 4 — History + event logging
  - Store sensor and device history (the user notes: "Đã" = DONE)
  - Log events: app interactions, control signals, threshold-triggered
    state changes

MODULE 5 — Voice + smart suggestions
  - Voice control of devices
  - Auto curtain/window suggestions based on environment

==================================================================
DELIVERABLE: a single Markdown file at
/Users/thienhao.nguyen/Documents/personal/YOLOHome/REPORT_EVIDENCE.md
==================================================================

Structure REPORT_EVIDENCE.md exactly as below. Use Vietnamese for any
text that will be quoted verbatim in the final report (module names,
UI labels). Use English for your own analysis.

# REPORT_EVIDENCE.md

## §1 MỞ ĐẦU evidence
### 1.1 Problem statement — 3–5 bullet points explaining WHY a smart-home
    monitor & control system is needed. Pull from README.md and any
    motivational text in the docs/ folders. Do NOT invent rationale.
### 1.2 System summary — one paragraph (Vietnamese OK), citing
    ARCHITECTURE.md §1.
### 1.3 Report outline — one bullet per future section, derived from the
    structure above.

## §2.1 Tổng quan evidence
- Copy the Mermaid component diagram and the ASCII fallback from
  ARCHITECTURE.md §2 verbatim (they are reusable).
- Copy the three sequence diagrams (Flow A/B/C) from §4.7-4.8.
- One-paragraph narration of the bus: UI → REST → MQTT → Gateway →
  Serial → Kit, with file:line anchors.
- Communication-channel summary table: protocol, endpoints, payload,
  reference (extract from ARCHITECTURE.md §5).

## §2.2 Module-by-module evidence

For EVERY module below, produce this exact sub-structure:

  ### Module N — <name>
  - **Status:** ✅ Implemented / 🟡 Partial / ❌ Not implemented
  - **What the requirement asks for:** (1–2 sentences in Vietnamese)
  - **Where it is implemented (file:line):** bulleted list of every
    file involved, FE + BE + Gateway + config
  - **How it works (the flow):** 4–8 bullet points, each ending in a
    file:line citation
  - **UI surface:** which page/component the user sees (file:line) and
    what labels appear (in Vietnamese, exact strings from the code)
  - **Data persisted:** which MongoDB collections / config files
  - **Code snippet:** one ≤15-line excerpt that captures the essence,
    with file:line header
  - **Gaps vs requirement:** what the requirement asks for but the
    code does NOT do. Be honest — half the requirement points may not
    exist yet. Examples to verify carefully:
      * Module 2 "auto-tune thresholds by day/night" — does any code
        actually change thresholds based on time of day? Grep for
        time-based logic in alertService.js, controller.py,
        threshold_service.py. Likely NOT implemented — report so.
      * Module 2 "send to user's PHONE via app" — is there any push
        notification, SMS, FCM, OneSignal, Twilio, email-to-SMS code?
        Likely NOT implemented; the current alert UX is in-app
        polling on the web dashboard.
      * Module 5 "auto curtain/window suggestions" — there are
        curtain_model.pkl files at /models/ and YOLOHome-Gateway/
        Decision_tree/, but is the Decision Tree actually wired into
        the runtime path? Check AIService usage and config.yml
        automation.ai.enabled.
  - **Demo path:** the minimum steps to demonstrate this module
    working live (used by the screenshot/video section)

Modules to cover:
  Module 1 — Sensor monitoring & display
  Module 2 — Automation + threshold alerts + mobile push
  Module 3 — Device on/off UI
  Module 4 — History + event logging
  Module 5 — Voice + smart suggestions

## §3 Kết quả evidence
### Screenshots checklist
   List the web pages worth screenshotting. For each: the URL/route,
   the precondition (e.g. "after seeding sensor data"), and what
   element should be visible. Cover at minimum:
   - Login page (/)
   - Signup page (/signup)
   - Dashboard with 3 sensor cards (/dashboard)
   - Dashboard with an active alert + the "Xác nhận" button
   - Device management page with toggles (/devices)
   - Voice control button in recording state
   Do NOT take screenshots yourself — just enumerate what to capture.

### Demo video script
   A 2–3 minute scene list:
   1. Open dashboard, point at live values.
   2. Toggle a device, show MQTT log + the relay reacting.
   3. Force a threshold violation, show the alert appearing and being
      resolved.
   4. Use voice command, show transcript toast and device reacting.
   For each scene: which terminal/window to show, what to say (in VN),
   and which file:line backs that behaviour.

### GitHub link
   Run `git remote -v` and `git log --oneline -5`. Report the remote
   URL and the 5 most recent commits.

==================================================================
RULES FOR THE INVESTIGATION
==================================================================
- Cite file:line for EVERY factual claim. No claim without an anchor.
- When the requirement is partially or not implemented, say so plainly
  in the "Gaps" bullet. The author needs honest status to write
  truthful "Module 2: not yet implemented" sections if necessary.
- Do NOT write new code or modify any source file. The only file you
  may write is REPORT_EVIDENCE.md.
- Do NOT take screenshots or record videos — only PLAN them.
- Vietnamese is the report language. Quote UI strings exactly as they
  appear in the source (e.g. "Xác nhận", "Cảnh báo ngưỡng", "Nhiệt
  độ", "Độ ẩm", "Cường độ ánh sáng").
- Keep snippets ≤15 lines each, always with a file:line header above.
- Length target for REPORT_EVIDENCE.md: dense but scannable, roughly
  600–900 lines. Tables > prose where possible.
- At the END of the file, add a "Verification checklist" section: 10
  spot-check items the report author should re-confirm before
  submitting (e.g. "verify Module 2 day/night logic does not exist,
  by grep -rn 'sunset\\|sunrise\\|hour\\|isDay' YOLOHome-*").

==================================================================
DELIVERABLE FORMAT REMINDER
==================================================================
Output: REPORT_EVIDENCE.md only. No commentary in chat beyond a
one-line "done, see REPORT_EVIDENCE.md".
