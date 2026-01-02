# CSV Format Guide for MARACAS Pro v4.0

This guide explains how to format your CSV file for batch uploading items to Omeka Classic.

## Required Encoding

**Your CSV must be saved in UTF-8 encoding** to properly handle Spanish characters, accents, and special symbols.

---

## Standard Columns (Dublin Core)

The following Dublin Core fields are supported:

| Column Name | Description | Example |
|------------|-------------|---------|
| **Title** | Item title | "Simpatía" |
| **Creator** | Author/creator name | "Rodrigo Blanco Calderón" |
| **Subject** | Keywords/topics (comma or semicolon separated) | "Literatura, ficción, novela" |
| **Description** | Detailed description | "A novel about emigration..." |
| **Publisher** | Publishing organization | "Alfaguara" |
| **Contributor** | Additional contributors | "Editor: Juan Pérez" |
| **Date** | Publication or creation date | "2021" |
| **Type** | Item type | "Texto", "Imagen en movimiento" |
| **Format** | Format specification | "Libro", "Cine documental" |
| **Identifier** | Unique identifier/code | "LIT0043" |
| **Source** | Source information | "Archivo Venezuela" |
| **Language** | Language code or name | "Español", "ES", "English" |
| **Relation** | Related resources (URLs) | "https://example.com/link" |
| **Coverage** | Spatial/temporal coverage | "Venezuela, siglo XXI" |
| **Rights** | Rights information | "Referencia externa", "Todos los derechos reservados" |

**Note:** All fields are **optional**. Include only the columns you need.

---

## Bilingual Support

If your data is bilingual, you can use language-specific columns:

- `Title (EN)` / `Title (ES)` - English/Spanish titles
- `Creator (EN)` / `Creator (ES)` - English/Spanish creators
- `Subject (EN)` / `Subject (ES)` - English/Spanish subjects
- `Description (EN)` / `Description (ES)` - English/Spanish descriptions

**How it works:**
- In the "Upload Data" tab, select your **Primary Language** preference
- The app will prioritize that language, but fall back to the other if missing
- Example: If "Spanish (ES)" is selected and both `Title (ES)` and `Title (EN)` exist, it will use `Title (ES)`

---

## Special Columns

### Tags

**Column name:** `Tags`

**Format:** Multiple tags separated by comma (`,`) or semicolon (`;`)

**Example:**
```
Tags
"literatura; ficción; novela; emigración; Venezuela"
```

### File Attachments

**Column name:** `Files` or `Files (if available)`

**Format:** URLs to files, separated by semicolon (`;`) or pipe (`|`)

**Example:**
```
Files (if available)
https://example.com/book-cover.jpg; https://example.com/book-excerpt.pdf
```

**Important:**
- URLs must be direct download links (ending in .jpg, .pdf, etc.)
- Files must be publicly accessible
- Omeka will download and attach these files to the item

---

## CSV Formatting Tips

### 1. Delimiters

The app supports:
- **Comma** (`,`)
- **Semicolon** (`;`)
- **Tab** (`\t`)
- **Auto-detection** (recommended)

Select your delimiter in the "Upload Data" tab.

### 2. Quoting Fields

Fields containing commas, semicolons, or quotes should be enclosed in double quotes:

```
"Literatura, ficción, novela, emigración"
```

If a field contains a double quote, escape it with another double quote:

```
"He said ""Hello"" to me"
```

### 3. Empty Fields

Empty fields are allowed. Just leave them blank or omit the column entirely.

---

## Sample Files

1. **`sample_maracas_upload.csv`** - Full example with all features (bilingual, tags, files)
2. **`sample_maracas_simple.csv`** - Simple example with basic fields only

---

## Common Mistakes to Avoid

❌ **Don't include an "ID" column** - Omeka will assign IDs automatically
❌ **Don't use Excel's default encoding** - Always save as UTF-8
❌ **Don't mix delimiters** - Use the same delimiter throughout
❌ **Don't include HTML in unquoted fields** - Use the "Render HTML values" option instead

✅ **Do save as UTF-8 CSV**
✅ **Do test with "Test Single Row" first**
✅ **Do use "Dry-run" mode** to check your data before uploading
✅ **Do check that element IDs are fetched** before uploading

---

## Quick Start Example

Here's a minimal CSV that will work:

```csv
Title,Creator,Description,Date
My First Item,John Doe,This is a test item,2024
My Second Item,Jane Smith,Another test item,2024
```

That's it! Just include the columns you need.

