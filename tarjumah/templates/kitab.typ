#set document(title: "{{TITLE}}", author: "{{AUTHOR}}")

#set page(
  paper: "iso-b5",
  margin: (x: 2.2cm, y: 2.5cm),
  numbering: "1",
  number-align: center,
)

#set text(
  font: ("EB Garamond", "New Computer Modern", "Liberation Serif", "Geeza Pro", "Amiri", "Noto Naskh Arabic"),
  size: 11pt,
  lang: "en",
)

#set par(
  justify: true,
  leading: 0.75em,
  first-line-indent: 1.2em,
)

#show heading.where(level: 1): it => [
  #pagebreak(weak: true)
  #v(2cm)
  #set text(size: 22pt, weight: "bold")
  #set par(first-line-indent: 0pt)
  #it
  #v(1cm)
]

#show heading.where(level: 2): it => [
  #v(0.9em)
  #set text(size: 13pt, weight: "bold")
  #set par(first-line-indent: 0pt)
  #it
  #v(0.3em)
]

#show heading.where(level: 3): it => [
  #v(0.6em)
  #set text(size: 11pt, weight: "bold", style: "italic")
  #set par(first-line-indent: 0pt)
  #it
]

#set footnote.entry(separator: line(length: 30%, stroke: 0.5pt))
#show footnote.entry: set text(size: 9pt)

// === Title page ===
#align(center)[
  #v(5cm)
  #text(size: 26pt, weight: "bold")[{{TITLE}}]
  #v(1cm)
  #text(size: 14pt, style: "italic")[{{AUTHOR}}]
  #v(2fr)
  #text(size: 10pt, fill: rgb("#555"))[Translated by Tarjumah]
  #v(1cm)
]
#pagebreak()

// === Table of Contents ===
#outline(title: [Contents], indent: auto)
#pagebreak()

// === Body ===
{{BODY}}
