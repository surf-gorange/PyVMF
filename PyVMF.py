import re
from copy import deepcopy
import sys
import time
import math
import operator
# import pywavefront


def num(s):  # Tries to turn string into int, then float, if all fails returns string
    try:
        return int(s)
    except ValueError:
        try:
            return float(s)
        except ValueError:
            return str(s)


class TempCategory:  # This class is used when reading the vmf file and when creating the vmf class later on
    def __init__(self, category, indent):
        self.category = category  # versioninfo, visgroups, world, solid, dispinfo, etc...
        self.indent = indent
        self.data = []  # Everything inside the curly brackets other than child categories (ex: "skyname" "sky_dust")
        self.children = []  # List of all children categories (ex: side, dispinfo, editor, etc...)
        self.current_child = None  # Used when going into nested children (ex: solid -> side -> dispinfo -> Normals)
        self.dic = {}  # This is where all the data is stored when it's cleaned, used when creating VMF class

    def __repr__(self):
        return self.category

    def add_line(self, line, indent):
        diff = indent - self.indent  # Finding out how far into the nested children we need to go
        c = self
        for i in range(diff-1):
            c = c.current_child
        c.data.append(line)

    def add_child(self, category, indent):
        diff = indent - self.indent  # Same concept as self.add_line
        c = self
        for i in range(diff-1):
            c = c.current_child

        new_child = TempCategory(category, indent)
        c.children.append(new_child)
        c.current_child = new_child

    def clean_up(self):
        self.category = self.category.split()[0]  # We remove the tabs
        for i in self.data:
            clean = re.findall(r'\"(.*?)\"', i)  # We remove the double quotes and separate (example line: "id" "2688")
            self.dic[clean[0]] = num(clean[1])  # The values, IF possible are turned into either ints or floats

        for j in self.children:
            j.clean_up()  # Nested function calls


def file_parser(file):
    with open(file, "r") as vmf:

        indent = 0
        previous_line = "versioninfo\n"  # We only know it's a category the next line (the curly brackets open)
        extracted = []

        for line in vmf.readlines()[1:]:
            if "}" in line:
                indent -= 1
                if indent == 0:  # If indent is not 0 we know it's a child category and not a main category
                    extracted.append(t)
                continue

            if "{" in line:
                if indent > 0:  # If indent is not 0 we know it's a child category and not a main category
                    # Open curly brackets ALWAYS follow a category, so we know the previous line is the category name
                    t.add_child(previous_line, indent)
                else:
                    t = TempCategory(previous_line, indent)  # This is a main category (not a child category)
                indent += 1
                continue

            if "\"" in line: t.add_line(line, indent)  # ALL lines with data have double quotes in them

            previous_line = line

    for c in extracted:
        # clean_up is a recursive function we only need to call it on the main categories
        c.clean_up()

    return extracted  # This is used when creating a VMT class


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


class Common:
    ID = 0

    def export(self):
        d = {}
        for item in self.export_list:
            t = getattr(self, item)
            d[item] = t
        return d, self.other

    def export_children(self):
        return []

    def copy(self):
        """Copies a category using the copy.deepcopy function"""
        return deepcopy(self)

    def ids(self):
        Common.ID += 1
        return Common.ID

    def _string_to_vertex(self, string: str):
        reg = re.sub(r'[(){}<>\[\]]', '', string).split()
        return Vertex(num(reg[0]), num(reg[1]), num(reg[2]))

    def _string_to_3x_vertex(self, string: str):
        reg = re.sub(r'[(){}<>]', '', string).split()
        clean = []
        for i in reg:
            clean.append(num(i))
        return clean

    def _string_to_color(self, string: str):
        temp = string.split()
        return Color(temp[0], temp[1], temp[2])

    def _string_to_uvaxis(self, string: str):
        reg = re.sub(r'[\[\]]', '', string).split()
        return UVaxis(*reg)

    def _dic_and_children(self, dic, children):
        if dic is None:
            dic = {}
        if children is None:
            children = []
        return dic, children

    def _dic(self, dic):
        if dic is None:
            dic = {}
        return dic


class Color:
    def __init__(self, r, g, b):
        self.r = r
        self.g = g
        self.b = b

    def __str__(self):
        return f"{self.r} {self.g} {self.b}"

    def set(self, r=-1, g=-1, b=-1):
        if r != -1 and 0 < r < 256:
            self.r = r
        if g != -1 and 0 < g < 256:
            self.g = g
        if b != -1 and 0 < b < 256:
            self.b = b

    def export(self):
        return self.r, self.g, self.b


class VersionInfo(Common):
    NAME = "versioninfo"

    def __init__(self, dic: dict = None):
        dic = self._dic(dic)

        self.editorversion = dic.pop("editorversion", 400)
        self.editorbuild = dic.pop("editorbuild", 8075)
        self.mapversion = dic.pop("mapversion", 7)
        self.formatversion = dic.pop("formatversion", 100)
        self.prefab = dic.pop("prefab", 0)

        self.other = dic
        self.export_list = ["editorversion", "editorbuild", "mapversion", "formatversion", "prefab"]


class VisGroups(Common):
    NAME = "visgroups"

    def __init__(self, dic: dict = None, children: list = None):
        dic, children = self._dic_and_children(dic, children)

        self.other = dic
        self.export_list = []

        self.visgroup = []
        for child in children:
            self.visgroup.append(VisGroup(child.dic, child.children))

    def new_visgroup(self, name: str):
        self.visgroup.append(VisGroup({"name": name}))

    def get_visgroups(self):
        return self.visgroup

    def export_children(self):
        return (*self.visgroup,)


class VisGroup(Common):
    NAME = "visgroup"

    def __init__(self, dic: dict = None, children: list = None):
        dic, children = self._dic_and_children(dic, children)

        self.name = dic.pop("name", "default")
        self.visgroupid = dic.pop("visgroupid", self.ids())
        self.color = dic.pop("color", "0 0 0")

        self.other = dic
        self.export_list = ["name", "visgroupid", "color"]

        self.visgroup = []
        for child in children:
            if str(child) == VisGroup.NAME:
                self.visgroup.append(VisGroup(child.dic, child.children))

    def export_children(self):
        return (*self.visgroup,)


class ViewSettings(Common):
    NAME = "viewsettings"

    def __init__(self, dic: dict = None):
        dic = self._dic(dic)

        self.bSnapToGrid = dic.pop("bSnapToGrid", 1)
        self.bShowGrid = dic.pop("bShowGrid", 1)
        self.bShowLogicalGrid = dic.pop("bShowLogicalGrid", 0)
        self.nGridSpacing = dic.pop("nGridSpacing", 64)
        self.bShow3DGrid = dic.pop("bShow3DGrid", 0)

        self.other = dic
        self.export_list = ["bSnapToGrid", "bShowGrid", "bShowLogicalGrid", "nGridSpacing", "bShow3DGrid"]


class World(Common):
    NAME = "world"

    def __init__(self, dic: dict = None, children: list = None):
        dic, children = self._dic_and_children(dic, children)

        self.id = dic.pop("id", self.ids())
        self.mapversion = dic.pop("mapversion", 1)
        self.classname = dic.pop("classname", "worldspawn")
        self.detailmaterial = dic.pop("detailmaterial", "detail/detailsprites")
        self.detailvbsp = dic.pop("detailvbsp", "detail.vsbp")
        self.maxpropscreenwidth = dic.pop("maxpropscreenwidth", -1)
        self.skyname = dic.pop("skyname", "sky_dust")

        self.other = dic
        self.export_list = ["id", "mapversion", "classname", "detailmaterial", "detailvbsp", "maxpropscreenwidth",
                            "skyname"]

        self.solid = []
        self.hidden = []
        self.group = []
        for child in children:
            if str(child) == Solid.NAME:
                self.solid.append(Solid(child.dic, child.children))

            elif str(child) == Hidden.NAME:
                self.hidden.append(Hidden(child.dic, child.children))

            elif str(child) == Group.NAME:
                self.group.append(Group(child.dic, child.children))

    def export_children(self):
        return (*self.solid, *self.hidden, *self.group)


class Vertex(Common):  # Vertex has to be above the Solid class (see: set_pos_vertex function)
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

        self.sorting = 0  # Used in solid get_3d_extremity
        self.normal = True

    def __str__(self):
        if self.normal:
            return f"{self.x} {self.y} {self.z}"
        else:
            return f"[{self.x} {self.y} {self.z}]"

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y and self.z == other.z

    def __add__(self, other):
        return Vertex(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other):
        return Vertex(self.x - other.x, self.y - other.y, self.z - other.z)

    def similar(self, other, accuracy=0.001):
        return ((abs(self.x - other.x) < accuracy) and
                (abs(self.y - other.y) < accuracy) and
                (abs(self.z - other.z) < accuracy))

    def divide(self, amount):
        self.x /= amount
        self.y /= amount
        self.z /= amount

    def divide_separate(self, x, y, z):
        self.x /= x
        self.y /= y
        self.z /= z

    def diff(self, other):
        return Vertex(self.x - other.x, self.y - other.y, self.z - other.z)

    def move(self, x, y, z):
        self.x += x
        self.y += y
        self.z += z

    def set(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def rotate_z(self, center, angle):
        a = math.radians(angle)
        new_x = center.x + (self.x - center.x)*math.cos(a) - (self.y - center.y)*math.sin(a)
        new_y = center.y + (self.x - center.x)*math.sin(a) + (self.y - center.y)*math.cos(a)
        self.set(new_x, new_y, self.z)

    def rotate_y(self, center, angle):
        a = math.radians(angle)
        new_x = center.x + (self.x - center.x) * math.cos(a) - (self.z - center.z) * math.sin(a)
        new_z = center.z + (self.x - center.x) * math.sin(a) + (self.z - center.z) * math.cos(a)
        self.set(new_x, self.y, new_z)

    def rotate_x(self, center, angle):
        a = math.radians(angle)
        new_y = center.y + (self.y - center.y) * math.cos(a) - (self.z - center.z) * math.sin(a)
        new_z = center.z + (self.y - center.y) * math.sin(a) + (self.z - center.z) * math.cos(a)
        self.set(self.x, new_y, new_z)

    def flip(self, x=None, y=None, z=None):
        if x is not None:
            self.x += 2 * (x - self.x)
        if y is not None:
            self.y += 2 * (y - self.y)
        if z is not None:
            self.z += 2 * (z - self.z)

    def align_to_grid(self):
        self.x = int(self.x)
        self.y = int(self.y)
        self.z = int(self.z)

    def export(self):
        return (self.x,
                self.y,
                self.z)


class Solid(Common):
    NAME = "solid"

    def __init__(self, dic: dict = None, children: list = None):
        dic, children = self._dic_and_children(dic, children)

        self.id = dic.pop("id", self.ids())

        self.other = dic
        self.export_list = ["id"]

        self.side = []
        self.editor = None
        for child in children:
            if str(child) == Side.NAME:
                self.side.append(Side(child.dic, child.children))

            elif str(child) == Editor.NAME:
                self.editor = Editor(child.dic)

    def add_sides(self, *args):
        self.side.extend(args)

    def move(self, x, y, z):
        for side in self.side:
            for vert in side.plane:
                vert.move(x, y, z)

    def get_linked_vertices(self, vertex: Vertex, similar=0.0) -> list:
        li = []

        for vert in self.get_all_vertices():
            if similar == 0.0:
                if vertex == vert:
                    li.append(vert)

            else:
                if vertex.similar(vert, similar):
                    li.append(vert)

        return li


    def rotate_x(self, center, angle):
        for side in self.side:
            side.rotate_x(center, angle)

    def rotate_y(self, center, angle):
        for side in self.side:
            side.rotate_y(center, angle)

    def rotate_z(self, center, angle):
        for side in self.side:
            side.rotate_z(center, angle)

    def flip(self, x=None, y=None, z=None):
        for vert in self.get_all_vertices():
            vert.flip(x, y, z)

    def scale(self, center, x=1.0, y=1.0, z=1.0):
        x -= 1
        y -= 1
        z -= 1
        for vertex in self.get_all_vertices():
            diff = vertex.diff(center)
            fixed_diff = (diff.x*x, diff.y*y, diff.z*z)
            vertex.move(*fixed_diff)

    @property
    def center(self):
        v = Vertex(0, 0, 0)
        vert_list = self.get_only_unique_vertices()
        for vert in vert_list:
            v = v + vert
        v.divide(len(vert_list))
        return v

    @center.setter
    def center(self, vertex):
        self.move(*vertex.diff(self.center).export())

    @property
    def center_geo(self):
        v = Vertex(0, 0, 0)

        x = self.get_axis_extremity(x=False).x
        y = self.get_axis_extremity(y=False).y
        z = self.get_axis_extremity(z=False).z

        size = self.get_size()
        size.divide(2)

        v.set(x, y, z)
        v.move(*size.export())

        return v

    def get_axis_extremity(self, x: bool = None, y: bool = None, z: bool = None) -> Vertex:
        verts = self.get_only_unique_vertices()

        if x is not None:
            lx = sorted(verts, key=operator.attrgetter("x"))
            return lx[int(not x)-1]

        elif y is not None:
            ly = sorted(verts, key=operator.attrgetter("y"))
            return ly[int(not y)-1]

        elif z is not None:
            lz = sorted(verts, key=operator.attrgetter("z"))
            return lz[int(not z)-1]

        raise ValueError("No axis given")

    def get_3d_extremity(self, x: bool = None, y: bool = None, z: bool = None):
        verts = self.get_only_unique_vertices()

        for vert in verts:
            vert.sorting = 0
            if x is not None:
                if x:
                    vert.sorting += vert.x
                else:
                    vert.sorting -= vert.x
            if y is not None:
                if y:
                    vert.sorting += vert.y
                else:
                    vert.sorting -= vert.y
            if z is not None:
                if z:
                    vert.sorting += vert.z
                else:
                    vert.sorting -= vert.z

        sort = sorted(verts, key=operator.attrgetter("sorting"))
        best = sort[-1]

        ties = []
        for vert in sort:
            if vert.sorting == best.sorting:
                ties.append(vert)

        return best, ties

    def get_all_vertices(self):
        vertex_list = []
        for side in self.side:
            vertex_list.extend(side.plane)
        return vertex_list

    def get_sides(self):
        return self.side

    def get_size(self) -> Vertex:
        x = []
        y = []
        z = []
        for vert in self.get_all_vertices():
            x.append(vert.x)
            y.append(vert.y)
            z.append(vert.z)

        return Vertex(max(x) - min(x), max(y) - min(y), max(z) - min(z))

    def get_displacement_sides(self, matrix_instead_of_side=False) -> list:
        li = []
        for side in self.side:
            if side.dispinfo is not None:
                if matrix_instead_of_side:
                    li.append(side.dispinfo.matrix)
                else:
                    li.append(side)
        return li

    def get_texture_sides(self, name: str, exact=False) -> list:
        li = []
        for side in self.side:
            if not exact:
                if name.upper() in side.material:
                    li.append(side)
            else:
                if side.material == name.upper():
                    li.append(side)
        return li

    def get_only_unique_vertices(self):
        vertex_list = []
        for side in self.side:
            for vertex in side.plane:
                if vertex not in vertex_list:
                    vertex_list.append(vertex)

        return vertex_list

    def has_texture(self, name: str, exact=False) -> bool:
        for side in self.side:
            if not exact:
                if name.upper() in side.material:
                    return True
            else:
                if side.material == name.upper():
                    return True
        return False

    def replace_texture(self, old_material: str, new_material: str):
        for side in self.side:
            if side.material == old_material:
                side.material = new_material

    def naive_subdivide(self, x=1, y=1, z=1) -> list:
        li = []

        s = self.copy()

        half_size = s.get_size()
        half_size.divide(2)

        ratio = (1/x, 1/y, 1/z)

        s.scale(s.center, *ratio)

        move_amount = s.get_size()

        s.move(-half_size.x, half_size.y, half_size.z)
        s.move(move_amount.x/2, -move_amount.y/2, -move_amount.z/2)

        for iz in range(z):
            for iy in range(y):
                for ix in range(x):
                    s2 = s.copy()
                    s2.move(ix * move_amount.x, -iy * move_amount.y, -iz * move_amount.z)
                    li.append(s2)

        return li

    def is_simple_solid(self) -> bool:
        return len(self.side) <= 6

    def set_texture(self, new_material):
        for side in self.get_sides():
            side.material = new_material

    def remove_all_displacements(self):
        for side in self.side:
            side.remove_displacement()

    def export_children(self):
        return (*self.side, self.editor)


class Editor(Common):
    NAME = "editor"

    def __init__(self, dic: dict = None, parent_type=None):
        dic = self._dic(dic)

        self.parent_type = parent_type  # This is not used in the VMF

        self.color = dic.pop("color", "0 0 0")
        self.color = self._string_to_color(self.color)
        self.groupid = dic.pop("groupid", None)
        self.visgroupid = dic.pop("visgroupid", None)
        self.visgroupshown = dic.pop("visgroupshown", 1)
        self.visgroupautoshown = dic.pop("visgroupautoshown", 1)
        self.logicalpos = dic.pop("logicalpos", "[0 2500]")  # Unique to Entity

        self.other = dic
        self.export_list = []

    def has_visgroup(self) -> bool:
        if self.visgroupid is None:
            return False
        else:
            return True

    def export(self):
        d = {"color": self.color}
        if self.groupid is not None:
            d["groupid"] = self.groupid
        if self.visgroupid is not None:
            d["visgroupid"] = self.visgroupid
        d["visgroupshown"] = self.visgroupshown
        d["visgroupautoshown"] = self.visgroupautoshown
        if self.parent_type == "entity":
            d["logicalpos"] = self.logicalpos

        return d, self.other


class Group(Common):
    NAME = "group"

    def __init__(self, dic: dict = None, children: list = None):
        dic, children = self._dic_and_children(dic, children)

        self.id = dic.pop("id", self.ids())

        self.other = dic
        self.export_list = ["id"]

        self.editor = None
        for child in children:
            if str(child) == Editor.NAME:
                self.editor = Editor(child.dic)

    def export_children(self):
        return [self.editor]


class Side(Common):
    NAME = "side"

    def __init__(self, dic: dict = None, children: list = None):
        dic, children = self._dic_and_children(dic, children)

        self.id = dic.pop("id", self.ids())

        p = dic.pop("plane", "(0 0 0) (0 0 0) (0 0 0)")
        t = self._string_to_3x_vertex(p)
        self.plane = (Vertex(t[0], t[1], t[2]),
                      Vertex(t[3], t[4], t[5]),
                      Vertex(t[6], t[7], t[8]))

        self.material = dic.pop("material", "TOOLS/TOOLSNODRAW")

        self.uaxis = dic.pop("uaxis", "[1 0 0 0] 0.5")
        self.uaxis = self._string_to_uvaxis(self.uaxis)
        self.vaxis = dic.pop("vaxis", "[0 -1 0 0] 0.5")
        self.vaxis = self._string_to_uvaxis(self.vaxis)

        self.rotation = dic.pop("rotation", 0)
        self.lightmapscale = dic.pop("lightmapscale", 16)
        self.smoothing_groups = dic.pop("smoothing_groups", 0)

        self.other = dic
        self.export_list = []

        self.dispinfo = None
        for child in children:
            if str(child) == DispInfo.NAME:
                self.dispinfo = DispInfo(child.dic, child.children)

    def __str__(self):
        return f"({self.plane[0]}) ({self.plane[1]}) ({self.plane[2]})"

    def move(self, x, y, z):
        for vertex in self.plane:
            vertex.move(x, y, z)

    def rotate_x(self, center, angle):
        for vert in self.plane:
            vert.rotate_x(center, angle)

    def rotate_y(self, center, angle):
        for vert in self.plane:
            vert.rotate_y(center, angle)

    def rotate_z(self, center, angle):
        for vert in self.plane:
            vert.rotate_z(center, angle)

    def flip(self, x=None, y=None, z=None):
        raise ValueError("The flip function doesn't currently work")
        for vert in self.plane:
            vert.flip(x, y, z)

    def get_vertices(self):
        return self.plane

    def get_displacement(self):
        return self.dispinfo

    def get_vector(self):
        raise ValueError("Vectors not implemented yet")

    def remove_displacement(self):
        self.dispinfo = None

    def export(self):
        d = {"id": self.id,
             "plane": self.__str__(),
             "material": self.material,
             "uaxis": self.uaxis,
             "vaxis": self.vaxis,
             "rotation": self.rotation,
             "lightmapscale": self.lightmapscale,
             "smoothing_groups": self.smoothing_groups}

        return d, self.other

    def export_children(self):
        return [self.dispinfo]


class DispInfo(Common):
    NAME = "dispinfo"

    def __init__(self, dic: dict = None, children: list = None):
        dic, children = self._dic_and_children(dic, children)

        self.power = dic.pop("power", 3)
        startposition = dic.pop("startposition", "[0 0 0]")
        self.startposition = self._string_to_vertex(startposition)
        self.startposition.normal = False
        self.flags = dic.pop("flags", 0)
        self.elevation = dic.pop("elevation", 0)
        self.subdiv = dic.pop("subdiv", 0)

        self.size = 0
        self.matrix_size_fix = 0

        if self.power == 2 or self.power == 4:
            self.matrix_size_fix = self.power**2
            self.size = self.matrix_size_fix + 1
        else:
            self.size = self.power**2
            self.matrix_size_fix = self.size - 1

        self.matrix = Matrix(self.size)

        self.other = dic
        self.export_list = ["power", "startposition", "flags", "elevation", "subdiv"]

        self._normals = None
        self._distances = None
        self._offsets = None
        self._offset_normals = None
        self._alphas = None
        self._triangle_tags = None
        self._allowed_verts = None

        for child in children:
            if str(child) == Normals.NAME:
                self._normals = Normals(self.matrix, child.dic)
            if str(child) == Distances.NAME:
                self._distances = Distances(self.matrix, child.dic)
            if str(child) == Offsets.NAME:
                self._offsets = Offsets(self.matrix, child.dic)
            if str(child) == OffsetNormals.NAME:
                self._offset_normals = OffsetNormals(self.matrix, child.dic)
            if str(child) == Alphas.NAME:
                self._alphas = Alphas(self.matrix, child.dic)
            if str(child) == TriangleTags.NAME:
                self._triangle_tags = TriangleTags(self.matrix, child.dic)
            if str(child) == AllowedVerts.NAME:
                self._allowed_verts = AllowedVerts(self.matrix, child.dic)

    def export_children(self):
        return self._normals, self._distances, self._offsets, self._offset_normals, self._alphas,\
               self._triangle_tags, self._allowed_verts


class DispVert(Common):
    def __init__(self):
        self.normal = Vertex(0, 0, 0)
        self.distance = 0
        self.offset = Vertex(0, 0, 0)
        self.offset_normal = Vertex(0, 0, 1)
        self.alpha = 0
        self.triangle_tag = None

    def __str__(self):
        return f"{self.normal} {self.distance}"

    def set(self, normal, distance):
        self.normal.set(*normal)
        self.distance = distance

    def set_alpha(self, amount):
        if amount < 0 or amount > 255:
            raise ValueError(f"Error: {amount} not in range [0, 255]")
        else:
            self.alpha = amount


class TriangleTag(Common):
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __str__(self):
        return f"{self.x} {self.y}"


class Matrix(Common):
    def __init__(self, size: int):
        self.size = size
        self.matrix = [[DispVert() for y in range(self.size)] for x in range(self.size)]

    def __str__(self):
        return str(self.matrix)

    def get(self, x, y):
        return self.matrix[x][y]

    def row(self, y):
        li = []
        for x in range(self.size):
            li.append(self.matrix[x][y])
        return li

    def column(self, x):
        return self.matrix[x]

    def rect(self, x, y, w, h):
        for y2 in range(y, y + h):
            for x2 in range(x, x + w):
                yield x2, y2, self.get(x2, y2)

    def inv_rect(self, x, y, w, h, step):
        for y2 in range(y, y + h, step):
            for x2 in range(x, x + w, step):
                yield x2, y2, self.get(x2, self.size - y2 - 1)

    def extract_dic(self, dic, a_var=1, triangle=False):
        for y in range(self.size - triangle):
            t = dic.pop(f"row{y}").split(" ")
            for x in range((self.size - triangle) * a_var):
                yield x, y, t

    def export_attr(self, attribute):
        e = {}
        for y in range(self.size):
            current_row = f"row{y}"
            temp = getattr(self.row(y)[0], attribute)
            if temp is not None:
                e[current_row] = f"{temp}"
            for row in self.row(y)[1:]:
                temp = getattr(row, attribute)
                if temp is not None:
                    e[current_row] += f" {temp}"

        return e


class Normals(Common):
    NAME = "normals"

    def __init__(self, matrix, dic: dict = None):
        dic = self._dic(dic)

        self.matrix = matrix
        a_var = 3
        i = 0
        for x, y, t in self.matrix.extract_dic(dic, a_var):
            if i == 0:
                self.matrix.get(x//a_var, y).normal.x = num(t[x])
            elif i == 1:
                self.matrix.get(x//a_var, y).normal.y = num(t[x])
            else:
                self.matrix.get(x//a_var, y).normal.z = num(t[x])
                i = -1
            i += 1

        self.other = dic
        self.export_list = []

    def export(self):
        return self.matrix.export_attr("normal"), self.other


class Distances(Common):
    NAME = "distances"

    def __init__(self, matrix, dic: dict = None):
        dic = self._dic(dic)

        self.matrix = matrix
        for x, y, t in self.matrix.extract_dic(dic):
            self.matrix.get(x, y).distance = num(t[x])

        self.other = dic
        self.export_list = []

    def export(self):
        return self.matrix.export_attr("distance"), self.other


class Offsets(Common):
    NAME = "offsets"

    def __init__(self, matrix, dic: dict = None):
        dic = self._dic(dic)

        self.matrix = matrix
        a_var = 3
        i = 0
        for x, y, t in self.matrix.extract_dic(dic, a_var):
            if i == 0:
                self.matrix.get(x // a_var, y).offset.x = num(t[x])
            elif i == 1:
                self.matrix.get(x // a_var, y).offset.y = num(t[x])
            else:
                self.matrix.get(x // a_var, y).offset.z = num(t[x])
                i = -1
            i += 1

        self.other = dic
        self.export_list = []

    def export(self):
        return self.matrix.export_attr("offset"), self.other


class OffsetNormals(Common):
    NAME = "offset_normals"

    def __init__(self, matrix, dic: dict = None):
        dic = self._dic(dic)

        self.matrix = matrix
        a_var = 3
        i = 0
        for x, y, t in self.matrix.extract_dic(dic, a_var):
            if i == 0:
                self.matrix.get(x // a_var, y).offset_normal.x = num(t[x])
            elif i == 1:
                self.matrix.get(x // a_var, y).offset_normal.y = num(t[x])
            else:
                self.matrix.get(x // a_var, y).offset_normal.z = num(t[x])
                i = -1
            i += 1

        self.other = dic
        self.export_list = []

    def export(self):
        return self.matrix.export_attr("offset_normal"), self.other


class Alphas(Common):
    NAME = "alphas"

    def __init__(self, matrix, dic: dict = None):
        dic = self._dic(dic)

        self.matrix = matrix
        for x, y, t in self.matrix.extract_dic(dic):
            self.matrix.get(x, y).alpha = num(t[x])

        self.other = dic
        self.export_list = []

    def export(self):
        return self.matrix.export_attr("alpha"), self.other


class TriangleTags(Common):
    NAME = "triangle_tags"

    def __init__(self, matrix, dic: dict = None):
        dic = self._dic(dic)

        self.matrix = matrix  # TriangleTags is 1 row and column smaller than the others
        a_var = 2
        i = 0
        t1 = 0
        for x, y, t in self.matrix.extract_dic(dic, a_var, True):
            if i == 0:
                t1 = num(t[x])
            else:
                self.matrix.get(x // a_var, y).triangle_tag = TriangleTag(t1, num(t[x]))
                i = -1
            i += 1

        self.other = dic
        self.export_list = []

    def export(self):
        return self.matrix.export_attr("triangle_tag"), self.other


class AllowedVerts(Common):
    NAME = "allowed_verts"

    def __init__(self, matrix, dic: dict = None):
        dic = self._dic(dic)

        self.other = dic
        self.export_list = []


class UVaxis(Common):
    def __init__(self, x, y, z, offset, scale):
        self.x = x
        self.y = y
        self.z = z
        self.offset = offset
        self.scale = scale

    def __str__(self):
        return f"[{self.x} {self.y} {self.z} {self.offset}] {self.scale}"

    def localize(self, side):
        pass

    def export(self):
        return (self.x,
                self.y,
                self.z,
                self.offset,
                self.scale)


class Vector(Common):
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def __str__(self):
        return f"{self.x} {self.y} {self.z}"

    def __add__(self, other):
        return Vector(self.x + other.x, self.y + other.y, self.z + other.z)

    def __mul__(self, other):
        return Vector(self.x * other.x, self.y * other.y, self.z * other.z)

    def dot(self, other):
        t = self * other
        return t.x + t.y + t.z

    def cross(self, other):
        return Vector((self.y*other.z - self.z*other.y),
                      (self.z*other.x - self.x*other.z),
                      (self.x*other.y - self.y*other.x))

    def normalize(self):
        m = self.mag()
        self.x /= m
        self.y /= m
        self.z /= m

    def mag(self):
        return math.sqrt(self.x ** 2 + self.y ** 2 + self.z ** 2)

    def angle(self, other):
        return math.degrees(math.acos(self.dot(other) / (self.mag() * other.mag())))

    def angle_to_origin(self):
        return Vector(-1, 0, 0).angle(self)

    def to_vertex(self):
        return Vertex(self.x, self.y, self.z)

    @classmethod
    def vector_from_2_vertices(cls, v1: Vertex, v2: Vertex):
        return Vector(*(v2-v1).export())


class Hidden(Common):
    NAME = "hidden"

    def __init__(self, dic: dict = None, children: list = None):
        dic, children = self._dic_and_children(dic, children)

        self.other = dic
        self.export_list = []

        self.entity = None
        self.solid = None
        for child in children:
            if str(child) == Entity.NAME:
                self.entity = Entity(child.dic, child.children)

            elif str(child) == Solid.NAME:
                self.solid = Solid(child.dic, child.children)

    def export_children(self):
        return self.entity, self.solid


class Entity(Common):
    NAME = "entity"

    def __init__(self, dic: dict = None, children: list = None):
        dic, children = self._dic_and_children(dic, children)

        self.id = dic.pop("id", self.ids())
        self.classname = dic.pop("classname", "info_player_terrorist")

        self.other = dic
        if "origin" in dic:
            self.other["origin"] = self._string_to_vertex(dic["origin"])
        self.export_list = ["id", "classname"]

        self.connections = []
        self.solid = []
        self.editor = None
        for child in children:
            if str(child) == Solid.NAME:
                self.solid.append(Solid(child.dic, child.children))

            elif str(child) == Editor.NAME:
                self.editor = Editor(child.dic, Entity.NAME)

            elif str(child) == Connections.NAME:
                self.connections.append(Connections(child.dic))

    def export_children(self):
        return (*self.connections, *self.solid, self.editor)


class Connections(Common):
    NAME = "connections"

    def __init__(self, dic: dict = None):
        dic = self._dic(dic)

        self.other = dic
        self.export_list = []


class Cameras(Common):
    NAME = "cameras"

    def __init__(self, dic: dict = None, children: list = None):
        dic, children = self._dic_and_children(dic, children)

        self.activecamera = dic.pop("activecamera", -1)

        self.other = dic
        self.export_list = ["activecamera"]

        self.camera = []
        for child in children:
            self.camera.append(Camera(child.dic))

    def export_children(self):
        return (*self.camera,)


class Camera(Common):
    NAME = "camera"

    def __init__(self, dic: dict = None):
        dic = self._dic(dic)

        self.position = dic.pop("position", "[0 0 0]")
        self.look = dic.pop("look", "[0 0 0]")

        self.other = dic
        self.export_list = ["position", "look"]


class Cordons(Common):
    NAME = "cordons"

    def __init__(self, dic: dict = None, children: list = None):
        dic, children = self._dic_and_children(dic, children)

        self.active = dic.pop("active", 0)

        self.other = dic
        self.export_list = ["active"]

        self.cordon = []
        for child in children:
            self.cordon.append(Cordon(child.dic, child.children))

    def export_children(self):
        return (*self.cordon,)


class Cordon(Common):
    NAME = "cordon"

    def __init__(self, dic: dict = None, children: list = None):
        dic, children = self._dic_and_children(dic, children)

        self.name = dic.pop("name", "default")
        self.active = dic.pop("active", 1)

        self.other = dic
        self.export_list = ["name", "active"]

        self.box = []
        for child in children:
            self.box.append(Box(child.dic))

    def export_children(self):
        return (*self.box,)


class Box(Common):
    NAME = "box"

    def __init__(self, dic: dict = None):
        dic = self._dic(dic)

        self.mins = dic.pop("mins", "(0 0 0)")
        self.maxs = dic.pop("maxs", "(0 0 0)")

        self.other = dic
        self.export_list = ["mins", "maxs"]


class SolidGenerator:
    @staticmethod
    def dev_material(solid, dev):
        if dev == 1:
            solid.set_texture("tools/toolsorigin")
        elif dev == 2:
            solid.set_texture("tools/toolsinvisibleladder")
        elif dev == 3:
            solid.set_texture("tools/toolsdotted")
        elif dev == 4:
            solid.set_texture("tools/bullet_hit_marker")
        elif dev == 5:
            solid.set_texture("tools/toolsblack")

    @staticmethod
    def cube(vertex: Vertex, w, h, l, center=False, dev=0):
        x, y, z = vertex.export()
        f1 = Side(dic={"plane": f"({x + w} {y} {z + l}) ({x + w} {y} {z}) ({x} {y} {z})"})
        f2 = Side(dic={"plane": f"({x + w} {y + h} {z}) ({x + w} {y + h} {z + l}) ({x} {y + h} {z + l})"})
        f3 = Side(dic={"plane": f"({x} {y} {z}) ({x} {y + h} {z}) ({x} {y + h} {z + l})"})
        f4 = Side(dic={"plane": f"({x + w} {y + h} {z}) ({x + w} {y} {z}) ({x + w} {y} {z + l})"})
        f5 = Side(dic={"plane": f"({x} {y} {z + l}) ({x} {y + h} {z + l}) ({x + w} {y + h} {z + l})"})
        f6 = Side(dic={"plane": f"({x} {y + h} {z}) ({x} {y} {z}) ({x + w} {y} {z})"})

        solid = Solid()
        solid.add_sides(f1, f2, f3, f4, f5, f6)
        solid.editor = Editor()

        if center:
            solid.center = Vertex(x, y, z)

        SolidGenerator.dev_material(solid, dev)

        return solid

    @staticmethod
    def displacement_triangle(vertex: Vertex, w, h, l, dev=0):
        x, y, z = vertex.export()
        f1 = Side(dic={"plane": f"({x} {y} {z}) ({x} {y + h} {z}) ({x} {y + h} {z + l})"})
        f2 = Side(dic={"plane": f"({x} {y + h} {z}) ({x} {y} {z}) ({x + w} {y} {z})"})
        f3 = Side(dic={"plane": f"({x} {y} {z + l}) ({x} {y + h} {z + l}) ({x + w} {y} {z + l})"})
        f4 = Side(dic={"plane": f"({x + w} {y} {z + l}) ({x + w} {y} {z}) ({x} {y} {z})"})
        f5 = Side(dic={"plane": f"({x} {y + h} {z + l}) ({x} {y + h} {z}) ({x + w} {y} {z})"})

        solid = Solid()
        solid.add_sides(f1, f2, f3, f4, f5)
        solid.editor = Editor()

        SolidGenerator.dev_material(solid, dev)

        return solid


class VMF:
    info_in_console = False  # Prints info like "VMF loaded", progress bar, etc...

    def __init__(self):
        # EXPORT VARIABLES
        self.__indent = 0  # Keeps track of indent
        self.__size = 0  # The approximate amount of solids (used for the progress bar)
        self.__count = 0  # Progress bar variable
        self.__file = None  # The output file

        # CATEGORIES
        self.versioninfo = None
        self.visgroups = None
        self.viewsettings = None
        self.world = None
        self.entity = []
        self.hidden = []
        self.cameras = None
        self.cordons = None

        # OTHER VARIABLES
        self.file = None

    def get_solids(self, include_hidden=False, include_solid_entities=True):
        li = []
        li.extend(self.world.solid)
        if include_hidden:
            for s in self.world.hidden:
                li.append(s.solid)

        if include_solid_entities:
            for e in self.entity:
                for s in e.solid:
                    li.append(s)

        if include_hidden:
            for h in self.hidden:
                if h.entity is not None:
                    for s in h.entity.solid:
                        li.append(s)

        return li

    def get_entities(self, include_hidden=False, include_solid_entities=False):
        li = []
        if include_hidden:
            for h in self.hidden:
                if h.entity is not None:
                    if not h.entity.solid or include_solid_entities:
                        li.append(h.entity)

        for e in self.entity:
            if not e.solid or include_solid_entities:
                li.append(e)

        return li

    def get_solids_and_entities(self, include_hidden=False, direct_solid_from_entity=True):
        # direct_solid_from_entity is if you want the entity instead of getting directly the solid from the entity
        if direct_solid_from_entity:
            return self.get_solids(include_hidden) + self.get_entities(include_hidden)
        return self.get_solids(include_hidden, False) + self.get_entities(include_hidden, True)

    def get_all_from_visgroup(self, name: str):
        v_id = None
        li = []
        for visgroup in self.visgroups.get_visgroups():
            if visgroup.name == name:
                v_id = visgroup.visgroupid

        if v_id is not None:
            for item in self.get_solids_and_entities(direct_solid_from_entity=False):
                if item.editor.visgroupid == v_id:
                    li.append(item)

        return li

    def get_group_center(self, group: list, geo=False):
        v = Vertex(0, 0, 0)
        for solid in group:
            if geo:
                v = v + solid.center_geo
            else:
                v = v + solid.center
        v.divide(len(group))
        return v

    def sort_by_attribute(self, category_list: list, attr: str):
        return sorted(category_list, key=operator.attrgetter(attr))

    def add_to_visgroup(self, name: str, *args):
        v_id = None
        for visgroup in self.visgroups.get_visgroups():
            if visgroup.name == name:
                v_id = visgroup.visgroupid

        for item in args:
            item.editor.visgroupid = v_id

    def add_solids(self, *args):
        self.world.solid.extend(args)

    def add_entities(self, *args):
        self.entity.extend(args)

    def add_section(self, section: TempCategory):
        name = str(section)
        dic = section.dic
        children = section.children

        if name == VersionInfo.NAME:
            self.versioninfo = VersionInfo(dic)

        elif name == VisGroups.NAME:
            self.visgroups = VisGroups(dic, children)

        elif name == ViewSettings.NAME:
            self.viewsettings = ViewSettings(dic)

        elif name == World.NAME:
            self.world = World(dic, children)

        elif name == Entity.NAME:
            self.entity.append(Entity(dic, children))

        elif name == Hidden.NAME:
            self.hidden.append(Hidden(dic, children))

        elif name == Cameras.NAME:
            self.cameras = Cameras(dic, children)

        elif name == Cordons.NAME:
            self.cordons = Cordons(dic, children)

    def mark_vertex(self, vertex: Vertex, size=32, dev=1, visgroup=None):
        s = SolidGenerator.cube(vertex, size, size, size, True, dev)
        if visgroup is not None:
            print(visgroup)
            self.add_to_visgroup(visgroup, s)
        self.add_solids(s)

    def blank_vmf(self):
        self.versioninfo = VersionInfo()
        self.visgroups = VisGroups()
        self.viewsettings = ViewSettings()
        self.world = World()
        self.cameras = Cameras()
        self.cordons = Cordons()

    def export(self, filename):
        self.__indent = 1  # Represents the indent of the data and not the categories (which use indent-1)

        start_time = time.time()  # To get how long the export took

        if VMF.info_in_console:
            print("Exporting VMF")

            for item in (self.versioninfo, self.visgroups, self.viewsettings, self.world,
                         *self.entity, *self.hidden, self.cameras, self.cordons):
                self._get_export_size(item)  # Gets the total amount of children

            if self.__size == 0:  # We want to avoid division by 0 in progress bar
                self.__size += 1

        # I initially wrote everything to a string, which I then added to the file, turns out writing directly to the
        # file is much faster by a long shot (the biggest file ~31mb takes about 8 seconds, before it took over 5 mins)
        with open(filename, "w+") as self.file:
            for item in (self.versioninfo, self.visgroups, self.viewsettings, self.world,
                         *self.entity, *self.hidden, self.cameras, self.cordons):
                self._nest_export(item)

        if VMF.info_in_console:
            print(f"Done in {round(time.time()-start_time, 3)} seconds")

    def _nest_export(self, category):
        if VMF.info_in_console:
            self._progress()  # Progress bar
        if category is not None:  # Some classes export None (ex: Hidden class export_children function)
            # In the VMF it's first information (ex: id, classname, etc...) then children (ex: side, editor, etc...)
            # I don't know if it's necessary but it makes comparing the exported map to the original much easier
            # This is why I've chosen to keep the same order as the hammer generated VMF for pretty much everything
            self._format_converter(category.NAME, category.export())

            for child in category.export_children():
                self.__count += 1  # For the progress bar
                self.__indent += 1
                self._nest_export(child)  # Recursion
                self.__indent -= 1

            # When there aren't any more children we close the curly brackets
            self.file.write("\t" * (self.__indent-1) + "}\n")

    def _get_export_size(self, category):  # Same concept as _nest_export just without writing to file
        if category is not None:
            for child in category.export_children():
                self.__size += 1
                self._get_export_size(child)

    def _progress(self, suffix=''):  # Some progress bar I found on StackOverflow
        bar_len = 60
        filled_len = int(round(bar_len * self.__count / float(self.__size)))

        percents = round(100.0 * self.__count / float(self.__size), 1)
        bar = '=' * filled_len + '-' * (bar_len - filled_len)

        sys.stdout.write('[%s] %s%s ...%s\r' % (bar, percents, '%', suffix))
        sys.stdout.flush()

    def _format_converter(self, name, info_list):
        # The category name is always one less indent from the data/children, and since self.indent keeps track of the
        # data indent and not the category indent (doesn't matter which one you track as long as it's always the same)
        t = "\t"*(self.__indent-1)
        self.file.write(f"{t}{name}\n{t}{{\n")
        t += "\t"

        for item in info_list:
            if not item:
                continue

            if type(item) is dict:
                for i, j in item.items():
                    self.file.write(f"{t}\"{i}\" \"{str(j)}\"\n")
            else:
                self.file.write(f"{t}\"{item[0]}\" \"{str(item[1])}\"\n")


def load_vmf(name):
    if VMF.info_in_console:
        print("Loading VMF")

    v = VMF()
    f = file_parser(name)
    for section in f:
        v.add_section(section)

    if VMF.info_in_console:
        print("VMF Loaded")
        print("------------------------------")
    return v


def new_vmf():
    v = VMF()
    v.blank_vmf()
    return v
