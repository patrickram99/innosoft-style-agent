# CLAUDE.md — mapa del repositorio

Tesis de Ingeniería de Software (Universidad La Salle, 2026): *Agente de IA de sugerencias estilísticas integrado con
OJS*, caso de estudio revista Innosoft. El repositorio tiene **dos productos** con reglas distintas, cada uno con su
propio `CLAUDE.md`. Este archivo solo dice dónde está cada cosa; no lo cargues todo: entra a la carpeta que toque.

| Carpeta | Qué es | Reglas en |
|---|---|---|
| `AVANCE.md` | **Fuente única del avance** del software y de la tesis. Léelo primero. | — |
| `agente/` | El software: FastAPI + PyMuPDF + reglas YAML, specs SDD, pruebas, Docker, Excel RICE, catálogo de requisitos. Equivale a `innosoft-style-agent/` de `agente/specs/00-producto.md` §13. | `agente/CLAUDE.md` |
| `Tesis-Doc/` | El documento de tesis en LaTeX (clase `tesisulasalle`), un `.tex` por capítulo. Se compila en local con MiKTeX (`Tesis-Doc\compilar.ps1`); el entregable es `Tesis-Doc/build/main.pdf`. | `Tesis-Doc/CLAUDE.md` |
| `scripts/avance.py` | Regenera el bloque automático de `AVANCE.md` leyendo `agente/` y `Tesis-Doc/`. | este archivo |

## Cómo trabajar aquí sin cargar contexto de más

1. Lee `AVANCE.md` (sección **Ahora** + tablero). Ahí está el sprint en curso, los bloqueos y los próximos pasos.
2. Decide si la tarea es de **código** (→ `agente/CLAUDE.md`) o de **tesis** (→ `Tesis-Doc/CLAUDE.md`) y lee solo ese.
3. Abre únicamente los archivos que la tarea necesita: una spec `US-nn.md`, un capítulo `.tex`, un módulo. No leas
   todas las specs ni todos los capítulos "para tener contexto": `AVANCE.md` ya resume su estado.
4. Al terminar cualquier cambio que afecte estados (spec implementada, capítulo revisado, regla nueva), ejecuta
   `python scripts/avance.py` desde la raíz y, si corresponde, actualiza a mano la sección **Ahora** de `AVANCE.md`.

## Precedencia cuando algo se contradice

`agente/specs/00-producto.md` > `agente/specs/US-nn.md` > `agente/catalogo_requisitos_innosoft.md` > tesis (`Tesis-Doc/`).
La tesis describe el software; nunca lo redefine. Si una decisión no está en ninguna spec, **pregunta**, no la inventes.

## Reglas comunes

- Idioma: documentación, specs, mensajes al usuario y tesis en español; código e identificadores en inglés.
- Entorno de desarrollo Windows: comandos en PowerShell. Nada de scripts solo-bash.
- No hagas `git push` ni crees repositorios remotos sin que te lo pidan. Los commits se hacen cuando el usuario lo pida
  o cuando `agente/CLAUDE.md` lo indique (cierre de historia).
- `agente/muestras/` tiene manuscritos reales con datos personales (Ley N.º 29733): nunca se copian a pruebas, commits,
  logs, prompts ni a la tesis.
- No crees borradores paralelos (PDF, Google Docs, copias "v2"). Si aparece uno, se integra en `Tesis-Doc/` y se anota
  en su registro de sincronización.
