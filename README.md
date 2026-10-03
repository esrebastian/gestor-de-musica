# Gestionador de archivos

Aplicación de escritorio para analizar y organizar archivos, comenzando por bibliotecas de música. La primera versión permite escanear canciones, revisar repetidos y ordenar música por sus metadatos. La organización de videos, imágenes y documentos queda prevista para etapas posteriores; esos archivos no se modifican en esta versión.

## Funciones actuales

- Escanea una carpeta y sus subcarpetas para encontrar audio MP3, FLAC, M4A, AAC, OGG, WAV, WMA y OPUS.
- Muestra canción, artista, álbum, género y duración; indica el avance del análisis con una barra y porcentaje.
- Distingue copias exactas mediante SHA-256 de posibles repetidos con artista, canción y álbum coincidentes.
- Previsualiza la organización antes de confirmar. Puede crear la estructura `Carpeta elegida/Artista/Álbum/Canción.ext` y opcionalmente incluir el género.
- Para copias exactas permite conservarlas, mover las copias adicionales a `Repetidos` o enviarlas a la Papelera de Windows.
- Informa los errores de lectura y organización en la interfaz.
- Usa una interfaz oscura verde grisácea, con acentos verde lima y turquesa, y el icono de la aplicación.

## Compatibilidad futura

Las extensiones de video, imagen y documento ya están agrupadas en `app/file_types.py` para facilitar la incorporación de sus propios analizadores y organizadores. Por ahora solo la categoría de música está activa: escanear una carpeta no lee, organiza ni modifica los demás tipos de archivo.

## Instalar y abrir

Ejecuta `GestionadorDeArchivos-Setup-<versión>.exe` y sigue el asistente. La opción para crear un acceso directo en el Escritorio está marcada por defecto y también se agrega un acceso al menú Inicio. La aplicación se instala en el perfil del usuario y no requiere permisos de administrador.

## Ejecutar desde el código

Se requiere Python 3.11 o superior. En Windows, abre PowerShell en la carpeta del proyecto:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python main.py
```

Si PowerShell bloquea la activación del entorno:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

## Crear el instalador de Windows

La construcción se debe realizar en Windows con Python 3.11 o superior e [Inno Setup 6 o 7](https://jrsoftware.org/isinfo.php). Desde PowerShell, prepara el entorno e inicia el script:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\build_windows.ps1
```

La versión se define en `VERSION` con formato `MAJOR.MINOR.PATCH`. El script añade el icono y los metadatos al ejecutable, incluye el logotipo de la interfaz y compila el instalador. Los archivos generados son:

- Ejecutable: `dist\GestionadorDeArchivos\GestionadorDeArchivos.exe`
- Instalador: `dist\installer\GestionadorDeArchivos-Setup-<versión>.exe`

Antes de distribuir el instalador, pruébalo en un Windows que no tenga Python instalado. Windows SmartScreen o algunos antivirus pueden advertir sobre ejecutables nuevos sin firma digital.

## Dependencias

- `customtkinter`: interfaz gráfica.
- `mutagen`: lectura de metadatos de audio.
- `Send2Trash`: envío seguro de copias exactas a la Papelera.
- PyInstaller e Inno Setup se usan únicamente para generar el instalador de Windows.

## Alcance y precauciones

- Actualmente solo se gestionan archivos de audio dentro de la carpeta elegida. Videos, documentos e imágenes quedan intactos.
- La carpeta `Repetidos` no se vuelve a incluir al analizar la carpeta elegida.
- La detección identifica copias idénticas byte por byte, no canciones que suenen igual pero estén codificadas de forma distinta.
- La organización mueve los archivos originales. Revisa la vista previa y conserva una copia de seguridad.

## Pruebas

```powershell
python -m unittest discover -s tests -v
```
