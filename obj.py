# def obj_to_solids(filename):
#     scene = pywavefront.Wavefront(filename, collect_faces=False)
#     for mesh in scene.meshes.values():
#         yield coordinates_to_solid(mesh.untouched_faces)
#
#
# def coordinates_to_solid(coordinate_list):
#     s = Solid()
#     s.editor = Editor()
#     p = 1
#     for face in coordinate_list:
#         verts = ""
#         for vert in face:
#             verts+="("
#             for xyz in vert:
#                 verts += " "
#                 verts += str(xyz)
#             verts+=")"
#
#         f = Side({"id":p,
#                   "plane":verts,
#                   "uaxis":"[1 0 0 0] 0.5",
#                   "vaxis":"[0 -1 0 0] 0.5"})
#         p += 1
#
#         s.side.append(f)
#     return s