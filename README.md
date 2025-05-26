# StealthShare v0.1 pre1

**A simple metadata remover for photos and some documents.**

## Disclaimer

Please don't judge too harshly, I'm a beginner developer. Feedback is welcome! This project is a learning experience for me.

## About StealthShare

StealthShare is a user-friendly desktop application designed to help you protect your privacy by removing potentially sensitive metadata from your files before sharing them. It's built entirely in Python and compiled into a single executable using PyInstaller for ease of use on Windows.

The application allows for batch processing of files, meaning you can clean multiple files at once. It's open-source, and I hope it will be useful to others.

## Features

* **Metadata Cleaning:** Removes common metadata from images (like EXIF, GPS location) and some document types.
* **Batch Processing:** Clean an unlimited number of files simultaneously.
* **User-Friendly Interface:** Simple GUI to select files, choose cleaning profiles, and manage output.
* **Cleaning Profiles:**
    * **Standard:** Removes common private information (EXIF geolocation, author data), aims for compatibility.
    * **Aggressive:** Attempts to remove maximum metadata, including XMP, IPTC, and all PNG chunks. This might affect some specific file functionalities.
    * **EXIF Only (for photos):** Removes only EXIF data from images, leaving other data untouched.
* **Optional ICC Profile Preservation:** Choose whether to keep or remove ICC color profiles from images.
* **Optional Output Sorting:** Organize cleaned files into subfolders by type (Images, PDF, Documents).
* **Multilingual Interface:** Supports English and Russian, with auto-detection based on system language and manual switching.
* **Cross-Platform (Python source):** While the `.exe` is for Windows, the Python source can be run on other platforms where Python and the required libraries are available.
* **Open Source:** The code is available for review and contributions.

## Supported File Types (for metadata cleaning)

* **Images:** JPG, JPEG, PNG, TIFF, TIF, GIF, WebP, BMP
* **Documents:** DOCX (Microsoft Word), XLSX (Microsoft Excel), PPTX (Microsoft PowerPoint)
* **PDF:** Adobe PDF

## How It Works (Simplified)

StealthShare uses a combination of Python libraries to handle metadata:
* **Pillow (PIL Fork) & piexif:** For reading and removing EXIF, XMP (attempted), and other image-specific metadata.
* **pikepdf:** For robust PDF metadata cleaning (Info dictionary, XMP).
* **python-docx, openpyxl, python-pptx:** For cleaning core properties from Microsoft Office documents.

The application provides different cleaning profiles to balance between privacy and file integrity/functionality.

## Future Development

This is an ongoing project, and I plan to improve and add more features in the future, such as:
* More granular control over metadata removal.
* Support for more file formats.
* Enhanced reporting.
* (Potentially) Drag-and-Drop functionality once cross-platform library compatibility improves.

## For Developers

### Tech Stack

* **Language:** Python 3
* **GUI:** Tkinter (with ttk for theming)
* **Core Libraries:** Pillow, piexif, pikepdf, python-docx, openpyxl, python-pptx
* **Packaging (for .exe):** PyInstaller

### Building the .exe (Example for Windows)

You'll need PyInstaller: `pip install pyinstaller`

1.  Prepare an icon file (e.g., `stealthshare.ico` for the executable, and `stealthshare_icon.png` for the application window). Place them in your project directory.
2.  Run the PyInstaller command from your project directory:
    ```bash
    python -m PyInstaller --onefile --windowed --name StealthShare --icon=stealthshare.ico --add-data "stealthshare_icon.png:." main.py
    ```
    * `--icon=stealthshare.ico`: Sets the icon for the `.exe` file itself.
    * `--add-data "stealthshare_icon.png:."`: Bundles the PNG icon used by the application window. The `:.` ensures it's placed in the root of the bundled data.

    The executable `StealthShare.exe` will be in the `dist` folder.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details (you'll need to create this file if you haven't).

## Feedback

Your feedback is highly appreciated! If you encounter any issues or have suggestions for improvement, please feel free to open an issue on the GitHub repository.

---
*IQUXAe*
