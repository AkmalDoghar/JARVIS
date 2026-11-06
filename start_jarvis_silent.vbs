' ======================================================================
' JARVIS AI ASSISTANT - SILENT BACKGROUND BOOTSTRAPPER (Phase 10)
' Launches JARVIS Master Desktop Suite completely hidden on Windows boot
' with NO console windows or flashing command prompts.
' ======================================================================
Option Explicit
Dim FSO, WshShell, ScriptDir, PythonwPath, DesktopScript

Set FSO = CreateObject("Scripting.FileSystemObject")
ScriptDir = FSO.GetParentFolderName(WScript.ScriptFullName)
PythonwPath = ScriptDir & "\.venv\Scripts\pythonw.exe"
DesktopScript = ScriptDir & "\start_jarvis_desktop.py"

If Not FSO.FileExists(PythonwPath) Then
    PythonwPath = "pythonw.exe"
End If

Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = ScriptDir

' Run completely hidden in the background (0 = hide window, False = don't wait)
WshShell.Run Chr(34) & PythonwPath & Chr(34) & " " & Chr(34) & DesktopScript & Chr(34), 0, False

Set WshShell = Nothing
Set FSO = Nothing
