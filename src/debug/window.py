from PyVMF import *
from random import randint

v = load_vmf("window.vmf")

r = SolidGenerator.room(Vertex(0, 0, 0), 1024, 1024, 1024)
v.add_solids(*r[randint(0, 5)].window())

v.add_solids(*r)


v.export("window_g.vmf")
