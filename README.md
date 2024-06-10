# WaveWeaver

WaveWeaver is an open-source tool designed to automate the process of cutting audio clips based on pauses. It provides an intuitive graphical user interface (GUI) for managing, categorizing, and renaming audio clips, making it ideal for game modders and sound designers.

## Features

- **Automated Audio Cutting:** Automatically cut audio files into individual clips based on silence detection.
- **Adjustable Thresholds:** Use sliders to adjust the silence detection threshold (dB/LUFS) to refine where the cuts occur.
- **Waveform Visualization:** Visual display of the audio waveform with lines indicating the cut points.
- **Clip Adjustment:** Manually adjust the start and end points of each clip for precision.
- **Categorization:** Categorize clips (e.g., "Select," "Move," "Attack") via the GUI.
- **Renaming and Organizing:** Automatically rename and move clips into designated folders.
- **Batch Processing:** Support for batch processing multiple files.

## Getting Started

### Downloading the Program

You can download the latest version of WaveWeaver as a standalone executable. No need to install Python or any additional dependencies.

1. **Download the Executable:**
   - Go to the [Releases](https://github.com/yourusername/WaveWeaver/releases) page on GitHub.
   - Download the latest version for your operating system (e.g., `WaveWeaver.exe` for Windows).

2. **Run the Program:**
   - Simply double-click the downloaded executable file to run WaveWeaver.

### Using WaveWeaver

1. **Load an Audio File:**
   - Click the "Load Audio File" button and select your audio file.

2. **Adjust Silence Threshold:**
   - Use the "Silence Threshold (dB)" slider to adjust the threshold for detecting pauses in the audio.

3. **Preview and Adjust Clips:**
   - View the waveform and adjust the cut points if necessary.
   - Select clips from the list to rename and categorize them.

4. **Save Clips:**
   - Enter the unit name and select the command type.
   - Click "Save Selected Chunk" to save the clip to the appropriate folder.

## Creating a Standalone Executable (For Developers)

If you wish to build the executable yourself, follow these steps:

1. **Install PyInstaller:**
   ```bash
   pip install pyinstaller
   ```

2. **Create the Executable:**
   ```bash
   pyinstaller --onefile --windowed waveweaver.py
   ```

3. **Locate the Executable:**
   - The executable will be located in the `dist` directory within your project folder.

### Example Project Structure

```
WaveWeaver/
│
├── waveweaver.py
├── LICENSE
├── README.md
└── ...
```

## Contributing

Contributions are welcome! Please fork the repository and create a pull request with your improvements.

### Reporting Issues

If you encounter any issues, please open an issue on GitHub with detailed information.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

- Thanks to the open-source community for their valuable tools and resources.
- Special thanks to the contributors for their time and effort in improving this project.

---