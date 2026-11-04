' ======================================================================
' JARVIS AI ASSISTANT - SILENT BACKGROUND BOOTSTRAPPER (Phase 10)
' Launches JARVIS completely hidden with no flashing command prompts.
' ======================================================================
Option Explicit
Dim FSO, WshShell, ScriptDir, BatPath

Set FSO = CreateObject("Scripting.FileSystemObject")
ScriptDir = FSO.GetParentFolderName(WScript.ScriptFullName)
BatPath = ScriptDir & "\start_jarvis_all.bat"

If FSO.FileExists(BatPath) Then
    Set WshShell = CreateObject("WScript.Shell")
    WshShell.CurrentDirectory = ScriptDir
    ' Run hidden (window style 0, do not wait for completion)
    WshShell.Run Chr(34) & BatPath & Chr(34), 0, False
    Set WshShell = Nothing
End If

Set FSO = Nothing
