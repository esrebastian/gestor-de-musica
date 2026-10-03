import sys

from app.gui import GestionadorArchivosApp

if __name__ == "__main__":
    if sys.platform == "win32":
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "ZombieFiles.GestionadorDeArchivos"
        )
    app = GestionadorArchivosApp()
    app.mainloop()
