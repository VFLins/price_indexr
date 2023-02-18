Set WinScriptHost = CreateObject("WScript.Shell")
scriptdir = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
WinScriptHost.Run Chr(34) & scriptdir & "/routines/caller.bat" & Chr(34), 0
Set WinScriptHost = Nothing