# AI Coding Guidance for `vaccheria-reservations`

This repo is a **tiny Streamlit single-page application** used to collect table reservations for "Antica Vaccheria" and forward them via email (originally through an n8n flow).

Keep the following in mind when working with or extending the code:

## 📁 Project Structure

- `app.py` – the *only* Python source file.  All logic (UI, state, email sending, CSS tweaks) lives here.
- `requirements.txt` – lists `streamlit` and `requests` (the latter currently unused but left from when n8n webhooks were considered).
- `assets/` – contains two images (`logo.png`, `favicon.png`) referenced by `st.set_page_config` and custom markup.  The app falls back to plain text if the logo file is missing.
- No tests, build system, or additional modules.  New features should either stay in `app.py` or be factored into new modules and imported.

## 🎯 Architecture & Flow

1. **Streamlit session state** controls a three‑step wizard (`step` 1–3).  Each step updates the same global dictionary in `st.session_state`.
2. **Custom CSS** is injected via `st.markdown` at the top.  Most styling targets Streamlit data-testid attributes (`stPills`, `stDateInput`, etc.) to enlarge controls for mobile.
3. **Reservation logic**: collect guests, date/time, personal info, then show a summary.  Selecting `9+` guests short‑circuits the form and shows a contact message.
4. **Confirmation** calls `send_email_reservation()` which uses Gmail SMTP.  The comment `# python func instead than n8n` hints that the original design used an n8n webhook; if re‑introducing n8n, replace or augment this function.
5. After successful send, the code clears relevant session keys, resets `step` to 1, and triggers a custom `st.dialog` popup.

## 🛠 Developer Workflows

- **Install & run locally**:
  ```bash
  pip install -r requirements.txt
  streamlit run app.py
  ```
- **Secrets**: the Gmail password is read from `st.secrets["EMAIL_PASSWORD"]`.  When developing locally create a `secrets.toml` with:
  ```toml
  EMAIL_PASSWORD = "<app‑password or smtp password>"
  ```
  Do **not** commit real credentials; GitHub/Streamlit Cloud use their own secret stores.
- **Deployment**: simply push to a GitHub repo and point Streamlit Cloud (or another host) at it.  Ensure the `EMAIL_PASSWORD` secret is configured there.
- **Assets**: swap logos by overwriting `assets/logo.png` or add an SVG and adjust the fallback text in `app.py`.

## 🧩 Conventions & Patterns

- UI text and comments are in **Italian**.  Variables are mostly English but match context (`dati`, `guests`, `notes`).  Preserve the language when editing text strings.
- Use `st.pills` for choice lists instead of selectboxes – it's the project's idiom (see guest count and hours pickers).
- The progress bar is a simple `st.progress(step / 3)`; steps are hardcoded at 3.  Add new steps by adjusting this and the `if/elif` chain.
- Session state keys are deleted manually when resetting; remember to remove any new keys if you expand state.
- The email subject line and body are constructed with Italian headings.

## 🔗 Integration Points

- **SMTP**: `send_email_reservation()` is the only external integration.  It uses `smtplib` with hard‑coded `smtp.gmail.com:587`.  To switch to another provider, update this helper.
- **n8n (optional)**: the repository README mentions an n8n flow.  If you re‑enable it, you’ll likely replace the direct SMTP call with a `requests.post()` to a webhook.

## ✅ Tips for AI Agents

- When modifying `app.py`, keep the multi‑step logic linear – don’t introduce unrelated branches that require resetting state differently.
- Use existing CSS selectors when styling new widgets; the file already contains examples of targeting pills, inputs, and labels.
- If adding new assets, document their usage in comments near the `logo_path` logic.
- When adding configuration options, prefer `st.secrets` and avoid hard‑coding sensitive data.
- Preserve the Italian language for UI strings; translation is not in scope unless the user explicitly requests.
- There are no tests; if you add any, place them in a new `tests/` directory and update `requirements.txt` accordingly.

---

Feel free to ask for clarification or suggest additional sections if anything is unclear or missing.