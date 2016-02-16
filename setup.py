import sys
from cx_Freeze import setup, Executable

setup(
    name = "Oscilloscope",
    executables = [Executable("Oscilloscope.py", base = "Win32GUI", targetName="Oscilloscope.exe", icon="Media/icon.ico")],
	options = {'build_exe': {'include_files': ['Media/about.png', 'Media/color.png', 'Media/exit.png', 'Media/icon.png', 'Media/open.png']}})