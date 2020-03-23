from PyVMF import *
from random import randint

v = new_vmf()

r = SolidGenerator.surf_ramp(Vertex(), 1024, 576, 128, 32, 1)
v.add_solids(r)

v.export("window_g.vmf")
