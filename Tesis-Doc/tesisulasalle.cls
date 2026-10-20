%% ============================================================================
%% tesisulasalle.cls
%% Clase LaTeX que reproduce el "Anexo - Esquema del Informe de Investigación
%% Tecnológica (ByP)" de la Escuela Profesional de Ingeniería de Software.
%%
%% Formato tomado del .docx original:
%%   - Papel A4; márgenes sup./inf. 2,5 cm, izq./der. 3 cm; pie a 1,25 cm.
%%   - Portada: logo arriba a la izquierda (5,19 x 2,40 cm); textos centrados
%%     en Calibri 14 pt negrita; sin número de página.
%%   - Títulos de nivel 1: Times New Roman 14 pt negrita, centrados, negro,
%%     24 pt antes. Cada uno inicia en página nueva.
%%   - Subtítulos: Times New Roman 12 pt negrita, alineados a la izquierda,
%%     sin numeración (opción `numerado` para numerarlos 1.1, 1.2...).
%%   - Sub-subtítulos (Objetivo General / Específicos): lista "a.", "b." con
%%     sangría izquierda de 1,27 cm y francesa de 0,635 cm.
%%   - Cuerpo: Times New Roman 12 pt, justificado, interlineado 1,5,
%%     10 pt de espacio después de cada párrafo, sin sangría de primera línea.
%%   - Número de página: abajo a la derecha (Calibri 11 pt), numeración
%%     arábiga continua desde la portada (la portada cuenta como página 1).
%%
%% Opciones de clase:
%%   numerado  -> numera las secciones (1.1, 1.2, ...) como en una tesis clásica.
%%   Cualquier otra opción se pasa a la clase `report`.
%%
%% Compatible con pdfLaTeX (recomendado en Overleaf), XeLaTeX y LuaLaTeX.
%% ============================================================================
\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{tesisulasalle}[2026/10/19 v1.0 Esquema Informe de Investigacion Tecnologica (ByP)]

% ---------------------------------------------------------------------------
% Opciones
% ---------------------------------------------------------------------------
\newif\ifulsl@numerado \ulsl@numeradofalse
\DeclareOption{numerado}{\ulsl@numeradotrue}
\DeclareOption*{\PassOptionsToClass{\CurrentOption}{report}}
\ProcessOptions\relax

\LoadClass[12pt,a4paper,oneside]{report}

% ---------------------------------------------------------------------------
% Motor, codificación y fuentes
%   Cuerpo  -> Times New Roman  (newtxtext / TeX Gyre Termes)
%   Portada -> Calibri          (Carlito, métricamente idéntica a Calibri)
% ---------------------------------------------------------------------------
\RequirePackage{iftex}
\ifPDFTeX
  \RequirePackage[T1]{fontenc}
  \RequirePackage[utf8]{inputenc}
  \IfFileExists{newtxtext.sty}{%
    \RequirePackage{newtxtext}%
    \RequirePackage{newtxmath}%
  }{%
    \RequirePackage{mathptmx}%
  }
  \IfFileExists{carlito.sty}{%
    \RequirePackage{carlito}% fija \sfdefault = Carlito
  }{}
  \newcommand*\ulsl@calibri{\sffamily}
\else
  \RequirePackage{fontspec}
  \IfFontExistsTF{TeX Gyre Termes}
    {\setmainfont{TeX Gyre Termes}}
    {\setmainfont{Latin Modern Roman}}
  \IfFontExistsTF{Carlito}
    {\newfontfamily\ulsl@carlitofont{Carlito}}
    {\let\ulsl@carlitofont\sffamily}
  \newcommand*\ulsl@calibri{\ulsl@carlitofont}
\fi

% Idioma: español (principal) e inglés (para el Abstract)
\RequirePackage[english,spanish,es-tabla,es-noshorthands,es-nolists]{babel}

% ---------------------------------------------------------------------------
% Página
% ---------------------------------------------------------------------------
\RequirePackage[a4paper,
  top=2.5cm, bottom=2.5cm, left=3cm, right=3cm,
  headheight=14pt, headsep=0.5cm,
  footskip=1.25cm]{geometry}

% Interlineado 1,5 de Word con Times 12 pt  ->  ~20,7 pt entre líneas.
% (\setstretch{1.43} sobre el \baselineskip de 14,5 pt de LaTeX).
\RequirePackage{setspace}
\setstretch{1.43}

% Párrafos: justificados, sin sangría, 10 pt después (estilo Normal del .docx)
\setlength{\parindent}{0pt}
\setlength{\parskip}{10pt plus 2pt minus 1pt}

% ---------------------------------------------------------------------------
% Paquetes de uso general
% ---------------------------------------------------------------------------
\RequirePackage{graphicx}
\RequirePackage{xcolor}
\RequirePackage{etoolbox}
\RequirePackage{enumitem}
\RequirePackage{booktabs}
\RequirePackage{array}
\RequirePackage{longtable}
\RequirePackage{float}
\RequirePackage{chngcntr}
\RequirePackage[nottoc]{tocbibind} % Índices de tablas/figuras y Referencias en el Índice General
\RequirePackage{titlesec}
\RequirePackage{titletoc}
\RequirePackage{fancyhdr}
\RequirePackage[font=small,labelfont=bf,labelsep=period,justification=centering]{caption}

% ---------------------------------------------------------------------------
% Nombres de los índices y secciones (igual que en el .docx)
% ---------------------------------------------------------------------------
\addto\captionsspanish{%
  \renewcommand{\contentsname}{Índice General}%
  \renewcommand{\listtablename}{Índice de Tablas}%
  \renewcommand{\listfigurename}{Índice de Figuras}%
  \renewcommand{\bibname}{Referencias}%
  \renewcommand{\refname}{Referencias}%
  \renewcommand{\chaptername}{Capítulo}%
  \renewcommand{\appendixname}{Anexo}%
  \renewcommand{\tablename}{Tabla}%
  \renewcommand{\figurename}{Figura}%
}

% ---------------------------------------------------------------------------
% Numeración
%   Capítulos en romanos (Capítulo I, II, III).
%   Secciones 1.1, 1.2... (solo visibles con la opción `numerado`).
%   Sub-secciones a., b., c. (como la lista de Objetivos del .docx).
%   Tablas y figuras con numeración continua (Tabla 1, Figura 1...).
% ---------------------------------------------------------------------------
\setcounter{secnumdepth}{2}
\setcounter{tocdepth}{1}
\renewcommand{\thechapter}{\Roman{chapter}}
\renewcommand{\thesection}{\arabic{chapter}.\arabic{section}}
\renewcommand{\thesubsection}{\alph{subsection}}
\counterwithout{figure}{chapter}
\counterwithout{table}{chapter}
\counterwithout{equation}{chapter}

% ---------------------------------------------------------------------------
% Títulos
% ---------------------------------------------------------------------------
\newcommand*\ulsl@hUno{\normalfont\bfseries\fontsize{14}{17}\selectfont\color{black}}
\newcommand*\ulsl@hDos{\normalfont\bfseries\fontsize{12}{14.5}\selectfont}

% Nivel 1 numerado:  "Capítulo I – Problemática del Proyecto"
\titleformat{\chapter}[block]
  {\ulsl@hUno\filcenter}
  {\chaptertitlename\ \thechapter\ --}
  {0.33em}
  {}
% Nivel 1 sin número: Dedicatoria, Resumen, Conclusiones, Referencias...
\titleformat{name=\chapter,numberless}[block]
  {\ulsl@hUno\filcenter}
  {}
  {0pt}
  {}
\titlespacing*{\chapter}{0pt}{24pt}{18pt}

% Nivel 2: "Contexto del problema", "Justificación"...
\ifulsl@numerado
  \titleformat{\section}[hang]{\ulsl@hDos}{\thesection}{1em}{}
\else
  \titleformat{\section}[hang]{\ulsl@hDos}{}{0pt}{}
\fi
\titleformat{name=\section,numberless}[hang]{\ulsl@hDos}{}{0pt}{}
\titlespacing*{\section}{0pt}{12pt plus 2pt minus 2pt}{4pt}

% Nivel 3: "a. Objetivo General", "b. Objetivos Específicos"
%   sangría izq. 1,27 cm, francesa 0,635 cm (lista numId 20 del .docx)
\titleformat{\subsection}[hang]
  {\ulsl@hDos}
  {\makebox[0.635cm][l]{\thesubsection.}}
  {0pt}
  {}
\titleformat{name=\subsection,numberless}[hang]{\ulsl@hDos}{}{0pt}{}
\titlespacing*{\subsection}{0.635cm}{8pt plus 2pt minus 2pt}{4pt}

% Nivel 4 (por si se necesita): negrita cursiva, sin número
\titleformat{\subsubsection}[hang]{\normalfont\bfseries\itshape\normalsize}{}{0pt}{}
\titlespacing*{\subsubsection}{0pt}{8pt}{2pt}

% ---------------------------------------------------------------------------
% Índice General
% ---------------------------------------------------------------------------
\titlecontents{chapter}[0pt]
  {\addvspace{6pt}\bfseries}
  {\chaptername\ \thecontentslabel\ --\ }
  {}
  {\titlerule*[0.6pc]{.}\contentspage}
\ifulsl@numerado
  \titlecontents{section}[1.5em]
    {}
    {\contentslabel{2.3em}}
    {}
    {\titlerule*[0.6pc]{.}\contentspage}
\else
  \titlecontents{section}[1.5em]
    {}
    {}
    {}
    {\titlerule*[0.6pc]{.}\contentspage}
\fi
\titlecontents{subsection}[3.5em]
  {}
  {\thecontentslabel.\ }
  {}
  {\titlerule*[0.6pc]{.}\contentspage}
\titlecontents{figure}[0pt]
  {}
  {\figurename\ \thecontentslabel.\ }
  {}
  {\titlerule*[0.6pc]{.}\contentspage}
\titlecontents{table}[0pt]
  {}
  {\tablename\ \thecontentslabel.\ }
  {}
  {\titlerule*[0.6pc]{.}\contentspage}

% ---------------------------------------------------------------------------
% Pie de página: número a la derecha, Calibri 11 pt. Sin encabezado.
% ---------------------------------------------------------------------------
\fancypagestyle{ulsl}{%
  \fancyhf{}%
  \fancyfoot[R]{{\ulsl@calibri\fontsize{11}{13}\selectfont\thepage}}%
  \renewcommand{\headrulewidth}{0pt}%
  \renewcommand{\footrulewidth}{0pt}%
}
\fancypagestyle{plain}{%  páginas que abren capítulo
  \fancyhf{}%
  \fancyfoot[R]{{\ulsl@calibri\fontsize{11}{13}\selectfont\thepage}}%
  \renewcommand{\headrulewidth}{0pt}%
  \renewcommand{\footrulewidth}{0pt}%
}
\pagestyle{ulsl}

% ---------------------------------------------------------------------------
% Datos de la portada
% ---------------------------------------------------------------------------
\newcommand*\ulsl@logo{ullasalle.png}
\newcommand*\ulsl@escuela{ESCUELA PROFESIONAL DE INGENIERÍA DE SOFTWARE}
\newcommand*\ulsl@titulo{[TITULO DE LA TESIS TECNOLÓGICA]}
\newcommand*\ulsl@autor{[Autor]}
\newcommand*\ulsl@grado{[Grado o Título a obtener]}
\newcommand*\ulsl@asesor{}
\newcommand*\ulsl@ciudad{AREQUIPA -- PERÚ}
\newcommand*\ulsl@anio{[Año]}

\newcommand*\logo[1]{\renewcommand*\ulsl@logo{#1}}
\newcommand*\escuela[1]{\renewcommand*\ulsl@escuela{#1}}
\newcommand*\titulo[1]{\renewcommand*\ulsl@titulo{#1}}
\newcommand*\autor[1]{\renewcommand*\ulsl@autor{#1}}
\newcommand*\grado[1]{\renewcommand*\ulsl@grado{#1}}
\newcommand*\asesor[1]{\renewcommand*\ulsl@asesor{#1}}
\newcommand*\ciudad[1]{\renewcommand*\ulsl@ciudad{#1}}
\newcommand*\anio[1]{\renewcommand*\ulsl@anio{#1}}

% ---------------------------------------------------------------------------
% Portada
%   Reproduce la secuencia de párrafos del .docx (Calibri, interlineado 1,15,
%   10 pt después). Cada párrafo vacío del original se convierte en un
%   espacio vertical equivalente:
%     vacío 11 pt ≈ 25 pt · vacío 14 pt ≈ 30 pt · vacío 18 pt ≈ 35 pt
% ---------------------------------------------------------------------------
\newcommand*\ulsl@vacio[1]{%
  \ifcase#1\or\vspace{25.4pt}\or\vspace{29.6pt}\or\vspace{35.3pt}\fi}

\newcommand\portada{%
  \begingroup
  \thispagestyle{empty}%
  \setstretch{1}%
  \setlength{\parskip}{10pt}%
  \setlength{\parindent}{0pt}%
  \ulsl@calibri\bfseries\fontsize{14}{19.6}\selectfont
  % Logo: alineado a la izquierda, 5,19 x 2,40 cm
  \IfFileExists{\ulsl@logo}{%
    \includegraphics[width=5.19cm,height=2.40cm,keepaspectratio]{\ulsl@logo}%
  }{%
    \fbox{\parbox[c][2.2cm][c]{5cm}{\centering\normalfont\small
      Falta el logo:\\\texttt{\ulsl@logo}}}%
  }\par
  \ulsl@vacio1\ulsl@vacio1
  {\centering \ulsl@escuela\par}
  \ulsl@vacio3
  {\centering \ulsl@titulo\par}
  \ulsl@vacio2
  {\centering \ulsl@autor\par}
  \ulsl@vacio2
  {\centering \ulsl@grado\par}
  \ulsl@vacio2\ulsl@vacio2
  {\centering Asesor: \ulsl@asesor\par}
  \ulsl@vacio3\ulsl@vacio2\ulsl@vacio2
  {\centering \ulsl@ciudad\par}
  {\centering \ulsl@anio\par}
  \endgroup
  \clearpage
}
% \maketitle como alias de \portada
\renewcommand\maketitle{\portada}

% ---------------------------------------------------------------------------
% Títulos de nivel 1 sin número que van al Índice General
% ---------------------------------------------------------------------------
\newcommand\tituloSinNumero[1]{%
  \chapter*{#1}%
  \addcontentsline{toc}{chapter}{#1}%
  \markboth{#1}{#1}%
}

% Preliminares
\newenvironment{dedicatoria}{\tituloSinNumero{Dedicatoria}}{\clearpage}
\newenvironment{agradecimientos}{\tituloSinNumero{Agradecimientos}}{\clearpage}
\newenvironment{resumen}{\tituloSinNumero{Resumen}}{\clearpage}
\renewenvironment{abstract}
  {\tituloSinNumero{Abstract}\begin{otherlanguage}{english}}
  {\end{otherlanguage}\clearpage}
\newenvironment{palabrasclave}{\tituloSinNumero{Palabras clave}}{\clearpage}

% Índices
\newcommand\indicegeneral{\tableofcontents\clearpage}
\newcommand\indicetablas{\listoftables\clearpage}
\newcommand\indicefiguras{\listoffigures\clearpage}

% Índice de Abreviaturas y Siglas
%   \begin{siglas}
%     \sigla{API}{Application Programming Interface}
%   \end{siglas}
\newenvironment{siglas}
  {\tituloSinNumero{Índice de Abreviaturas y Siglas}%
   \begin{description}[style=sameline, leftmargin=3cm, labelwidth=2.7cm,
     labelsep=0.3cm, align=left, itemsep=0pt, parsep=0pt, font=\bfseries]}
  {\end{description}\clearpage}
\newcommand\sigla[2]{\item[#1] #2}

% Finales
\newenvironment{conclusiones}{\tituloSinNumero{Conclusiones}}{\clearpage}

% Anexos: "Anexos" como título de nivel 1 y cada anexo como "Anexo A. ..."
\newcounter{ulsl@anexo}
\newcommand\anexos{%
  \tituloSinNumero{Anexos}%
  \setcounter{ulsl@anexo}{0}%
}
\newcommand\anexo[1]{%
  \refstepcounter{ulsl@anexo}%
  \section*{\appendixname\ \Alph{ulsl@anexo}. #1}%
  \addcontentsline{toc}{section}{\appendixname\ \Alph{ulsl@anexo}. #1}%
}

% Listas con la sangría del .docx (1,27 cm)
\setlist{leftmargin=1.27cm, itemsep=2pt, topsep=4pt}
\setlist[enumerate,1]{label=\alph*.}

% ---------------------------------------------------------------------------
% Hipervínculos (al final)
% ---------------------------------------------------------------------------
\RequirePackage[hidelinks,bookmarksnumbered]{hyperref}
\AtBeginDocument{%
  \hypersetup{pdftitle={\ulsl@titulo}, pdfauthor={\ulsl@autor}}%
}

\endinput
