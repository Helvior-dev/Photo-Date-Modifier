# Photo Date & EXIF Modifier 📅📸

A specialized Python CLI tool to update photo creation dates in EXIF metadata as well as file system timestamps (including Windows Creation Time via native WinAPI).

## 🚀 Features
- **EXIF Metadata Update**: Modifies EXIF tags (`DateTime`, `DateTimeOriginal`, `DateTimeDigitized`) so photo galleries (Google Photos, Apple Photos, Windows Media Player) display the updated timestamp correctly.
- **System Timestamp Sync**: Updates file modification time (`os.utime`) and Windows File Creation Time (`SetFileTime` via `ctypes.WinDLL`).
- **Two Operation Modes**:
  1. **Full Exact Date**: Set a specific day, month, and year (DD/MM/YYYY) while preserving original image capture time (hours, minutes, seconds).
  2. **Year Only**: Update only the year (YYYY) while retaining original month, day, hours, minutes, and seconds (great for fixing camera clock year offsets).
- **Batch & Single File Support**: Works on individual image files or entire directories (`.jpg`, `.jpeg`, `.png`, `.webp`).
- **Progress Tracking**: Real-time progress bar powered by `tqdm`.

## 🛠️ Installation & Setup

1. **Navigate to project directory**:
   ```bash
   cd "Photo date modife"
   ```

2. **Create & activate virtual environment**:
   - **Windows (PowerShell)**:
     ```powershell
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```
   - **Linux / macOS**:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run**:
   ```bash
   python main.py
   ```

## 📝 Modes
- **Mode 1 (Full Date)**: Enter `25/12/2023` -> updates date to Dec 25, 2023.
- **Mode 2 (Year Only)**: Enter `2024` -> photo from `15/05/2018 14:30` becomes `15/05/2024 14:30`.
