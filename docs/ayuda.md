# Ayuda en pantalla — cómo mantenerla

El menú **Ayuda** (barra superior) ofrece:

- **Ayuda de este módulo (F1)**: abre el tema del módulo que está a la vista.
- **Índice de ayuda… (Ctrl+F1)**: lista de todos los temas con buscador (no distingue tildes ni mayúsculas).

## Dónde está el contenido

Un archivo Markdown por módulo en `assets/ayuda/<clave>.md`. La **clave** es la misma que usa
`MainWindow.load_module("clave", …)`. Vive en `assets` para que se empaquete con la aplicación
sin tocar los `.spec`.

Para **editar** la ayuda basta con cambiar el `.md`; no hace falta programar nada.

## Manual de usuario en PDF

El manual `docs/Manual_de_Usuario_ItalosManager.pdf` **se genera desde estos mismos archivos**, así la
ayuda en pantalla y el manual nunca se contradicen:

```
python generar_manual.py
```

Vuelva a ejecutarlo después de cambiar cualquier `.md` (o al agregar un módulo) y publique el PDF nuevo.
Usa portada, índice con números de página, tablas, listas, cuadros de aviso y enlaces entre capítulos.
El generador antiguo (texto escrito a mano, con datos que no coinciden con el programa) está en
`docs/legacy/` solo como referencia obsoleta.

## Cómo mantener la documentación fiel al programa

- Describa solo lo que el programa **hace hoy**; lo que todavía no existe se anota como pendiente, no como si funcionara.
- Al cambiar un botón, campo o comportamiento, actualice **en el mismo cambio** el tema de ayuda, la guía de `docs/` del
  módulo y el `README.md` si lo menciona, y regenere el manual PDF (`python generar_manual.py`).
- Los nombres de botones y pestañas se escriben tal como aparecen en pantalla, entre **negritas**.

## Agregar un módulo nuevo

1. Cree `assets/ayuda/<clave>.md` (empiece con un título `# …`).
2. Agregue `("<clave>", "Título en el índice")` a `TEMAS` en `app/utils/ayuda.py`, en el orden del menú lateral.

Los tests (`tests/test_ayuda.py`) fallan si un módulo del menú lateral no tiene ayuda, si un archivo no está
registrado o si un enlace interno apunta a un tema que no existe.

## Estructura recomendada de cada tema

Para qué sirve → **Antes de empezar** (qué debe estar cargado) → pasos numerados de las tareas comunes →
consejos / problemas frecuentes → enlaces a módulos relacionados.

Enlaces entre temas: `[texto](ayuda:clave)`. Enlaces externos se abren en el navegador.

## Código

- `app/utils/ayuda.py`: lista de temas, lectura de archivos y búsqueda (sin Qt).
- `app/views/ayuda_dialog.py`: ventana (índice + buscador + visor Markdown), no modal.
- `app/views/main_window.py`: menú Ayuda, atajos y seguimiento del módulo actual.
