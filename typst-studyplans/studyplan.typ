#set page(paper: "a4", flipped: true)

#let programme = json("bachelor.json")

#let name = programme.name
#let type = programme.programme_type_display

#let gray30 = luma(20%)

#box(
  text(24pt, gray30, weight: "bold", type),
  stroke: 3pt + gray30, inset: 8pt, radius: 5pt, baseline: 30%
)
#h(0.5em)
#text(24pt, name)

#let modules = programme.modules
#let semesters = programme.semester_count

#semesters Semesters | #modules.len() Modules

#let modules_per_semester = range(1, semesters).map(sem => {
  modules.filter(m => {
    m.courses.map(c => c.semester).any(x => x == sem)
  })
})

#modules_per_semester.map(x => x.len())

#grid.cell

// #let cols = calc.max(..modules_per_semester)
// #let num_cards = cols * semesters

// #num_cards

// #let cards = range(1, num_cards).map(x => {rect(fill: red, inset: 10pt)})

// #grid(
//   columns: cols,
//   rows: semesters,
//   gutter: 5pt,
//   ..cards
// )