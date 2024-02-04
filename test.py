import cadquery as cq

result = cq.Workplane().box(10, 10, 10)

highlight = result.faces('>Z')

