# -*- coding: utf-8 -*-
"""
MARACAS Pro v4.0 — Integrated Digital Heritage Management

Changes in v4:
- DYNAMIC Element ID Fetching (No more hardcoded IDs).
- Configurable Base URL (Works on any Omeka install).
- File Upload Support (via 'file_urls' JSON property).
- Improved CSV reading and error handling.
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os, json, time, threading, queue, re, csv, sys
from pathlib import Path
from urllib.parse import urljoin
import html as html_mod

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import pandas as pd

try:
    import keyring
except ImportError:
    keyring = None

class MaracasProV4:
    # ---------------------------- Init ----------------------------
    def __init__(self, root):
        self.root = root
        self.root.title("MARACAS Pro v4.0 — Generic Omeka Batch Uploader")
        self.root.geometry("1420x950")

        # State
        self._log_q = queue.Queue()
        self.cancel_requested = False
        self.input_csv_file = None
        self.csv_format = None
        self.stats = {"upload_success": 0, "upload_failed": 0}

        # Config/state variables
        self.setup_configuration()

        # HTTP session
        self.session = self.create_session()

        # UI
        self.create_interface()
        self.apply_styles()
        self.load_settings()
        self.load_saved_key()

        # Start log pump
        self.root.after(60, self._drain_log_queue)
        self.enqueue_log("✅ Ready. Please configure API URL and Key in the Setup tab.")

    # ---------------------------- Configuration ----------------------------
    def setup_configuration(self):
        # Keys & toggles
        self.omeka_api_url = tk.StringVar(value="https://yoursite.com/api/")
        self.omeka_api_key = tk.StringVar(value="")
        self.remember_key = tk.BooleanVar(value=True)
        self.render_html_values = tk.BooleanVar(value=True)
        self.items_public = tk.BooleanVar(value=True)
        self.dry_run = tk.BooleanVar(value=False)

        # Paths
        self.output_dir = str(Path.home() / "Downloads")
        self.output_dir_var = tk.StringVar(value=self.output_dir)

        # Upload options
        self.upload_limit = tk.IntVar(value=0)
        self.req_delay_ms = tk.IntVar(value=100)
        self.csv_delimiter = tk.StringVar(value="Auto")
        
        # Language preference for strict CSVs
        self.target_lang_pref = tk.StringVar(value="english") # 'spanish' or 'english'

        # DC element IDs - Initially empty, fetched dynamically
        self.dc_elements = {} 
        # Fallback default map (Standard Omeka Classic) - only used if fetch fails
        self.default_dc_map = {
            "Identifier": 43, "Title": 50, "Creator": 39, "Contributor": 37,
            "Subject": 49, "Type": 51, "Description": 41, "Date": 40,
            "Language": 44, "Format": 42, "Rights": 47, "Publisher": 45,
            "Relation": 46, "Source": 48, "Coverage": 38
        }

    def create_session(self):
        s = requests.Session()
        retry_strategy = Retry(
            total=3, backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        s.mount("http://", adapter); s.mount("https://", adapter)
        s.headers.update({"User-Agent": "MARACAS-Pro/4.0", "Accept": "application/json"})
        return s

    # ---------------------------- UI ----------------------------
    def create_interface(self):
        self.create_header()
        self.create_tabs()
        self.create_status_bar()

    def create_header(self):
        header = tk.Frame(self.root, bg="#1a365d", height=84); header.pack(fill=tk.X); header.pack_propagate(False)
        left = tk.Frame(header, bg="#1a365d"); left.pack(side="left", padx=20, pady=10)
        tk.Label(left, text="MARACAS Pro v4.0", font=("Arial", 20, "bold"), bg="#1a365d", fg="white").pack(anchor="w")
        tk.Label(left, text="Universal Omeka Bulk Uploader", font=("Arial", 11), bg="#1a365d", fg="#cbd5e0").pack(anchor="w")
        right = tk.Frame(header, bg="#1a365d"); right.pack(side="right", padx=20, pady=10)
        self.omeka_status = tk.Label(right, text="API Status: ●", font=("Arial", 10, "bold"), bg="#1a365d", fg="#ef4444")
        self.omeka_status.pack(anchor="e")

    def create_tabs(self):
        main = tk.Frame(self.root, bg="#f8fafc"); main.pack(fill=tk.BOTH, expand=True, padx=16, pady=16)
        self.notebook = ttk.Notebook(main); self.notebook.pack(fill=tk.BOTH, expand=True)
        self.create_setup_tab()
        self.create_upload_tab()
        self.create_about_tab()

    def create_status_bar(self):
        self.status_bar = tk.Frame(self.root, bg="#e2e8f0", height=30); self.status_bar.pack(fill=tk.X, side="bottom")
        self.status_bar.pack_propagate(False)
        self.status_label = tk.Label(self.status_bar, text="", bg="#e2e8f0", fg="#4a5568", font=("Arial", 9))
        self.status_label.pack(side="left", padx=10)

    def apply_styles(self):
        style = ttk.Style()
        try: style.theme_use("clam")
        except Exception: pass
        style.configure("TNotebook.Tab", background="#e2e8f0", foreground="#2d3748", padding=[16, 8], font=("Arial", 10, "bold"))
        style.map("TNotebook.Tab", background=[("selected", "#4299e1"), ("active", "#bee3f8")], foreground=[("selected", "white"), ("active", "#2b6cb0")])
        style.configure("TProgressbar", background="#4299e1", troughcolor="#e2e8f0", borderwidth=1)

    # ---------------------------- Tabs ----------------------------
    def create_setup_tab(self):
        tab = tk.Frame(self.notebook, bg="#f8fafc"); self.notebook.add(tab, text="⚙️ Setup")

        # API Config
        group = tk.LabelFrame(tab, text="API Configuration", font=("Arial", 12, "bold"), bg="#f8fafc", fg="#1a365d")
        group.pack(fill=tk.X, padx=20, pady=20)
        
        # URL
        row0 = tk.Frame(group, bg="#f8fafc"); row0.pack(fill=tk.X, padx=15, pady=8)
        tk.Label(row0, text="Omeka API Endpoint:", font=("Arial", 10, "bold"), bg="#f8fafc").pack(side="left")
        tk.Entry(row0, textvariable=self.omeka_api_url, width=60).pack(side="left", padx=10)
        tk.Label(row0, text="(e.g., https://site.com/api/)", bg="#f8fafc", fg="#718096").pack(side="left")

        # Key
        row1 = tk.Frame(group, bg="#f8fafc"); row1.pack(fill=tk.X, padx=15, pady=8)
        tk.Label(row1, text="Omeka API Key:", font=("Arial", 10, "bold"), bg="#f8fafc").pack(side="left")
        self.omeka_api_entry = tk.Entry(row1, textvariable=self.omeka_api_key, show="*", width=60)
        self.omeka_api_entry.pack(side="left", padx=10)
        tk.Checkbutton(row1, text="Remember key", variable=self.remember_key, bg="#f8fafc").pack(side="left", padx=(10,0))
        tk.Button(row1, text="Forget Key", command=self.forget_saved_key, bg="#e53e3e", fg="white").pack(side="left", padx=10)

        # Connection & Mapping
        row1b = tk.Frame(group, bg="#f8fafc"); row1b.pack(fill=tk.X, padx=15, pady=10)
        tk.Button(row1b, text="1. Test Connection", command=self.test_omeka_connection, bg="#4299e1", fg="white").pack(side="left")
        tk.Button(row1b, text="2. Fetch Element IDs (Required)", command=self.fetch_element_ids, bg="#805ad5", fg="white").pack(side="left", padx=15)
        self.mapping_status = tk.Label(row1b, text="IDs not mapped", bg="#f8fafc", fg="#e53e3e")
        self.mapping_status.pack(side="left")

        # Output
        group2 = tk.LabelFrame(tab, text="Output & Utilities", font=("Arial", 12, "bold"), bg="#f8fafc", fg="#1a365d")
        group2.pack(fill=tk.X, padx=20, pady=10)
        row2 = tk.Frame(group2, bg="#f8fafc"); row2.pack(fill=tk.X, padx=15, pady=8)
        tk.Entry(row2, textvariable=self.output_dir_var, width=80).pack(side="left", padx=(0,10))
        tk.Button(row2, text="Browse", command=self.browse_output_directory, bg="#ed8936", fg="white").pack(side="left")
        tk.Button(row2, text="Open Folder", command=self.open_output_directory).pack(side="left", padx=6)
        tk.Button(row2, text="Export Log", command=self.export_log).pack(side="left", padx=6)

        tk.Button(tab, text="💾 Save Configuration", command=self.save_settings, bg="#38a169", fg="white",
                  font=("Arial", 12, "bold"), padx=20, pady=6).pack(pady=16)

    def create_upload_tab(self):
        tab = tk.Frame(self.notebook, bg="#f8fafc"); self.notebook.add(tab, text="📤 Upload Data")

        # File
        file_group = tk.LabelFrame(tab, text="Select CSV File", font=("Arial", 12, "bold"), bg="#f8fafc", fg="#1a365d")
        file_group.pack(fill=tk.X, padx=20, pady=(20,10))
        row = tk.Frame(file_group, bg="#f8fafc"); row.pack(fill=tk.X, padx=15, pady=12)
        self.upload_file_label = tk.Label(row, text="No file selected", bg="#f8fafc", fg="#718096"); self.upload_file_label.pack(side="left")
        tk.Button(row, text="📂 Browse CSV", bg="#4299e1", fg="white", command=self.browse_upload_file).pack(side="left", padx=10)

        # Options
        opt_group = tk.LabelFrame(tab, text="Upload Options", font=("Arial", 12, "bold"), bg="#f8fafc", fg="#1a365d")
        opt_group.pack(fill=tk.X, padx=20, pady=6)
        
        crow = tk.Frame(opt_group, bg="#f8fafc"); crow.pack(fill=tk.X, padx=15, pady=8)
        tk.Label(crow, text="Delimiter:", bg="#f8fafc").pack(side="left")
        ttk.Combobox(crow, textvariable=self.csv_delimiter, values=["Auto", "Comma (,)", "Semicolon (;)", "Tab (\\t)"], width=15, state="readonly").pack(side="left", padx=8)
        
        tk.Label(crow, text="Primary Language:", bg="#f8fafc").pack(side="left", padx=(15,0))
        tk.Radiobutton(crow, text="Spanish (ES)", variable=self.target_lang_pref, value="spanish", bg="#f8fafc").pack(side="left")
        tk.Radiobutton(crow, text="English (EN)", variable=self.target_lang_pref, value="english", bg="#f8fafc").pack(side="left")

        orow2 = tk.Frame(opt_group, bg="#f8fafc"); orow2.pack(fill=tk.X, padx=15, pady=6)
        tk.Checkbutton(orow2, text="Render HTML values", variable=self.render_html_values, bg="#f8fafc").pack(side="left")
        tk.Checkbutton(orow2, text="Make items public", variable=self.items_public, bg="#f8fafc").pack(side="left", padx=15)
        tk.Checkbutton(orow2, text="Dry-run (Log only)", variable=self.dry_run, bg="#f8fafc").pack(side="left", padx=15)
        tk.Label(orow2, text="Limit:", bg="#f8fafc").pack(side="left", padx=(20,5))
        tk.Entry(orow2, textvariable=self.upload_limit, width=6).pack(side="left")

        # Controls
        ctrl = tk.Frame(tab, bg="#f8fafc"); ctrl.pack(fill=tk.X, padx=20, pady=12)
        self.upload_btn = tk.Button(ctrl, text="📤 Start Upload", command=self.start_upload,
                                    bg="#e53e3e", fg="white", font=("Arial", 13, "bold"), padx=18, pady=8); self.upload_btn.pack(side="left")
        self.cancel_btn = tk.Button(ctrl, text="✋ Cancel", command=self.request_cancel, state="disabled"); self.cancel_btn.pack(side="left", padx=10)
        tk.Button(ctrl, text="🧪 Test Single Row", command=self.test_single_upload,
                  bg="#d69e2e", fg="white", font=("Arial", 11, "bold"), padx=14, pady=6).pack(side="left", padx=12)
        tk.Button(ctrl, text="🧹 Clear Log", command=self.clear_upload_log,
                  bg="#718096", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=12)

        # Progress & log
        prog = tk.LabelFrame(tab, text="Progress", font=("Arial", 12, "bold"), bg="#f8fafc", fg="#1a365d")
        prog.pack(fill=tk.BOTH, expand=True, padx=20, pady=(10, 20))
        srow = tk.Frame(prog, bg="#f8fafc"); srow.pack(fill=tk.X, padx=15, pady=8)
        self.upload_total_label   = tk.Label(srow, text="Total: 0", bg="#f8fafc")
        self.upload_success_label = tk.Label(srow, text="Success: 0", bg="#f8fafc", fg="#38a169")
        self.upload_failed_label  = tk.Label(srow, text="Failed: 0",  bg="#f8fafc", fg="#e53e3e")
        self.upload_total_label.pack(side="left", padx=10)
        self.upload_success_label.pack(side="left", padx=10)
        self.upload_failed_label.pack(side="left", padx=10)
        self.upload_progress = ttk.Progressbar(prog, mode="determinate"); self.upload_progress.pack(fill=tk.X, padx=15, pady=(0,10))
        self.upload_log = scrolledtext.ScrolledText(prog, height=16, font=("Consolas", 9),
                                                    bg="#1a202c", fg="#e2e8f0", insertbackground="white")
        self.upload_log.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 12))

    def create_about_tab(self):
        tab = tk.Frame(self.notebook, bg="#f8fafc"); self.notebook.add(tab, text="ℹ️ About")
        tk.Label(tab, text="MARACAS Pro v4.0", font=("Arial", 16, "bold"), bg="#f8fafc", fg="#1a365d").pack(pady=20)
        tk.Label(tab, text="Corrects hardcoded IDs and URLs from v3.\nIncludes dynamic element mapping and file URL support.",
                 bg="#f8fafc", fg="#4a5568").pack()

    # ---------------------------- Core Logic ----------------------------
    def _drain_log_queue(self):
        try:
            while True:
                msg = self._log_q.get_nowait()
                ts = time.strftime("%H:%M:%S")
                self.upload_log.insert(tk.END, f"[{ts}] {msg}\n")
                self.upload_log.see(tk.END)
                self.status_label.config(text=msg)
        except queue.Empty:
            pass
        self.root.after(60, self._drain_log_queue)

    def enqueue_log(self, message): self._log_q.put(message)
    def _ui(self, fn, *args, **kwargs): self.root.after(0, lambda: fn(*args, **kwargs))

    # ---------------------------- Config & Key ----------------------------
    def save_settings(self):
        try:
            settings = {
                "output_dir": self.output_dir_var.get(),
                "api_url": self.omeka_api_url.get().strip()
            }
            Path(".maracas_pro_settings.json").write_text(json.dumps(settings, indent=2), encoding="utf-8")
            self.save_api_key_if_opted()
            messagebox.showinfo("Success", "⚙️ Configuration saved.")
        except Exception as e:
            messagebox.showerror("Error", f"Error saving configuration: {e}")

    def load_settings(self):
        try:
            p = Path(".maracas_pro_settings.json")
            if p.exists():
                data = json.loads(p.read_text(encoding="utf-8"))
                if data.get("output_dir"):
                    self.output_dir = data["output_dir"]; self.output_dir_var.set(self.output_dir)
                if data.get("api_url"):
                    self.omeka_api_url.set(data["api_url"])
        except Exception: pass

    def load_saved_key(self):
        # 1. Try Keyring
        if keyring:
            try:
                saved = keyring.get_password("MARACAS-PRO", "OMEKA_API_KEY")
                if saved: self.omeka_api_key.set(saved); self.enqueue_log("🔑 Loaded key from Keychain"); return
            except Exception: pass
        # 2. Try File
        try:
            p = Path.home() / ".maracas_pro.json"
            if p.exists():
                data = json.loads(p.read_text(encoding="utf-8"))
                if data.get("api_key"):
                    self.omeka_api_key.set(data["api_key"])
                    self.enqueue_log("🔑 Loaded key from ~/.maracas_pro.json")
        except Exception: pass

    def save_api_key_if_opted(self):
        if not self.remember_key.get(): return
        key = self.omeka_api_key.get().strip()
        if not key: return
        # Try Keyring
        if keyring:
            try:
                keyring.set_password("MARACAS-PRO", "OMEKA_API_KEY", key)
                return
            except Exception: pass
        # Fallback File
        try:
            p = Path.home() / ".maracas_pro.json"
            p.write_text(json.dumps({"api_key": key}), encoding="utf-8")
        except Exception: pass

    def forget_saved_key(self):
        if keyring:
            try: keyring.delete_password("MARACAS-PRO", "OMEKA_API_KEY")
            except Exception: pass
        try:
            p = Path.home() / ".maracas_pro.json"
            if p.exists(): p.unlink()
        except Exception: pass
        self.omeka_api_key.set("")
        self.enqueue_log("🧹 Removed saved API key")

    # ---------------------------- API Logic ----------------------------
    def get_api_url(self, endpoint=""):
        base = self.omeka_api_url.get().strip()
        if not base.endswith("/"): base += "/"
        return urljoin(base, endpoint)

    def test_omeka_connection(self):
        url = self.get_api_url("site")
        self.enqueue_log(f"🔎 Testing: {url}")
        try:
            r = self.session.get(url, params={"key": self.omeka_api_key.get()}, timeout=10)
            if r.status_code == 200:
                self.omeka_status.config(fg="#38a169", text="API Status: OK")
                self.enqueue_log("✅ Connection Successful.")
                messagebox.showinfo("Success", "Connected to Omeka API!")
            elif r.status_code == 403:
                self.omeka_status.config(fg="#f59e0b", text="API Status: 403")
                messagebox.showwarning("Auth Error", "API Key Invalid or insufficient permissions.")
            else:
                self.omeka_status.config(fg="#ef4444", text=f"Status: {r.status_code}")
                self.enqueue_log(f"❌ Error {r.status_code}: {r.text}")
        except Exception as e:
            self.enqueue_log(f"❌ Network Error: {e}")
            messagebox.showerror("Connection Error", str(e))

    def fetch_element_ids(self):
        """Dynamically fetch Dublin Core IDs from the API."""
        url = self.get_api_url("elements")
        self.enqueue_log("🔄 Fetching Element IDs from API...")
        try:
            # We need to page through if there are many, but usually 50 gets DC
            r = self.session.get(url, params={"key": self.omeka_api_key.get(), "per_page": 200})
            if r.status_code != 200:
                raise Exception(f"API returned {r.status_code}")
            
            data = r.json()
            mapping = {}
            for el in data:
                # We typically only care about 'Dublin Core' set, but mapping by name is usually safe enough unique
                name = el.get("name")
                eid = el.get("id")
                if name and eid:
                    mapping[name] = eid
            
            # Update our map
            self.dc_elements = mapping
            self.mapping_status.config(text=f"✅ Mapped {len(mapping)} IDs", fg="#38a169")
            self.enqueue_log(f"✅ Successfully mapped {len(mapping)} Element IDs.")
            
            # Verify critical ones exist
            if "Title" not in self.dc_elements:
                self.enqueue_log("⚠️ Warning: 'Title' element not found in API response.")
                
        except Exception as e:
            self.enqueue_log(f"❌ Failed to fetch elements: {e}")
            self.dc_elements = self.default_dc_map
            self.mapping_status.config(text="⚠️ Using Fallback Defaults", fg="#f59e0b")
            self.enqueue_log("⚠️ Using default hardcoded IDs (Risk of mismatch!)")

    # ---------------------------- CSV & Processing ----------------------------
    def browse_output_directory(self):
        p = filedialog.askdirectory()
        if p: self.output_dir_var.set(p)

    def open_output_directory(self):
        path = self.output_dir_var.get()
        if sys.platform == 'win32': os.startfile(path)
        else: os.system(f'xdg-open "{path}"')

    def export_log(self):
        out = Path(self.output_dir_var.get()) / f"maracas_log_{int(time.time())}.txt"
        out.write_text(self.upload_log.get("1.0", tk.END), encoding="utf-8")
        self.enqueue_log(f"Log saved to {out}")

    def browse_upload_file(self):
        path = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
        if path:
            self.input_csv_file = path
            self.upload_file_label.config(text=os.path.basename(path), fg="#38a169")

    def _detect_delimiter(self, path):
        if self.csv_delimiter.get() == "Comma (,)": return ","
        if self.csv_delimiter.get() == "Semicolon (;)": return ";"
        if self.csv_delimiter.get() == "Tab (\\t)": return "\t"
        try:
            with open(path, "r", encoding="utf-8") as f: sample = f.read(2048)
            return csv.Sniffer().sniff(sample).delimiter
        except: return ","

    def _read_csv(self):
        sep = self._detect_delimiter(self.input_csv_file)
        df = pd.read_csv(self.input_csv_file, dtype=str, sep=sep).fillna("")
        # Normalize headers
        clean_cols = {}
        for c in df.columns:
            clean_cols[c] = c.strip().replace("  ", " ")
        df.rename(columns=clean_cols, inplace=True)
        return df

    # ---------------------------- Item Construction ----------------------------
    def get_element_id(self, name):
        # Returns ID if found, else None
        return self.dc_elements.get(name)

    def prepare_item_payload(self, row):
        """Constructs the JSON body for Omeka."""
        element_texts = []
        lang_pref = self.target_lang_pref.get() # 'english' or 'spanish'

        # Helper to get value from row, checking (EN)/(ES) variants
        def get_val(base_name):
            # Helper to check if a value exists and is non-empty
            def has_value(key):
                val = row.get(key)
                if val is None:
                    return False
                return bool(str(val).strip())
            
            val = None
            
            # 1. Try Preference first
            if lang_pref == "english":
                if has_value(f"{base_name} (EN)"):
                    val = row.get(f"{base_name} (EN)")
                elif has_value(f"{base_name} (ES)"):
                    val = row.get(f"{base_name} (ES)")
            else:  # spanish
                if has_value(f"{base_name} (ES)"):
                    val = row.get(f"{base_name} (ES)")
                elif has_value(f"{base_name} (EN)"):
                    val = row.get(f"{base_name} (EN)")
            
            # 2. Try Naked Name if no bilingual version found
            if not val and has_value(base_name):
                val = row.get(base_name)
            
            return str(val).strip() if val else ""

        # Map standard DC fields
        dc_fields = [
            "Title", "Creator", "Subject", "Description", "Publisher", "Contributor", 
            "Date", "Type", "Format", "Identifier", "Source", "Language", 
            "Relation", "Coverage", "Rights"
        ]

        render_html = self.render_html_values.get()

        for field in dc_fields:
            text = get_val(field)
            if not text: continue
            
            el_id = self.get_element_id(field)
            if not el_id: continue

            # HTML Check
            is_html = False
            if "<" in text and ">" in text:
                if render_html: is_html = True
                else: text = html_mod.escape(text)

            element_texts.append({
                "element": {"id": el_id},
                "text": text,
                "html": is_html
            })

        # Logic for File URLs (If available)
        file_urls = []
        raw_files = row.get("Files (if available)") or row.get("Files")
        if raw_files:
            # Split by comma or pipe
            parts = re.split(r'[;|]', str(raw_files))
            for p in parts:
                p = p.strip()
                if p.startswith("http"):
                    file_urls.append(p)
        
        # Logic for Tags
        tags = []
        raw_tags = get_val("Tags")
        if raw_tags:
            parts = re.split(r'[,;]', raw_tags)
            tags = [{"name": t.strip()} for t in parts if t.strip()]

        payload = {
            "public": self.items_public.get(),
            "element_texts": element_texts,
            "tags": tags
        }
        
        # Add file URLs only if present
        if file_urls:
            payload["file_urls"] = file_urls

        return payload

    # ---------------------------- Upload Loop ----------------------------
    def start_upload(self):
        if not self.input_csv_file: return messagebox.showerror("Error", "Select CSV first")
        if not self.dc_elements: 
            messagebox.showwarning("Warning", "You haven't fetched Element IDs yet.\nUsing defaults (might fail).")
            self.dc_elements = self.default_dc_map

        self.cancel_requested = False
        self.upload_btn.config(state="disabled")
        self.cancel_btn.config(state="normal")
        threading.Thread(target=self._run_upload, daemon=True).start()

    def request_cancel(self):
        self.cancel_requested = True
        self.enqueue_log("✋ Cancel requested...")

    def test_single_upload(self):
        if not self.input_csv_file: return
        threading.Thread(target=self._run_single_test, daemon=True).start()

    def _run_single_test(self):
        try:
            df = self._read_csv()
            if df.empty: return self.enqueue_log("CSV Empty")
            
            row = df.iloc[0].to_dict()
            self.enqueue_log("🧪 Testing first row payload construction...")
            payload = self.prepare_item_payload(row)
            
            self.enqueue_log(f"📦 JSON Payload (Partial): {str(payload)[:300]}...")
            
            if self.dry_run.get():
                self.enqueue_log("✅ Dry Run: Payload looks good.")
                return

            self.enqueue_log("🚀 Sending POST...")
            url = self.get_api_url("items")
            r = self.session.post(url, json=payload, params={"key": self.omeka_api_key.get()})
            
            if r.status_code == 201:
                new_id = r.json().get("id")
                self.enqueue_log(f"✅ SUCCESS! Created Item ID: {new_id}")
            else:
                self.enqueue_log(f"❌ Failed: {r.status_code} - {r.text}")

        except Exception as e:
            self.enqueue_log(f"❌ Error: {e}")

    def _run_upload(self):
        try:
            df = self._read_csv()
            data = df.to_dict(orient="records")
            limit = self.upload_limit.get()
            if limit > 0: data = data[:limit]
            
            total = len(data)
            self._ui(self.upload_total_label.config, text=f"Total: {total}")
            self.stats = {"upload_success": 0, "upload_failed": 0}
            self._ui(self.upload_progress.configure, value=0)

            delay = self.req_delay_ms.get() / 1000.0
            url = self.get_api_url("items")
            
            self.enqueue_log(f"🚀 Starting Batch: {total} items")

            for i, row in enumerate(data):
                if self.cancel_requested: break
                
                payload = self.prepare_item_payload(row)
                
                if not self.dry_run.get():
                    try:
                        r = self.session.post(url, json=payload, params={"key": self.omeka_api_key.get()})
                        if r.status_code == 201:
                            self.stats["upload_success"] += 1
                            item_id = r.json().get("id")
                            self.enqueue_log(f"✅ Item {i+1}: Created (ID {item_id})")
                        else:
                            self.stats["upload_failed"] += 1
                            self.enqueue_log(f"❌ Item {i+1}: Failed ({r.status_code})")
                    except Exception as e:
                        self.stats["upload_failed"] += 1
                        self.enqueue_log(f"❌ Item {i+1}: Exception {e}")
                else:
                    self.stats["upload_success"] += 1
                    self.enqueue_log(f"✅ Item {i+1}: Dry run OK")

                # UI Update
                self._ui(self.upload_success_label.config, text=f"Success: {self.stats['upload_success']}")
                self._ui(self.upload_failed_label.config, text=f"Failed: {self.stats['upload_failed']}")
                self._ui(self.upload_progress.configure, value=((i+1)/total)*100)
                
                time.sleep(delay)

            self.enqueue_log("🏁 Batch Complete.")

        except Exception as e:
            self.enqueue_log(f"🔥 Critical Error: {e}")
        finally:
            self._ui(self.upload_btn.config, state="normal")
            self._ui(self.cancel_btn.config, state="disabled")

    def clear_upload_log(self):
        self.upload_log.delete(1.0, tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = MaracasProV4(root)
    root.mainloop()