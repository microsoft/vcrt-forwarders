using System;
using System.Collections.Generic;
using System.IO;
using System.Runtime.InteropServices;
using UnityEditor;
using UnityEngine;

[InitializeOnLoad]
public class InitVCRTForwarders
{
    [DllImport("kernel32.dll", SetLastError = true)]
    static extern IntPtr LoadLibraryExW([MarshalAs(UnmanagedType.LPWStr)] string fileName, IntPtr fileHandle, uint flags);

    [DllImport("kernel32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    static extern bool FreeLibrary(IntPtr moduleHandle);

    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    static extern int AddDllDirectory(string lpPathName);

    const uint LOAD_LIBRARY_SEARCH_USER_DIRS = 0x00000400;

    const string moduleName = "vcruntime140_app.dll";

    static InitVCRTForwarders()
    {
        IntPtr modulePtr = LoadLibraryExW(moduleName, IntPtr.Zero, LOAD_LIBRARY_SEARCH_USER_DIRS);
        if (modulePtr != IntPtr.Zero)
        {
            // DLL search paths already configured in this process; nothing more to do.
            FreeLibrary(modulePtr);
            return;
        }

        List<string> searchFolders = new List<string>()
        {
            Application.dataPath,                                       // Assets folder
            Path.GetFullPath(Path.Combine("Library", "PackageCache")),  // Library\PackageCache folder
            Path.GetFullPath("Packages")                                // Pacakges folder
        };

        // Find a representative VCRTForwarders binary - there should be only one.
        string dllDirectory = string.Empty;
        for (int i = 0; i < searchFolders.Count; i++)
        {
            string[] files = Directory.GetFiles(searchFolders[i], moduleName, SearchOption.AllDirectories);
            if (files.Length == 0) { continue; }

            if (files.Length == 1)
            {
                dllDirectory = files[0];
                break;
            }

            Debug.LogError(string.Format("Failed to find single asset for {0}; found {1} instead!", moduleName, files.Length));
            return;
        }

        if (string.IsNullOrEmpty(dllDirectory))
        {
            Debug.LogError($"Failed to find {moduleName}.");
            return;
        }
            
        dllDirectory = dllDirectory.Replace('/', '\\');
        if (AddDllDirectory(dllDirectory) == 0)
        {
            Debug.LogError(string.Format("Failed to set DLL directory {0}: Win32 error {1}", dllDirectory, Marshal.GetLastWin32Error()));
            return;
        }

        Debug.Log(string.Format("Added DLL directory {0} to the user search path.", dllDirectory));
    }
}
