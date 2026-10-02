\def\RCSfile{innosoft}%
\def\RCSversion{1.0b}%
\def\RCSdate{2014/07/22}%

%-------------------------------------------------------
% Definiciones Constantes
%-------------------------------------------------------
\def\@journal{Revista Innovaci\'on y Software} 
\def\@company{Universidad La Salle, Arequipa, Per\'u}
\def\@issn{2708-0935}
\def\@shortjid{innosoft}
\def\@journalweb{\url{https://revistas.ulasalle.edu.pe/innosoft}}
\def\@journalmail{\href{mailto:facin.innosoft@ulasalle.edu.pe}{\nolinkurl{facin.innosoft@ulasalle.edu.pe}}}
\def\@journallicense{Esta obra est\'a bajo una \href{https://creativecommons.org/licenses/by/4.0/}{Licencia \\ Creative Commons  Atribuci\'on \\ 4.0 Internacional.
}}

%-------------------------------------------------------
% Definiciones Variables
%-------------------------------------------------------
% Revista
\def\volume{x}
\def\no{x}
\def\month{x-y}
\def\year{z}
\def\pages{x-y}
% Artículo
\def\recibido{dd/mm/aaaa}
\def\aceptado{dd/mm/aaaa}
\def\publicado{dd/mm/aaaa}

\def\ark{ark}
\def\doi{doi}
\def\purl{purl}

\def\orcidID#1{[{\href{https://orcid.org/#1}{\nolinkurl{#1}}}]}

%------------------------------------------------------- 
\NeedsTeXFormat{LaTeX2e}[1995/12/01]
\ProvidesClass{\@shortjid}

\let\if@noauthor\iftrue
\DeclareOption{noauthor}{\let\if@noauthor\iffalse}

\DeclareOption*{\PassOptionsToClass{\CurrentOption}{article}}

\ProcessOptions

\LoadClass[11pt]{article}

%-------------------------------------------------------
% Idioma ESPAÑOL
%-------------------------------------------------------
\RequirePackage[spanish,activeacute]{babel}
\RequirePackage[ansinew]{inputenc}

%-------------------------------------------------------
% Paquetes para fórmulas, ecuaciones y símbolos matemáticos
%-------------------------------------------------------
\RequirePackage{amsmath}
\RequirePackage{amssymb}
\RequirePackage{latexsym}

%-------------------------------------------------------
% Paquetes para figuras
%-------------------------------------------------------
\RequirePackage[dvips]{graphicx}
\RequirePackage[justification=centering, font=small]{caption}
\captionsetup{labelsep=period, belowskip=1em}

%-------------------------------------------------------
% Paquetes para bibliografia
%-------------------------------------------------------
\RequirePackage{{IEEEtran/IEEEtran}}
%-------------------------------------------------------
% Paquetes para tablas
%-------------------------------------------------------
\RequirePackage[para]{threeparttable}
\usepackage{etoolbox}
\appto\TPTnoteSettings{\footnotesize}
%-------------------------------------------------------
% Configuración de bloque de autores
%-------------------------------------------------------
\RequirePackage{authblk}
\renewcommand{\Authsep}{, }
\renewcommand{\Authand}{, }
\renewcommand{\Authands}{, }

%-------------------------------------------------------
% Configuración de titulos de secciones y subsecciones
%-------------------------------------------------------
\RequirePackage{titlesec}
\titlespacing{\section}{0pt}{16pt}{*-1.5}
\titleformat{\section}
	{\normalfont\fontsize{14}{14}\bfseries}{\thesection}{0em}{}
\titlespacing{\subsection}{0pt}{12pt}{*-1.5}
\titleformat{\subsection}
	{\normalfont\fontsize{12}{12}\bfseries}{\thesubsection}{0em}{}
\titleformat{\subsubsection}
	{\normalfont\fontsize{12}{12}\bfseries}{\thesubsection}{0em}{}	

%-------------------------------------------------------
% Configuración de vínculos
%-------------------------------------------------------
\RequirePackage[bookmarks=true, colorlinks=true, linkcolor=red, citecolor=blue, urlcolor=blue]{hyperref}
\RequirePackage{xcolor}

%-------------------------------------------------------
% Configuración de página y márgenes
%-------------------------------------------------------
\RequirePackage[letterpaper,headheight=3.81cm, top=3.81cm, bottom=3.81cm, left=2cm, right=1.2cm]{geometry}
\setlength\parindent{0pt}
\RequirePackage{setspace}

%-------------------------------------------------------
% Configuración de cabecera y pie de página
%-------------------------------------------------------
\RequirePackage{fancyhdr}
\pagestyle{fancy}
\fancyhf{}
\lhead{{\fontsize{9}{10}\selectfont \textcolor{gray}{\@journal \\
Vol. \volume, No. \no, Mes \month, \year \\
ISSN: \@issn \\
P\'ag. \pages \\}
\vskip -0.5em
\@journalweb}}

\rfoot{\thepage}
\lfoot{\textcolor{gray}{\\
\@company\\}
\@journalmail}
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}

\fancypagestyle{firstpage}{
\rhead{{\fontsize{9}{10}\selectfont \textcolor{gray}{
\includegraphics[width=80pt]{license.png}\\
\vskip 0em
\@journallicense\\}}}
}
%-------------------------------------------------------
% Configuración del resumen
%-------------------------------------------------------
\renewenvironment{abstract}{%
\\\vskip -1em
\par\noindent\rule{\textwidth}{0.5pt}
\vskip 1em
{\raggedright\textbf\abstractname\addvspace\baselineskip}}
{\par\noindent\rule{\textwidth}{0.5pt}}

%-------------------------------------------------------
% Configuración de título del artículo
%-------------------------------------------------------
\def\titlefont{\fontsize{18}{20}\selectfont\raggedright\textbf}
\def\authorfont{\fontsize{11}{11}\selectfont\raggedright}

\makeatletter

\let\ps@plain\ps@firstpage 
\renewcommand\@maketitle{%
\vskip -1em
{\par\noindent{\fontsize{11pt}{11pt}\selectfont Tipo de art\'iculo: \tipoarticulo\\
Tem\'atica: \tematica\\
Recibido: \recibido\ \textbar\ Aceptado: \aceptado\ \textbar\ Publicado: \publicado\\}}

{\par\noindent{\fontsize{10pt}{10pt}\selectfont
\vskip -6em
\\\hspace*{37em}
Identificadores persistentes:\\\hspace*{37em}
DOI: \href{https://doi.org/\doi}{\nolinkurl{\doi}}\\\hspace*{37em}
ARK: \href{https://n2t.net/\ark}{\nolinkurl{\ark}}\\\hspace*{37em} }}

\vskip 0.5em
{\par\noindent \titlefont\@title \par\noindent }
\vskip 0.5em
{\par\noindent \textit{\titlefont\englistitle} \par\noindent }
\vskip 1em
\if@noauthor
{\par\noindent \authorfont\@author \par\noindent}
\vskip -0.5em
{\par\noindent {\fontsize{11pt}{11pt}\selectfont $^*$Autor para correspondencia: \authormail} \par\noindent}
\fi
}

\makeatother

%-------------------------------------------------------
% Configuración de comandos
%-------------------------------------------------------
\def\keywordname{{\bf Palabras claves:}}
\providecommand{\keywords}[1]{\par\addvspace\baselineskip
\noindent\keywordname\enspace\ignorespaces#1}

\def\englishabstractname{\bf Abstract}
\providecommand{\englishabstract}[1]{\par\addvspace\baselineskip
\noindent\englishabstractname\enspace\ignorespaces\\\it#1}

\def\englishkeywordname{{\bf Keywords:}}
\providecommand{\englishkeywords}[1]{\par\addvspace\baselineskip
\noindent\englishkeywordname\enspace\ignorespaces#1}

\newtheorem{definition}{\sc Definición}

\addto\captionsspanish{%
  \renewcommand\tablename{Tabla}
}

\def\theoremname{Teorema}

\DeclareMathSymbol{\Gamma}{\mathalpha}{letters}{"00}
\DeclareMathSymbol{\Delta}{\mathalpha}{letters}{"01}
\DeclareMathSymbol{\Theta}{\mathalpha}{letters}{"02}
\DeclareMathSymbol{\Lambda}{\mathalpha}{letters}{"03}
\DeclareMathSymbol{\Xi}{\mathalpha}{letters}{"04}
\DeclareMathSymbol{\Pi}{\mathalpha}{letters}{"05}
\DeclareMathSymbol{\Sigma}{\mathalpha}{letters}{"06}
\DeclareMathSymbol{\Upsilon}{\mathalpha}{letters}{"07}
\DeclareMathSymbol{\Phi}{\mathalpha}{letters}{"08}
\DeclareMathSymbol{\Psi}{\mathalpha}{letters}{"09}
\DeclareMathSymbol{\Omega}{\mathalpha}{letters}{"0A}

\setlength\footnotesep{7.7pt}
\let\footnotesize\small

\long\def\@makecaption#1#2{%
  \small
  \vskip\abovecaptionskip
  \sbox\@tempboxa{{\bfseries #1.} #2}%
  \ifdim \wd\@tempboxa >\hsize
    {\bfseries #1.} #2\par
  \else
    \global \@minipagefalse
    \hb@xt@\hsize{\hfil\box\@tempboxa\hfil}%
  \fi
  \vskip\belowcaptionskip}

\def\fps@figure{htbp}
\def\fnum@figure{\figurename\thinspace\thefigure}
\def \@floatboxreset {%
        \reset@font
        \small
        \@setnobreak
        \@setminipage
        
\setcounter{equation}{0}
}