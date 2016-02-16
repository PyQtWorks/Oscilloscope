import sys
from cx_Freeze import setup, Executable

setup(
    name = "Oscilloscope",
    executables = [Executable("Oscilloscope.py", base = "Win32GUI", targetName="Oscilloscope.exe", icon="icon.ico")],
	options = {'build_exe': {'include_files': ['about.png', 'color.png', 'exit.png', 'icon.png', 'open.png']}})