# Photo Date Modifier

An interactive Python CLI for changing photo capture dates and file timestamps.

## Features

- Updates EXIF `DateTime`, `DateTimeOriginal`, and `DateTimeDigitized` fields.
- Updates the file modification time. On Windows, it also updates the file creation time.
- Sets a full date while preserving the original time, or changes only the year.
- Works with one image or supported images directly inside a folder.
- Shows progress with `tqdm` when processing multiple files.

## Supported formats

`jpg`, `jpeg`, `png`, `webp`

## Important

The program edits the selected image files in place and does not create copies. Back up important files first. The folder mode does not search subfolders. On operating systems other than Windows, the creation time is not changed.

If a file has no readable EXIF date, its current modification time is used as the source date. Image applications may display date fields differently.

## Requirements

- Python 3.8 or newer
- Packages listed in `requirements.txt`

## Setup

Clone the repository and enter its directory:

```bash
git clone https://github.com/Helvior-dev/Photo-Date-Modifier.git
cd Photo-Date-Modifier
```

Create and activate a virtual environment, then install dependencies:

- Windows PowerShell:

  ```powershell
  python -m venv venv
  .\venv\Scripts\Activate.ps1
  pip install -r requirements.txt
  ```

- Linux or macOS:

  ```bash
  python3 -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt
  ```

## Usage

Run the program:

```bash
python main.py
```

Enter the path to an image or folder, then choose a mode:

1. Enter a date as `DD/MM/YYYY`. The original capture time is preserved.
2. Enter a year from `1900` to `2100`. The original month, day, and time are preserved. February 29 is changed to February 28 when the target year is not a leap year.
