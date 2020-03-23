from PyVMF import *
from obj import *

v = new_vmf()

for solid in obj_to_solids("minecraft.obj", "banana/minecraft", 64):
    v.add_solids(solid)

v.export("ico.vmf")
