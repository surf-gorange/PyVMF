from pywavefront import *
from PyVMF import *


def obj_to_solids(filename: str, scale: int = 64):
    """
    Turns an .obj file to VMF solids, **BETA** it's very finicky and remember to invert normals

    :param filename:
    :param scale:
    """
    scene = Wavefront(filename, collect_faces=True)
    for mesh in scene.mesh_list:
        solid = Solid()

        for face in mesh.faces[::2]:
            side = Side()

            for i, vertex in enumerate(face):
                vs = str(scene.vertices[vertex])
                v = Convert.string_to_vertex(vs)
                v.multiply(scale)
                side.plane[i] = v

            solid.add_sides(side)

        solid.editor = Editor()
        solid.rotate_x(Vertex(0, 0, 0), 90)

        yield solid
