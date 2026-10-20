# CLAUDE.md — documento de tesis (LaTeX)

Esta carpeta es la **única versión vigente** del informe de tesis. Es un proyecto LaTeX con la
clase `tesisulasalle` (esquema oficial de informe de investigación tecnológica). El mapa del repositorio está en
`../CLAUDE.md`; el estado de cada capítulo, en `../AVANCE.md`.

## Estructura: un archivo por parte, se edita uno a la vez

| Archivo | Contenido |
|---|---|
| `main.tex` | Portada y `\input` de cada parte. Solo se toca para cambiar datos de portada o añadir un archivo. |
| `preambulo.tex` | Paquetes y macros propias (`\pendiente{}`, pgfgantt, landscape). |
| `tesisulasalle.cls` | Clase de la universidad. Los autores la ajustan a mano; no la reescribas. |
| `capitulos/00-preliminares.tex` | Dedicatoria, agradecimientos, índices, siglas, resumen, abstract, palabras clave. |
| `capitulos/01-problematica.tex` | Capítulo I: contexto, antecedentes y estado del arte, definición del problema. |
| `capitulos/02-planteamiento.tex` | Capítulo II: fundamentos, objetivos, justificación, viabilidad, limitaciones. |
| `capitulos/03-metodologia.tex` | Capítulo III: marco de trabajo, requisitos, propuesta, arquitectura, plan, evaluación. |
| `capitulos/04-conclusiones.tex` | Conclusiones (se redactan al cierre del Sprint 6). |
| `capitulos/referencias.tex` | `thebibliography` en formato IEEE; se cita con `\cite{refN}`. |
| `anexos/A-fichas-lectura.tex` | Fichas de lectura crítica de los 24 documentos seleccionados. |
| `anexos/B-matriz-trazabilidad.tex` | Matriz historia → componente → clase → código → tabla. |
| `figuras/` | Imágenes incluidas (copias de `../agente/docs/diagramas/`; si cambia un diagrama, vuelve a copiar el PNG). |
| `plantilla/` | Esquema oficial `.docx` del que deriva la clase. Solo referencia. |
| `compilar.ps1` | Compila en Windows con MiKTeX hacia `build/`. |
| `build/` | Salidas de compilación (ignorada por git). |

**Para una tarea de tesis, abre solo el capítulo afectado.** No cargues `anexos/` ni `referencias.tex` salvo que la
tarea sea sobre ellos: son los archivos más largos y casi nunca cambian.

## Reglas de edición

1. **Se compila en local; el entregable es `build/main.pdf`.** Toda salida va a `build/` (ignorada por git): nunca
   generes `.aux`, `.log` ni `.pdf` junto a los `.tex`.
   - En Windows (el usuario, y la forma oficial): `.\compilar.ps1` (MiKTeX + latexmk).
   - Desde el shell Linux de Claude sobre este equipo: `cd Tesis-Doc && latexmk -pdf -interaction=nonstopmode
     -halt-on-error -outdir=build main.tex`. Esa VM tiene TeX Live sin `babel-spanish`; si falla con
     *Unknown option 'spanish'*, instálalo en el árbol de usuario con
     `mkdir -p ~/texmf/tex/generic && tar xzf build/babel-spanish.tgz -C ~/texmf/tex/generic` (el `.tgz` queda en
     `build/`; si no está, pídeselo al contenedor que sí tiene TeX Live completo). Tampoco tiene `newtxtext` ni
     `carlito`: la clase cae a `mathptmx`, así que ese PDF sirve para verificar, no como entregable: el entregable se
     genera en Windows con MiKTeX, que sí tiene todas las fuentes.
   - Después de compilar, revisa `build/main.log`: líneas que empiezan con `!` son errores; `Overfull \hbox` en tablas
     indica una celda que no cabe.
2. Cada `.tex` de `capitulos/` y `anexos/` empieza con una cabecera que `../scripts/avance.py` lee:
   ```
   % titulo: Capítulo II – Planteamiento del proyecto
   % estado: borrador        (pendiente | borrador | revisado | final)
   % actualizado: 2026-10-19
   ```
   Al editar un archivo, actualiza `estado` y `actualizado`.
3. Lo que falta se marca con `\pendiente{qué falta}` (sale en rojo en el PDF y se cuenta en `AVANCE.md`). Al resolverlo,
   quita la marca.
4. **La tesis describe el software, no lo redefine.** El Capítulo III resume y enlaza `../agente/specs/`. Si cambia una
   spec, se corrige la tesis; si la tesis contradice una spec, prevalece la spec. Las cifras de avance se copian al
   Capítulo III solo al cierre del Sprint 6; antes, se mantienen en `../AVANCE.md`.
5. Citas IEEE: `\cite{refN}` apunta a `\bibitem{refN}` en `capitulos/referencias.tex`. Una referencia nueva se añade al
   final de `thebibliography` con el siguiente número libre; LaTeX numera por orden de aparición en esa lista.
6. Tablas: `longtable` con `booktabs`, anchos en fracción de `\textwidth`, `\caption{}\label{tab:C-N}` como primera fila
   (C = capítulo, N = correlativo). Se referencian con `Tabla~\ref{tab:C-N}`. Figuras: entorno `figure[H]` con
   `\label{fig:nombre}`. Tablas anchas (≥ 6 columnas) van en `\begin{landscape}`.
7. Texto en español, con los términos técnicos en inglés en cursiva (`\emph{walking skeleton}`). Rutas y nombres de
   código en `\texttt{}`.
8. No crees otros borradores (Word, Google Docs, Markdown). Si llega material nuevo, intégralo aquí y regístralo en
   `README.md` → "Registro de sincronización" con el siguiente código S-nn.

## Observaciones heredadas del borrador original

Las decisiones tomadas al convertir el borrador `Tesis2026.pdf` (19-oct-2026) y lo que quedó por resolver están en
`README.md` de esta carpeta. Léelo antes de rehacer una sección completa, para no deshacer una decisión ya tomada.
