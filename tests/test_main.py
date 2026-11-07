"""Offline tests for photo EXIF dates and filesystem timestamps."""

import os
import platform
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from PIL import ExifTags, Image

import main


if os.name == "nt":
    preferred_temp_dir = Path(os.environ.get("LOCALAPPDATA", "")) / "Temp" / "opencode"
else:
    preferred_temp_dir = Path()
TEST_TEMP_DIR = preferred_temp_dir if preferred_temp_dir.is_dir() else Path(tempfile.gettempdir())


class PhotoDateTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(dir=TEST_TEMP_DIR)
        self.addCleanup(self.temp_dir.cleanup)
        self.folder = Path(self.temp_dir.name)

    def create_image_with_exif(self, name="photo.jpg"):
        path = self.folder / name
        exif = Image.Exif()
        exif[306] = "2020:01:01 00:00:00"
        exif_ifd = exif.get_ifd(ExifTags.IFD.Exif)
        exif_ifd[36867] = "2018:05:15 14:30:00"
        exif_ifd[36868] = "2018:05:15 14:30:00"
        Image.new("RGB", (16, 16), "white").save(path, exif=exif)
        return path

    def test_reads_capture_date_from_nested_exif_ifd(self):
        path = self.create_image_with_exif()
        fallback_time = datetime(2022, 1, 1).timestamp()
        os.utime(path, (fallback_time, fallback_time))

        self.assertEqual(main.get_photo_datetime(path), datetime(2018, 5, 15, 14, 30, 0))

    def test_updates_exif_fields_and_modification_time(self):
        path = self.create_image_with_exif()
        target = datetime(2024, 5, 15, 14, 30, 0)

        main.apply_date_to_file(path, target)

        with Image.open(path) as image:
            exif = image.getexif()
            exif_ifd = exif.get_ifd(ExifTags.IFD.Exif)
            self.assertEqual(exif.get(306), "2024:05:15 14:30:00")
            self.assertEqual(exif_ifd.get(36867), "2024:05:15 14:30:00")
            self.assertEqual(exif_ifd.get(36868), "2024:05:15 14:30:00")

        self.assertAlmostEqual(path.stat().st_mtime, target.timestamp(), delta=1)

    @unittest.skipUnless(platform.system() == "Windows", "Windows creation time is platform-specific")
    def test_windows_creation_time_uses_local_datetime(self):
        path = self.folder / "timestamp.txt"
        path.write_text("temporary test file", encoding="ascii")
        target = datetime(2020, 1, 2, 3, 4, 5)

        main.set_creation_time(path, target)

        self.assertAlmostEqual(path.stat().st_ctime, target.timestamp(), delta=2)

    def test_cli_runs_with_cp1252_console_encoding(self):
        result = subprocess.run(
            [sys.executable, "-B", str(Path(main.__file__).resolve())],
            input="__missing_photo_test_path__\n\n",
            text=True,
            encoding="cp1252",
            capture_output=True,
            env={**os.environ, "PYTHONIOENCODING": "cp1252"},
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Error: Path does not exist.", result.stdout)


if __name__ == "__main__":
    unittest.main()
