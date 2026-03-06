' ============================================
' Kompres File - Silent Launcher
' Menjalankan compressor.py tanpa console window
' ============================================
Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName) & "\"
pyScript = scriptDir & "compressor.py"

If WScript.Arguments.Count > 0 Then
    arg = WScript.Arguments(0)
    shell.Run "pythonw """ & pyScript & """ """ & arg & """", 0, False
End If
