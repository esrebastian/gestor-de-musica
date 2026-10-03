# Gestor de Música

Aplicación de escritorio para analizar y organizar una biblioteca musical. Después de instalarla, se abre desde el acceso directo del Escritorio o del menú Inicio, sin terminal y sin instalar Python en el equipo del usuario.

## Funciones

- Escanea la carpeta elegida y sus subcarpetas; muestra canción, artista, álbum, género y duración en una tabla.
- Lee metadatos con Mutagen y analiza archivos MP3, FLAC, M4A, AAC, OGG, WAV, WMA y OPUS.
- Distingue copias exactas con SHA-256 de posibles repetidos que comparten artista, canción y álbum, pero tienen contenido distinto.
- Previsualiza la organización antes de confirmar. Por defecto crea `Carpeta elegida/Artista/Álbum/Canción.ext`; también permite añadir género.
- Para copias exactas permite no hacer nada, mover las copias adicionales a `Repetidos` o enviarlas a la Papelera de Windows. Conserva una copia por grupo y pide confirmación antes de actuar.
- Muestra los errores de lectura y organización en la interfaz gráfica.

## Instalar y abrir

Ejecuta `GestorDeMusica-Setup-<versión>.exe` y sigue el asistente (por ejemplo, `GestorDeMusica-Setup-1.0.0.exe`). La opción para crear un acceso directo en el Escritorio está marcada por defecto y también se agrega un acceso al menú Inicio. Se instala en el perfil del usuario y no requiere permisos de administrador.

## Ejecutar desde el código

Se requiere Python 3.11 o superior.

En Windows, abre PowerShell en la carpeta del proyecto y ejecuta:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python main.py
```

Si PowerShell bloquea la activación del entorno, puedes ejecutar los comandos del entorno directamente sin activarlo:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

En Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

## Crear el instalador de Windows

La aplicación instalada se abre desde su acceso directo del Escritorio o del menú Inicio, sin consola y sin requerir Python en el equipo del usuario. PyInstaller no es un compilador cruzado: el instalador se debe construir en Windows.

La construcción se hace en Windows. En el equipo de construcción instala Python 3.11 o superior e [Inno Setup 6 o 7](https://jrsoftware.org/isinfo.php). Después, en PowerShell, desde la carpeta del proyecto, prepara el entorno e inicia el script:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\build_windows.ps1
```

La versión del programa se define una sola vez en `VERSION`, usando el formato `MAJOR.MINOR.PATCH` (por ejemplo, `1.0.0`): incrementa `MAJOR` para cambios incompatibles, `MINOR` para funciones nuevas compatibles y `PATCH` para correcciones compatibles. Actualiza ese archivo para cada lanzamiento; el script utiliza el mismo valor en los metadatos del ejecutable y del instalador. El script instala PyInstaller, empaqueta CustomTkinter con sus recursos y compila un instalador sin consola. El instalador versionado se genera en `dist\installer\GestorDeMusica-Setup-<versión>.exe`, por ejemplo `dist\installer\GestorDeMusica-Setup-1.0.0.exe`. Al ejecutarlo, instala la aplicación en el perfil del usuario, ofrece crear el acceso directo del Escritorio (marcado por defecto) y añade un acceso al menú Inicio. No hace falta conceder permisos de administrador.

Antes de distribuir el instalador, pruébalo en un Windows que no tenga Python instalado. Comprueba que abre desde el acceso directo y que funcionan el análisis, la consulta de repetidas y la organización. Windows SmartScreen o algunos antivirus pueden advertir sobre ejecutables nuevos sin firma digital.

## Dependencias

Las dependencias de ejecución están en `requirements.txt`:

- `customtkinter`: interfaz gráfica.
- `mutagen`: lectura de metadatos de audio.
- `Send2Trash`: envío seguro de copias exactas a la Papelera.

PyInstaller e Inno Setup solo se necesitan para construir el instalador, no para usar la aplicación instalada.

## Estado y limitaciones

- Solo se gestionan archivos de audio dentro de la carpeta elegida; otros tipos de archivo no se mueven ni se eliminan.
- Los archivos que no se puedan leer aparecen en la ventana de incidencias. Antes de organizar se revisan permisos básicos; los fallos durante la ejecución se informan como operación parcial.
- La carpeta `Repetidos` no vuelve a incluirse al analizar la carpeta elegida.
- La detección identifica archivos idénticos byte por byte, no canciones que suenen igual pero estén codificadas de forma distinta.
- La organización mueve los archivos originales a la jerarquía elegida. Revisa la vista previa y conserva una copia de seguridad.

## Pruebas

Ejecuta las pruebas unitarias con:

```powershell
python -m unittest discover -s tests -v
```
