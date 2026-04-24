# Blood Collection Dashboard - User Guide

**For: Non-technical users who need to view biomarker collection data**

---

## 🎯 What Is This?

The Blood Collection Dashboard is a desktop application that monitors the progress of blood sample collection in clinical trials. It displays:

- **Overall collection rate** (percentage)
- **Samples collected vs. not collected**
- **12 different visits** tracked over time
- **Collection status** for all 100 participants
- **4 data views**: Blood, Plasma, Serum, and PBMC processing

---

## 🚀 Quick Start (Two Easy Options)

### Option A: Native Desktop App (Recommended)

1. **Download** `Blood_Collection_Dashboard.app`
2. **Double-click** to launch
3. **Dashboard opens** in a native window
4. **Click tabs** to view different data types

**Best for:** Familiar desktop app experience, faster loading

---

### Option B: Browser-based App

1. **Download** `Blood_Collection_Dashboard_Web.app`
2. **Double-click** to launch
3. **Browser opens automatically** at http://127.0.0.1:8050
4. **Dashboard displays** in your browser

**Best for:** Web-based interface, familiar browser experience

---

## 📊 What You'll See

### Header
- **Title:** Blood Collection Dashboard
- **Info:** Number of participants and visits

### Tabs
- **Blood Collected** - Primary blood collection status
- **Plasma Processing** - Plasma sample processing
- **Serum Processing** - Serum sample processing  
- **PBMC Processing** - White blood cell processing

### Each Tab Shows:
1. **KPI Cards**
   - Overall Collection Rate (percentage)
   - Samples Collected
   - Samples Not Collected
   - Total Participants

2. **Charts**
   - Collection Rate by Visit (12 visits)
   - Participant Distribution (how many collected what %)
   - Collection Status Matrix (heatmap showing all participants × all visits)

---

## 🔍 Understanding the Heatmap

The heatmap shows collection status for every participant at every visit:

```
Green squares = Blood collected for this visit
Red squares   = Blood NOT collected for this visit
```

- **Rows:** Individual participants (BL_001 to BL_100)
- **Columns:** Visit 1 through Visit 12
- **Color:** Shows whether collection happened for that visit

---

## ❓ Need Fresh Sample Data?

If you need to regenerate the sample data:

1. Open a terminal
2. Navigate to the dashboard folder
3. Run: `python scripts/generate_data.py`
4. Restart the dashboard app

---

## 🐛 Troubleshooting

### App won't open?
**macOS Security:** If you see "Can't be opened because it's from an unidentified developer":

1. Right-click (or Control-click) the app
2. Select **Open**
3. Click **Open** in the warning dialog
4. The app will now open normally

### No charts showing?
- Make sure the app is fully loaded
- Check if sample data files exist in `output_files/` folder
- Try regenerating data: `python scripts/generate_data.py`

### Charts are small?
- The app window can be resized
- Drag the window edges to make it larger
- Charts will adjust automatically

### Browser won't open (Web version)?
- Check your firewall settings
- Ensure port 8050 is not blocked
- Try opening http://127.0.0.1:8050 manually

---

## 📁 File Structure

```
Blood Collection Dashboard/
├── Blood_Collection_Dashboard.app          # Option A (Native)
├── Blood_Collection_Dashboard_Web.app      # Option B (Browser)
├── output_files/                           # Data files
│   ├── blood_collected_at_visit.csv
│   ├── blood_plasma_processed.csv
│   ├── blood_serum_processed.csv
│   └── blood_pbmc_processed.csv
└── README_User_Guide.md                    # This file
```

---

## 💡 Tips

- **Hover over charts** to see detailed values
- **Click tabs** to switch between different biomarker types
- **Heatmap colors** update automatically when data changes
- **Collection threshold:** The 50% line indicates the benchmark for adequate collection

---

## 📞 Support

For questions about this dashboard or technical issues:

- **Data issues:** Check that CSV files are present in `output_files/`
- **App issues:** Try both the native and web versions
- **Report problems:** Contact your technical team with:
  - Which version (Native or Web)
  - What you expected vs. what happened
  - Screenshots if possible

---

**Enjoy monitoring your clinical trial data!** 🎉
