using System;
using System.IO;
using System.Runtime.CompilerServices;
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
    static extern IntPtr GetModuleHandleW(string moduleName);

    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    static extern IntPtr AddDllDirectory(string lpPathName);

    const uint LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR = 0x00000100;
    const uint LOAD_LIBRARY_SEARCH_SYSTEM32 = 0x00000800;

    const string moduleName = "vcruntime140_app.dll";

    static InitVCRTForwarders()
    {
        var initializerPath = GetInitializerPath();
        if (!Path.IsPathRooted(initializerPath))
        {
            Debug.LogError("Failed to determine the VCRTForwarders initializer's full path.");
            return;
        }

        var dllDirectory = Path.GetFullPath(Path.Combine(Path.GetDirectoryName(initializerPath), "..", "x64"));
        var modulePath = Path.Combine(dllDirectory, moduleName);
        if (GetModuleHandleW(modulePath) != IntPtr.Zero)
        {
            // The package's module is already loaded in this editor process.
            return;
        }

        IntPtr modulePtr = LoadLibraryExW(modulePath, IntPtr.Zero,
            LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR | LOAD_LIBRARY_SEARCH_SYSTEM32);
        if (modulePtr == IntPtr.Zero)
        {
            Debug.LogError(string.Format("Failed to load {0}: Win32 error {1}", modulePath, Marshal.GetLastWin32Error()));
            return;
        }

        if (AddDllDirectory(dllDirectory) == IntPtr.Zero)
        {
            var error = Marshal.GetLastWin32Error();
            FreeLibrary(modulePtr);
            Debug.LogError(string.Format("Failed to set DLL directory {0}: Win32 error {1}", dllDirectory, error));
            return;
        }

        // Keep the module loaded across domain reloads instead of probing other DLL directories.
        Debug.Log(string.Format("Added DLL directory {0} to the user search path.", dllDirectory));
    }

    static string GetInitializerPath([CallerFilePath] string path = "")
    {
        return path;
    }
}
