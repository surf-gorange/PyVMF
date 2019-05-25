import re
from copy import deepcopy
import sys
import time
import math
import operator


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


class Common:
    def export(self):
        d = {}
        for item in self.export_list:
            d[item] = getattr(self, item)
        return d, self.other

    def export_children(self):
        return []

    def copy(self):
        """Copies a category using the copy.deepcopy function"""
        return deepcopy(self)


class VersionInfo(Common):
    NAME = "versioninfo"
    def __init__(self, dic:dict={}):
        self.editorversion = dic.pop("editorversion", 400)
        self.editorbuild = dic.pop("editorbuild", 8075)
        self.mapversion = dic.pop("mapversion", 7)
        self.formatversion = dic.pop("formatversion", 100)
        self.prefab = dic.pop("prefab", 0)

        self.other = dic
        self.export_list = ["editorversion", "editorbuild", "mapversion", "formatversion", "prefab"]


class VisGroups(Common):
    NAME = "visgroups"
    def __init__(self, dic:dict={}, children=[]):
        self.other = dic
        self.export_list = []

        self.visgroup = []
        for child in children:
            self.visgroup.append(VisGroup(child.dic, child.children))

    def new_visgroup(self, name:str):
        self.visgroup.append(VisGroup({"name":name}))

    def get_visgroups(self):
        return self.visgroup

    def export_children(self):
        return (*self.visgroup,)


class VisGroup(Common):
    NAME = "visgroup"
    def __init__(self, dic:dict={}, children=[]):
        self.name = dic.pop("name", "default")
        self.visgroupid = dic.pop("visgroupid", 1)
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
    def __init__(self, dic:dict={}):
        self.bSnapToGrid = dic.pop("bSnapToGrid", 1)
        self.bShowGrid = dic.pop("bShowGrid", 1)
        self.bShowLogicalGrid = dic.pop("bShowLogicalGrid", 0)
        self.nGridSpacing = dic.pop("nGridSpacing", 64)
        self.bShow3DGrid = dic.pop("bShow3DGrid", 0)

        self.other = dic
        self.export_list = ["bSnapToGrid", "bShowGrid", "bShowLogicalGrid", "nGridSpacing", "bShow3DGrid"]


class World(Common):
    NAME = "world"
    def __init__(self, dic:dict={}, children=[]):
        self.id = dic.pop("id", 1)
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

    def __str__(self):
        return f"{self.x} {self.y} {self.z}"

    def __eq__(self, other):
        if self.x == other.x and self.y == other.y and self.z == other.z:
            return True
        return False

    def __add__(self, other):
        return Vertex(self.x + other.x, self.y + other.y, self.z + other.z)

    def divide(self, amount):
        self.x /= amount
        self.y /= amount
        self.z /= amount

    def diff(self, other):
        return self.x - other.x, self.y - other.y, self.z - other.z

    def move(self, x, y, z):
        self.x += x
        self.y += y
        self.z += z

    def set(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def rotate_z(self, center, angle):
        angle = math.radians(angle)
        new_x = center.x + (self.x - center.x)*math.cos(angle) - (self.y - center.y)*math.sin(angle)
        new_y = center.y + (self.x - center.x)*math.sin(angle) + (self.y - center.y)*math.cos(angle)
        self.set(new_x, new_y, self.z)

    def rotate_y(self, center, angle):
        angle = math.radians(angle)
        new_x = center.x + (self.x - center.x) * math.cos(angle) - (self.z - center.z) * math.sin(angle)
        new_z = center.z + (self.x - center.x) * math.sin(angle) + (self.z - center.z) * math.cos(angle)
        self.set(new_x, self.y, new_z)

    def rotate_x(self, center, angle):
        angle = math.radians(angle)
        new_y = center.y + (self.y - center.y) * math.cos(angle) - (self.z - center.z) * math.sin(angle)
        new_z = center.z + (self.y - center.y) * math.sin(angle) + (self.z - center.z) * math.cos(angle)
        self.set(self.x, new_y, new_z)

    def export(self):
        return (self.x,
                self.y,
                self.z)


class Solid(Common):
    NAME = "solid"
    def __init__(self, dic:dict={}, children=[]):
        self.id = dic.pop("id", 1)

        self.other = dic
        self.export_list = ["id"]

        self.side = []
        self.editor = None
        for child in children:
            if str(child) == Side.NAME:
                self.side.append(Side(child.dic, child.children))

            elif str(child) == Editor.NAME:
                self.editor = Editor(child.dic)

    def move(self, x, y, z):
        for side in self.side:
            for vert in side.plane:
                vert.move(x, y, z)

    def rotate_x(self, center, angle):
        for vert in self.get_all_vertices():
            vert.rotate_x(center, angle)

    def rotate_y(self, center, angle):
        for vert in self.get_all_vertices():
            vert.rotate_y(center, angle)

    def rotate_z(self, center, angle):
        for vert in self.get_all_vertices():
            vert.rotate_z(center, angle)

    @property
    def center(self):
        v = Vertex(0, 0, 0)
        counter = 0
        for vert in self.get_only_unique_vertices():
            v = v + vert
            counter += 1
        v.divide(counter)
        return v

    @center.setter
    def center(self, vertex):
        self.move(*vertex.diff(self.center))

    def get_all_vertices(self):
        vertex_list = []
        for side in self.side:
            vertex_list.extend(side.plane)
        return vertex_list

    def get_sides(self):
        return self.side

    def get_displacement_sides(self, matrix_instead_of_side=False):
        l = []
        for side in self.side:
            if side.dispinfo is not None:
                if matrix_instead_of_side:
                    l.append(side.dispinfo.matrix)
                else:
                    l.append(side)
        return l

    def get_only_unique_vertices(self):
        vertex_list = []
        for side in self.side:
            for vertex in side.plane:
                if not vertex in vertex_list:
                    vertex_list.append(vertex)

        return vertex_list

    def has_texture(self, name:str) -> bool:
        for side in self.side:
            if side.material == name.upper():
                return True
        return False

    def replace_texture(self, old_material:str, new_material:str):
        for side in self.side:
            if side.material == old_material:
                side.material = new_material

    def export_children(self):
        return (*self.side, self.editor)


class Editor(Common):
    NAME = "editor"
    def __init__(self, dic:dict={}, parent_type=None):
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

    def _string_to_color(self, string):
        temp = string.split()
        return [int(i) for i in temp]

    def _list_to_color(self, lis):
        return f"{lis[0]} {lis[1]} {lis[2]}"

    def has_visgroup(self) -> bool:
        if self.visgroupid is None:
            return False
        else:
            return True

    def export(self):
        d = {}
        d["color"] = self._list_to_color(self.color)
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
    def __init__(self, dic:dict={}, children=[]):
        self.id =dic.pop("id", 1)

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
    def __init__(self, dic:dict={}, children=[]):
        self.id = dic.pop("id", 1)

        t = self._string_to_3x_vertex(dic.pop("plane"))
        self.plane = (Vertex(t[0], t[1], t[2]),
                      Vertex(t[3], t[4], t[5]),
                      Vertex(t[6], t[7], t[8]))

        self.material = dic.pop("material", "TOOLS/TOOLSNODRAW")
        self.uaxis = dic.pop("uaxis")
        self.vaxis = dic.pop("vaxis")
        self.rotation = dic.pop("rotation", 0)
        self.lightmapscale = dic.pop("lightmapscale", 16)
        self.smoothing_groups = dic.pop("smoothing_groups", 0)

        self.other = dic
        self.export_list = []

        self.dispinfo = None
        for child in children:
            if str(child) == DispInfo.NAME:
                self.dispinfo = DispInfo(child.dic, child.children)

    def get_vertices(self):
        return self.plane

    def get_displacement(self):
        return self.dispinfo

    def _string_to_3x_vertex(self, string):
        reg = re.sub('[(){}<>]', '', string).split()
        clean = []
        for i in reg:
            clean.append(num(i))
        return clean

    def _plane_to_string(self):
        return f"({self.plane[0]}) ({self.plane[1]}) ({self.plane[2]})"

    def export(self):
        d = {"id" : self.id,
             "plane" : self._plane_to_string(),
             "material" : self.material,
             "uaxis" : self.uaxis,
             "vaxis" : self.vaxis,
             "rotation" : self.rotation,
             "lightmapscale" : self.lightmapscale,
             "smoothing_groups" : self.smoothing_groups}

        return d, self.other

    def export_children(self):
        return [self.dispinfo]


class DispInfo(Common):
    NAME = "dispinfo"
    def __init__(self, dic:dict={}, children=[]):
        self.power = dic.pop("power", 3)
        self.startposition = dic.pop("startposition", "[0 0 0]")
        self.flags = dic.pop("flags", 0)
        self.elevation = dic.pop("elevation", 0)
        self.subdiv = dic.pop("subdiv", 0)

        fix = 0
        if self.power == 2 or self.power == 4:
            fix = 1
        self.matrix = Matrix(self.power**2+fix)

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

    def move(self, normal, distance):
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
    def __init__(self, size:int):
        self.size = size
        self.matrix = [[DispVert() for y in range(self.size)] for x in range(self.size)]

    def __str__(self):
        return str(self.matrix)

    def get(self, x, y):
        return self.matrix[x][y]

    def row(self, y):
        l = []
        for x in range(self.size):
            l.append(self.matrix[x][y])
        return l

    def _extract_dic(self, dic, a_var=1, triangle=False):
        for y in range(self.size - triangle):
            t = dic.pop(f"row{y}").split(" ")
            for x in range((self.size - triangle) * a_var):
                yield x, y, t

    def _export(self, attribute):
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
    def __init__(self, matrix, dic:dict={}):
        self.matrix = matrix
        a_var = 3
        i = 0
        for x, y, t in self.matrix._extract_dic(dic, a_var):
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
        return self.matrix._export("normal"), self.other


class Distances(Common):
    NAME = "distances"
    def __init__(self, matrix, dic:dict={}):
        self.matrix = matrix
        for x, y, t in self.matrix._extract_dic(dic):
            self.matrix.get(x, y).distance = num(t[x])

        self.other = dic
        self.export_list = []

    def export(self):
        return self.matrix._export("distance"), self.other


class Offsets(Common):
    NAME = "offsets"
    def __init__(self, matrix, dic:dict={}):
        self.matrix = matrix
        a_var = 3
        i = 0
        for x, y, t in self.matrix._extract_dic(dic, a_var):
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
        return self.matrix._export("offset"), self.other


class OffsetNormals(Common):
    NAME = "offset_normals"
    def __init__(self, matrix, dic:dict={}):
        self.matrix = matrix
        a_var = 3
        i = 0
        for x, y, t in self.matrix._extract_dic(dic, a_var):
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
        return self.matrix._export("offset_normal"), self.other


class Alphas(Common):
    NAME = "alphas"
    def __init__(self, matrix, dic:dict={}):
        self.matrix = matrix
        for x, y, t in self.matrix._extract_dic(dic):
            self.matrix.get(x, y).alpha = num(t[x])

        self.other = dic
        self.export_list = []

    def export(self):
        return self.matrix._export("alpha"), self.other


class TriangleTags(Common):
    NAME = "triangle_tags"
    def __init__(self, matrix, dic:dict={}):
        self.matrix = matrix  # TriangleTags is 1 row and column smaller than the others
        a_var = 2
        i = 0
        t1 = 0
        for x, y, t in self.matrix._extract_dic(dic, a_var, True):
            if i == 0:
                t1 = num(t[x])
            else:
                self.matrix.get(x // a_var, y).triangle_tag = TriangleTag(t1, num(t[x]))
                i = -1
            i += 1

        self.other = dic
        self.export_list = []

    def export(self):
        return self.matrix._export("triangle_tag"), self.other


class AllowedVerts(Common):
    NAME = "allowed_verts"
    def __init__(self, matrix, dic:dict={}):
        self.other = dic
        self.export_list = []


class UVaxis(Common):
    def __init__(self, x, y, z, dec, dec2):
        self.x = x
        self.y = y
        self.z = z
        self.dec = dec
        self.dec2 = dec2

    def export(self):
        return (self.x,
                self.y,
                self.z,
                self.dec,
                self.dec2)


class Hidden(Common):
    NAME = "hidden"
    def __init__(self, dic:dict=[], children=[]):
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
    def __init__(self, dic:dict={}, children=[]):
        self.id = dic.pop("id", 1)
        self.classname = dic.pop("classname", "info_player_terrorist")

        self.other = dic
        if "origin" in dic:
            reg = re.sub('[(){}<>]', '', dic["origin"]).split()
            self.other["origin"] = Vertex(num(reg[0]), num(reg[1]), num(reg[2]))
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
    def __init__(self, dic:dict={}):
        self.other = dic
        self.export_list = []


class Cameras(Common):
    NAME = "cameras"
    def __init__(self, dic:dict={}, children=[]):
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
    def __init__(self, dic:dict={}):
        self.position = dic.pop("position", "[0 0 0]")
        self.look = dic.pop("look", "[0 0 0]")

        self.other = dic
        self.export_list = ["position", "look"]


class Cordons(Common):
    NAME = "cordons"
    def __init__(self, dic:dict={}, children=[]):
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
    def __init__(self, dic:dict={}, children=[]):
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
    def __init__(self, dic:dict={}):
        self.mins = dic.pop("mins", "(0 0 0)")
        self.maxs = dic.pop("maxs", "(0 0 0)")

        self.other = dic
        self.export_list = ["mins", "maxs"]


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

    def get_solids(self, include_hidden=False):
        l = []
        l.extend(self.world.solid)
        if include_hidden:
            for s in self.world.hidden:
                l.append(s.solid)

        for e in self.entity:
            for s in e.solid:
                l.append(s)

        if include_hidden:
            for h in self.hidden:
                if h.entity is not None:
                    for s in h.entity.solid:
                        l.append(s)

        return l

    def get_entities(self, include_hidden=False):
        l = []
        if include_hidden:
            for h in self.hidden:
                if h.entity is not None:
                    if not h.entity.solid:
                        l.append(h.entity)

        for e in self.entity:
            if not e.solid:
                l.append(e)

        return l

    def get_solids_and_entities(self, include_hidden=False):
        return self.get_solids(include_hidden) + self.get_entities(include_hidden)

    def get_all_from_visgroup(self, name:str):
        v_id = None
        l = []
        for visgroup in self.visgroups.get_visgroups():
            if visgroup.name == name:
                v_id = visgroup.visgroupid

        if v_id is not None:
            for item in self.get_solids_and_entities():
                if item.editor.visgroupid == v_id:
                    l.append(item)

        return l

    def sort_by_attribute(self, category_list:list, attr:str):
        return sorted(category_list, key=operator.attrgetter(attr))

    def add_to_visgroup(self, name:str, *args):
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

    def _add_section(self, section:TempCategory):
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

    def _blank_vmf(self):
        self.versioninfo = VersionInfo()
        self.visgroups = VisGroups()
        self.viewsettings = ViewSettings()
        self.world = World()
        self.cameras = Cameras()
        self.cordons = Cordons()

    def export(self, filename):
        self.__indent = 1  # Represents the indent of the data and not the categories (which use indent-1)

        if VMF.info_in_console:
            print("Exporting VMF")

            start_time = time.time()  # To get how long the export took

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
            if not item: continue

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
        v._add_section(section)

    if VMF.info_in_console:
        print("VMF Loaded")
        print("------------------------------")
    return v

def new_vmf():
    v = VMF()
    v._blank_vmf()
    return v
