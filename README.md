# Gestionador de archivos

Aplicación de escritorio para ordenar archivos. La implementación actual está centrada en música; las carpetas para videos, imágenes, documentos y otras categorías forman parte del diseño futuro y todavía no se procesan.

El lema de la aplicación es **“Tus carpetas ordenadas en un clic. Olvídate de limpiar a mano”.** Su identidad visual usa la mascota suministrada y la interfaz de referencia: fondo casi negro verdoso, paneles carbón, acentos verde lima y menta, duplicados ámbar e incidencias coral.

## Funciones actuales

- Escanea una carpeta y sus subcarpetas para encontrar audio MP3, FLAC, M4A, AAC, OGG, WAV, WMA y OPUS.
- Muestra canción, artista, álbum, género, formato y duración; indica el avance del análisis con una barra y porcentaje.
- Distingue copias exactas mediante SHA-256 de posibles repetidos con artista, canción y álbum coincidentes.
- Permite filtrar todas las canciones, repetidas y canciones con etiquetas ausentes.
- Permite cambiar entre lista y cuadrícula; las tarjetas muestran la carátula incrustada cuando existe.
- En cuadrícula, seleccionar un archivo actualiza únicamente su tarjeta, sin volver a dibujar la biblioteca.
- La cuadrícula crea sus tarjetas por filas cuando se acerca el desplazamiento y conserva las ya creadas para no reconstruirlas al volver.
- Las categorías de video, imágenes, documentos y archivos sin clasificar se pueden seleccionar y muestran un estado vacío mientras no estén habilitadas.
- La tarjeta «Regla de orden» abre ajustes de vista, orden y reglas de organización.
- Previsualiza la organización antes de confirmar y permite incluir el género como criterio opcional.
- Ofrece simulación sin cambios y modo seguro de copia, que conserva intactos los originales.
- La simulación permite buscar operaciones, filtrar música, consultar estados y copiar el reporte.
- Envía las canciones sin metadatos a la carpeta de artistas desconocidos cuando se activa esa regla.
- Para copias exactas permite conservarlas, mover las copias adicionales al árbol musical o enviarlas a la Papelera de Windows.
- Informa los errores de lectura y organización en la interfaz.

## Árbol de organización

La música se organiza dentro de la carpeta elegida, con esta estructura predeterminada:

```text
Carpeta_elegida/
└── Musica_y_Audio/
    ├── Artistas/
    │   ├── Nombre_Artista/
    │   │   ├── Nombre_Album/
    │   │   └── Canciones_Sueltas/
    │   └── Artistas_Desconocidos/
    │       └── Canciones_Sueltas/
    └── Duplicados/
```

Las canciones sin álbum quedan en `Canciones_Sueltas`; las canciones sin artista se agrupan en `Artistas_Desconocidos`. Los duplicados que se mueven se guardan en `Musica_y_Audio\Duplicados`, que se excluye de análisis posteriores. Las opciones de género o de organización por artista/álbum pueden añadir o cambiar subcarpetas.

## Categorías previstas

El árbol completo está guardado en [`docs/estructura_archivos.txt`](docs/estructura_archivos.txt), a partir del documento de diseño. `app/file_types.py` registra extensiones para listas de reproducción, proyectos de edición, descargas incompletas, videos, subtítulos, imágenes, diseños, documentos, comprimidos, instaladores, código y datos. Por ahora solo la categoría **music** está activa: el resto de archivos no se lee, mueve ni elimina.

```text
Organizador_Archivos/
├── Musica_y_Audio/
│   ├── Artistas/
│   ├── Listas_y_Proyectos/
│   │   ├── Playlists/
│   │   └── Proyectos_Edicion/
│   ├── Duplicados/
│   └── Archivos_No_Validos/
│       ├── Corruptos_o_Danados/
│       ├── Sin_Extension/
│       └── Incompletos/
├── Videos_y_Peliculas/
│   ├── Clips_y_Videos/
│   └── Guiones_y_Subtitulos/
├── Imagenes_y_Disenos/
│   ├── Fotos_e_Imagenes/
│   ├── Vectores_y_Disenos/
│   └── Capturas_de_Pantalla/
├── Documentos_y_Libros/
│   ├── PDF/
│   ├── Texto_y_Notas/
│   ├── Ofimatica/
│   └── Libros_Electronicos/
├── Comprimidos_e_Instaladores/
│   ├── Archivos_ZIP_y_RAR/
│   └── Instaladores/
├── Codigo_y_Proyectos/
│   ├── Scripts/
│   └── Bases_de_Datos/
└── Varios_Sin_Clasificar/
```

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

- Ejecutable y sus dependencias: `dist\GestionadorDeArchivos-<versión>\`
- Ejecutable: `dist\GestionadorDeArchivos-<versión>\GestionadorDeArchivos-<versión>.exe`
- Instalador: `dist\GestionadorDeArchivos-Setup-<versión>.exe`
- Archivos temporales de compilación: `build\GestionadorDeArchivos\`

`dist` conserva únicamente el ejecutable y el instalador de la versión actual; al completar una compilación correcta, el script elimina las salidas antiguas de esta aplicación. El ejecutable queda en su carpeta versionada y el instalador directamente en `dist`, sin subcarpeta.

Antes de distribuir el instalador, pruébalo en un Windows que no tenga Python instalado. Windows SmartScreen o algunos antivirus pueden advertir sobre ejecutables nuevos sin firma digital.

## Dependencias

- `customtkinter`: interfaz gráfica.
- `mutagen`: lectura de metadatos de audio.
- `Pillow`: visualización de carátulas incrustadas en la cuadrícula.
- `Send2Trash`: envío seguro de copias exactas a la Papelera.
- PyInstaller e Inno Setup se usan únicamente para generar el instalador de Windows.

## Alcance y precauciones

- Actualmente solo se gestionan archivos de audio dentro de la carpeta elegida. Videos, documentos e imágenes quedan intactos.
- `Musica_y_Audio\Duplicados` no se vuelve a incluir al analizar la carpeta elegida.
- La detección identifica copias idénticas byte por byte, no canciones que suenen igual pero estén codificadas de forma distinta.
- La organización mueve los archivos originales. Revisa la vista previa y conserva una copia de seguridad.

## Pruebas

```powershell
python -m unittest discover -s tests -v
```
