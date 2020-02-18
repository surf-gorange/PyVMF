from PyVMF import *
from obj import *

v = new_vmf()

for solid in obj_to_solids("ico.obj", 16):
    v.add_solids(solid)

v.export("ico.vmf")
