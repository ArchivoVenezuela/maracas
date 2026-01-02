# MARACAS Pro v4.0 — Universal Omeka Batch Uploader

MARACAS Pro v4 is a desktop application designed to batch upload items to **any** Omeka Classic installation via CSV. 

**New in v4.0:**
*   **Universal Compatibility:** Works with any Omeka site (no longer hardcoded).
*   **Dynamic Mapping:** Automatically fetches Element IDs from your specific server to prevent metadata errors.
*   **File Uploads:** Can download files from URLs and attach them to items.
*   **Bilingual Logic:** Smart fallback between English and Spanish metadata.

---

## 📦 Installation

### Windows (Easiest Method)
1.  Ensure you have **Python 3.10+** installed.
2.  Place `maracas_pro_v4.py`, `run_maracas_v4.bat`, and `requirements.txt` in a folder.
3.  Double-click **`run_maracas_v4.bat`**.
    *   *The first run will take a minute to set up the environment.*

### Mac / Linux
1.  Open Terminal and navigate to the folder.
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Run the application:
    ```bash
    python3 maracas_pro_v4.py
    ```

---

## ⚙️ Setup Guide (First Run)

The application requires a one-time setup to understand your Omeka installation.

1.  **API Endpoint:** Go to the **Setup** tab. Enter your API URL.
    *   Example: `https://my-archive.org/api/`
    *   *Note: Ensure you have the API plugin enabled in Omeka.*
2.  **API Key:** Enter your key (Users > API Keys in Omeka Admin).
3.  **Test Connection:** Click button **#1**. You should see a green "Success" message.
4.  **Fetch Element IDs (CRITICAL):** Click button **#2**. 
    *   This maps "Title", "Creator", etc., to the specific numeric IDs used by your database.
    *   **If you skip this, metadata may upload to the wrong fields.**

---

## 📄 CSV Formatting

Your CSV should use UTF-8 encoding. The header names determine where data goes.

### Standard Columns
You can use standard Dublin Core names:
*   `Title`, `Creator`, `Subject`, `Description`
*   `Publisher`, `Contributor`, `Date`, `Type`
*   `Format`, `Identifier`, `Source`, `Language`
*   `Relation`, `Coverage`, `Rights`, `Tags`

### Bilingual Columns (Optional)
If you have bilingual data, you can use suffixes. The app will prioritize one language based on your settings in the "Upload Data" tab.
*   `Title (EN)` / `Title (ES)`
*   `Description (EN)` / `Description (ES)`

### File Uploads
To attach files (images, PDFs) to an item, use a column named:
*   **`Files`** (or `Files (if available)`)

**Format:**
*   Contains direct download links (http/https).
*   Multiple files can be separated by a semicolon `;` or pipe `|`.
*   *Example:* `https://site.com/image1.jpg; https://site.com/doc.pdf`

---

## 🚀 How to Upload

1.  Go to the **Upload Data** tab.
2.  **Browse CSV:** Select your file.
3.  **Primary Language:** Choose if you prefer English or Spanish columns (if both exist).
4.  **Options:**
    *   *Render HTML:* If your CSV contains `<b>` or `<a>` tags, check this to render them.
    *   *Make Public:* If unchecked, items will be private (admin-only).
    *   *Dry-Run:* Runs the script and checks for errors **without** actually uploading anything. Highly recommended for the first test.
5.  **Start Upload:** Click the button.

---

## ❓ Troubleshooting

**"API Status: 403"**
*   Your API Key is incorrect, or the user associated with the key does not have permission to add items.

**"Warning: Using Fallback Defaults"**
*   The "Fetch Element IDs" step failed. Check your internet connection and API URL. Using defaults may result in metadata appearing in the wrong fields if your Omeka installation uses custom Element Sets.

**"Files not attaching"**
*   Ensure the URLs in the CSV are **direct** links (ending in .jpg, .pdf, etc.) and are publicly accessible.
*   Check `application/config.ini` in your Omeka installation to ensure `allow_url_fopen` is allowed if self-hosting.

---

## 📄 License
Open Source. Modify as needed for your institution.
