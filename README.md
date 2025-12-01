## GreenGuard AI / GreenGuard AI – Local Sustainability Assistant

GreenGuard AI (in the `GreenGuard AI` folder) is a local-first sustainability assistant built with **Streamlit**.  
It bundles:

- **GreenGuard Home**: a simple dashboard with eco tips and an integrated chat assistant powered by **Ollama**.
- **🟢 Carbon Quick Check**: a short questionnaire that highlights your biggest emission sources and suggests 3 high‑impact actions.
- **♻ Waste Scanner**: upload a photo of an item to get guidance on whether it’s recyclable, needs rinsing, or should go to general waste (using lightweight image heuristics, not a heavy CV model).

---

## 1. Prerequisites

- **Python**: 3.9 or newer (3.10+ recommended).
- **pip**: Python package manager.
- **Ollama** (optional but recommended, for the GreenGuard chat assistant):
  - Install Ollama from their website.
  - Make sure the `ollama` service is running on your machine.
  - Pull the configured model (as per `appjson.json`):

    ```bash
    ollama pull phi3:mini
    ```

If Ollama is not installed or not running, the main app will still start, but the chat assistant will show a message saying that Ollama is unavailable.

---

## 2. Python dependencies

From the project root (`GreenGuard AI`), install the required Python libraries:

```bash
pip install streamlit pandas pillow numpy
```

If you prefer a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate   # On Windows (PowerShell / CMD)
# source .venv/bin/activate  # On macOS / Linux

pip install streamlit pandas pillow numpy
```

---

## 3. Project structure (key files)

- `app.py` – main Streamlit entrypoint; orchestrates navigation, daily tips, sidebar chat, and links to the tools.
- `carbon_check.py` – implements the **Carbon Quick Check** questionnaire and results page.
- `waste_scanner.py` – implements the **Waste Scanner** image upload and heuristic analysis.
- `appjson.json` – configuration for:
  - Page title, icon, layout.
  - Global CSS styles.
  - Text content, tool descriptions, daily tips.
  - Ollama model name (`phi3:mini`) and system prompt.
  - Sidebar AI chat labels.
- `.streamlit/config.toml` – Streamlit theme (light theme and basic theming).

---

## 4. How to run the main app

1. **Open a terminal** and go to the project directory:

   ```bash
   cd "C:\Users\Omar Tarek\OneDrive\Desktop\GreenGuard AI"
   ```

2. (Optional) **Activate your virtual environment** if you created one.

3. **Start Streamlit** with the main app:

   ```bash
   streamlit run app.py
   ```

4. Your browser should open automatically at a URL like `http://localhost:8501`.  
   There you’ll see:
   - The GreenGuard AI home screen with:
     - App title and subtitle.
     - Feature cards for **Carbon Quick Check** and **Waste Scanner**.
     - A rotating **daily eco tip**.
     - The sidebar **GreenGuard AI** chat (if Ollama is available).

5. Use the buttons on the main page to:
   - Open **Carbon Quick Check** (answer questions, view impact bars and actions).
   - Open **Waste Scanner** (upload item photos and see recycling guidance).

---

## 5. Running tools individually (optional)

Although they are designed to be launched via `app.py`, you can run each tool as a standalone Streamlit app if desired:

- **Carbon Quick Check only**:

  ```bash
  streamlit run carbon_check.py
  ```

- **Waste Scanner only**:

  ```bash
  streamlit run waste_scanner.py
  ```

These open a minimal view focused solely on the chosen tool.

---

## 6. Configuration & customization

- **UI & text**: Edit `appjson.json` to change:
  - App title, subtitle, and footer note.
  - Tool titles, descriptions, and button labels.
  - Daily tips list under `"tips"`.
  - Sidebar AI labels and “thinking” message.
- **Styling**:
  - The `"style"` → `"StyleCss"` field in `appjson.json` contains embedded CSS for the landing page cards, chat bubbles, and sidebar.
  - `.streamlit/config.toml` holds the Streamlit theme base (`light`).
- **Ollama model & prompt**:
  - Change `"OllamaModel"` and `"OllamaPrompt"` under the `"ollama"` section in `appjson.json` if you want a different local model or behavior.

After editing `appjson.json`, just refresh the Streamlit page in your browser (or stop and rerun `streamlit run app.py`) to apply changes.

---

## 7. Troubleshooting

- **Streamlit command not found**  
  Make sure your Python `Scripts` folder is on the PATH, or call it via:

  ```bash
  python -m streamlit run app.py
  ```

- **Ollama-related message in chat**  
  If the sidebar chat says Ollama is not available:
  - Confirm that Ollama is installed and running.
  - Pull the `phi3:mini` model using `ollama pull phi3:mini`.
  - Restart the app with `streamlit run app.py`.

- **Blank or broken UI after editing config**  
  Ensure `appjson.json` remains valid JSON (no trailing commas, matching quotes/braces).  
  If unsure, revert your changes or validate the JSON using an online JSON validator, then restart the app.


