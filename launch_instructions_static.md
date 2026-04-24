# Blood Collection Dashboard - Quick Launch Guide

## Three Options Available

### Option 1: Static HTML (Simplest ⭐ Recommended for Sharing)
**File:** `Blood_Collection_Dashboard_Static.html`

1. Double-click the HTML file
2. Opens in your default browser automatically
3. **Pros:** Smallest file (~219KB), universal compatibility, easiest to share
4. **Note:** Requires internet connection for Plotly CDN charts

---

### Option 2: Native Desktop App (Fastest)
**File:** `Blood_Collection_Dashboard`

1. Double-click the executable
2. Dashboard opens in a native desktop window
3. **Pros:** Fastest launch, no browser overhead, works offline
4. **Best for:** Regular use on your Mac

---

### Option 3: Browser App (Familiar UI)
**File:** `Blood_Collection_Dashboard_Web`

1. Double-click the executable
2. Your browser opens automatically with dashboard
3. **Pros:** Full browser UI, interactive
4. **Best for:** Those who prefer browser interface

---

## Which Should I Use?

| Use Case | Recommended | Why |
|----------|-------------|-----|
| Share results via email | **Option 1 (HTML)** | Tiny file, universal |
| Daily dashboard use | **Option 2 (Desktop)** | Fastest, native |
| Detailed analysis | **Option 3 (Browser)** | Full interactivity |
| No internet available | **Option 2 or 3** | Offline capable |

---

## File Sizes
- **Static HTML:** 219 KB ⚡
- **Desktop App:** ~50 MB 🚀
- **Browser App:** ~57 MB 🌐

---

## Refresh Data
To generate fresh data and update the static HTML:
1. Run `python3 export_static_html.py` in the folder
2. New `Blood_Collection_Dashboard_Static.html` will be created

---

## Troubleshooting

**HTML won't open?**
- Try right-click → Open with → Your browser
- Check file associations for .html files

**Charts not showing in HTML?**
- Check internet connection (Plotly CDN required)
- Try opening in a different browser

**Apps won't open?**
- macOS: Right-click → Open → Open
- This is a macOS security warning, not a problem

**Dashboard shows no data?**
- Make sure data files exist in `output_files/` folder
- Run `python3 scripts/generate_data.py` to regenerate

---

## Dashboard Features

- **4 Tabs:** Blood Collected, Plasma, Serum, PBMC Processing
- **KPI Cards:** Collection rates, sample counts, participant totals
- **Interactive Charts:** Bar charts, histograms, heatmaps
- **Hover Tooltips:** See detailed info on any data point
- **50% Benchmark:** Visual threshold line for collection rates
- **100 Participants × 12 Visits:** Complete trial data

---

**Questions?** See `README_User_Guide.md` for detailed instructions.
