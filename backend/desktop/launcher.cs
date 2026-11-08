using System;
using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;

namespace JarvisDesktop {
    static class Program {
        [DllImport("shell32.dll", SetLastError = true)]
        private static extern void SetCurrentProcessExplicitAppUserModelID([MarshalAs(UnmanagedType.LPWStr)] string AppID);

        [STAThread]
        static void Main() {
            try {
                SetCurrentProcessExplicitAppUserModelID("JARVIS.Personal.AI.Assistant");
            } catch {}

            string projectRoot = @"D:\projects\JARVIS";
            string pythonw = Path.Combine(projectRoot, @".venv\Scripts\pythonw.exe");
            if (!File.Exists(pythonw)) {
                pythonw = "pythonw.exe";
            }
            string desktopScript = Path.Combine(projectRoot, "start_jarvis_desktop.py");

            ProcessStartInfo psi = new ProcessStartInfo {
                FileName = pythonw,
                Arguments = "\"" + desktopScript + "\"",
                WorkingDirectory = projectRoot,
                CreateNoWindow = true,
                UseShellExecute = false
            };

            try {
                Process.Start(psi);
            } catch {}
        }
    }
}
