import os
import sys
import platform
from pathlib import Path
from datetime import datetime, timezone
from PIL import Image
from PIL import ExifTags
from PIL.ExifTags import TAGS
from tqdm import tqdm

DATE_TAG_IDS = {
    tag_name: tag_id
    for tag_id, tag_name in TAGS.items()
    if tag_name in {"DateTime", "DateTimeOriginal", "DateTimeDigitized"}
}

if platform.system() == "Windows":
    import ctypes
    from ctypes import wintypes

    def set_creation_time(path, dt):
        """
        Updates the Windows file creation timestamp using local time and WinAPI.
        """
        FILE_WRITE_ATTRIBUTES = 0x100
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.CreateFileW.argtypes = (
            wintypes.LPCWSTR,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.LPVOID,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.HANDLE,
        )
        kernel32.CreateFileW.restype = wintypes.HANDLE
        kernel32.SetFileTime.argtypes = (
            wintypes.HANDLE,
            ctypes.POINTER(wintypes.FILETIME),
            ctypes.POINTER(wintypes.FILETIME),
            ctypes.POINTER(wintypes.FILETIME),
        )
        kernel32.SetFileTime.restype = wintypes.BOOL
        kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
        kernel32.CloseHandle.restype = wintypes.BOOL

        handle = kernel32.CreateFileW(
            str(path),
            FILE_WRITE_ATTRIBUTES,
            0,
            None,
            3,
            0,
            None,
        )
        if handle is None or handle == ctypes.c_void_p(-1).value:
            raise OSError(ctypes.get_last_error(), f"Could not open file for timestamp update: {path}")

        utc_dt = dt.astimezone(timezone.utc)
        delta = utc_dt - datetime(1601, 1, 1, tzinfo=timezone.utc)
        filetime_ticks = (
            (delta.days * 86400 + delta.seconds) * 10**7
            + delta.microseconds * 10
        )
        creation_time = wintypes.FILETIME(
            filetime_ticks & 0xFFFFFFFF,
            filetime_ticks >> 32,
        )

        try:
            if not kernel32.SetFileTime(handle, ctypes.byref(creation_time), None, None):
                raise OSError(ctypes.get_last_error(), f"Could not set file creation time: {path}")
        finally:
            kernel32.CloseHandle(handle)
else:
    def set_creation_time(path, dt):
        pass


def get_photo_datetime(file_path):
    """
    Extracts datetime from EXIF metadata. Falls back to file modification time.
    """
    try:
        with Image.open(file_path) as img:
            exif = img.getexif()
            if exif:
                exif_ifd = exif.get_ifd(ExifTags.IFD.Exif)
                for tag_name in ("DateTimeOriginal", "DateTimeDigitized", "DateTime"):
                    tag_id = DATE_TAG_IDS[tag_name]
                    value = exif.get(tag_id) if tag_name == "DateTime" else exif_ifd.get(tag_id)
                    if value is None:
                        value = exif.get(tag_id)
                    if value:
                        try:
                            return datetime.strptime(str(value), "%Y:%m:%d %H:%M:%S")
                        except ValueError:
                            continue
    except Exception:
        pass

    ts = file_path.stat().st_mtime
    return datetime.fromtimestamp(ts)


def apply_date_to_file(file_path, new_dt):
    """
    Updates EXIF date metadata, OS modification time, and Windows creation time.
    """
    original_access_time = file_path.stat().st_atime

    # 1. Update EXIF metadata
    try:
        with Image.open(file_path) as img:
            exif = img.getexif()
            exif_date_str = new_dt.strftime("%Y:%m:%d %H:%M:%S")
            exif[DATE_TAG_IDS["DateTime"]] = exif_date_str
            exif_ifd = exif.get_ifd(ExifTags.IFD.Exif)
            for tag_name in ("DateTimeOriginal", "DateTimeDigitized"):
                exif_ifd[DATE_TAG_IDS[tag_name]] = exif_date_str
                if DATE_TAG_IDS[tag_name] in exif:
                    exif[DATE_TAG_IDS[tag_name]] = exif_date_str

            img.save(file_path, exif=exif)
    except Exception as e:
        print(f"WARNING: Could not update EXIF for {file_path.name}: {e}")

    # 2. Update File System modification & access times
    mod_time = new_dt.timestamp()
    os.utime(file_path, (original_access_time, mod_time))

    # 3. Update Windows File Creation time
    if platform.system() == "Windows":
        try:
            set_creation_time(file_path, new_dt)
        except Exception as e:
            print(f"WARNING: Could not set creation time for {file_path.name}: {e}")


def main():
    print("=" * 60)
    print(" Photo Date & EXIF Modifier")
    print("=" * 60)

    raw_path = input("Enter path to image file or folder: ").strip().strip('"')
    path = Path(raw_path)

    if not path.exists():
        print("Error: Path does not exist.")
        return

    supported_exts = {".jpg", ".jpeg", ".png", ".webp"}
    
    if path.is_file():
        if path.suffix.lower() not in supported_exts:
            print(f"Error: Unsupported file format {path.suffix}")
            return
        files = [path]
    else:
        files = [f for f in path.glob("*") if f.suffix.lower() in supported_exts]

    if not files:
        print("No matching image files found (.jpg, .jpeg, .png, .webp).")
        return

    print(f"\nFound {len(files)} file(s).")
    print("\nSelect operation mode:")
    print("1. Set full exact date (DD/MM/YYYY)")
    print("2. Change year only (preserve original month, day, time)")
    
    choice = input("\nEnter choice (1 or 2): ").strip()

    if choice == "1":
        date_str = input("Enter new date (DD/MM/YYYY): ").strip()
        try:
            target_date = datetime.strptime(date_str, "%d/%m/%Y")
        except ValueError:
            print("Invalid date format. Use DD/MM/YYYY (e.g. 25/12/2023).")
            return

        for f in tqdm(files, desc="Updating date", ascii=True):
            # Preserve original time if available
            orig_dt = get_photo_datetime(f)
            new_dt = target_date.replace(
                hour=orig_dt.hour,
                minute=orig_dt.minute,
                second=orig_dt.second
            )
            apply_date_to_file(f, new_dt)

    elif choice == "2":
        year_str = input("Enter new year (YYYY): ").strip()
        try:
            new_year = int(year_str)
            if not (1900 <= new_year <= 2100):
                raise ValueError()
        except ValueError:
            print("Invalid year. Enter a 4-digit year (e.g. 2024).")
            return

        for f in tqdm(files, desc="Updating year", ascii=True):
            orig_dt = get_photo_datetime(f)
            try:
                new_dt = orig_dt.replace(year=new_year)
            except ValueError:
                # Handle leap year edge case (Feb 29 -> Feb 28)
                new_dt = orig_dt.replace(year=new_year, day=28)
            apply_date_to_file(f, new_dt)
    else:
        print("Invalid choice. Exiting.")
        return

    print("\nAll photo dates updated successfully!")


if __name__ == "__main__":
    main()
    input("\nPress Enter to exit...")
