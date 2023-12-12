import bpy
import random
import bmesh
import mathutils
from mathutils.bvhtree import BVHTree
from Modifications.Modification import Modification

def hide_obj_and_children(obj):
    for child in obj.children:
        hide_obj_and_children(child)
    obj.hide_render = True

def show_obj_and_children(obj):
	for child in obj.children:
		show_obj_and_children(child)
	obj.hide_render = False

# currently hyde_on_intersection works on all other children of the same parent - change that to accept other objects
class ShufflePos(Modification):
	def __init__(self, range=[], objects=[], hide_on_intersection = True, multi_range = False, scale_with = ""):
		self.hide = hide_on_intersection
		self.Range = range
		self.multiRange = multi_range
		self.scale_with = scale_with
		super(ShufflePos, self).__init__(objects)

	def performAction(self):
		random.shuffle(self.Objects)
		for obj in self.Objects:
			self.Action(obj)

			if self.hide:
				obj.hide_render = False
			else:
				continue
			parent =  obj.parent
			if parent is None:
				object_check = self.Objects
			else:
				object_check = parent.children
			#for obj_check in object_check:
				# if obj_check.hide_render == False and obj_check.name != obj.name and obj_check.type != 'CAMERA' :
				# 	check = self.are_objects_intersecting(obj, obj_check)
				# 	if check:
				# 		hide_obj_and_children(obj)
				# 		print("\n ____ Hiding ", obj.name, " because it intersects with ", obj_check.name, " ! \n")
				# 		bpy.context.view_layer.update()
				# 		continue
				# if obj.hide_render == False:
				# 	object_check.append(obj)
		bpy.context.view_layer.update()

	def are_objects_intersecting(self, obj1, obj2):
		BMESH_1 = bmesh.new()
		BMESH_1.from_mesh(obj1.data)
		BMESH_1.transform(obj1.matrix_world)
		BVHtree_1 = BVHTree.FromBMesh(BMESH_1)

		BMESH_2 = bmesh.new()
		BMESH_2.from_mesh(obj2.data)
		BMESH_2.transform(obj2.matrix_world)
		BVHtree_2 = BVHTree.FromBMesh(BMESH_2)

		inter = BVHtree_1.overlap(BVHtree_2)
			#if list is empty, no objects are touching
		if inter != []:
			return True
		else:
			return False		

class ShuffleXPos(ShufflePos):
	def Action(self, obj):
		obj.hide_render = True
		used_range = list(self.Range)
		scale = 1

		if (self.scale_with == "X"):
			scale = abs(obj.location.x)
		if (self.scale_with == "Y"):
			scale = abs(obj.location.y)
		if (self.scale_with == "Z"):
			scale = abs(obj.location.z)
		
		for idx, item in enumerate(used_range):
			used_range[idx] = item * scale

		if self.multiRange:
			used_range = random.choice(used_range)
			if isinstance(Range, list): 
				obj.location.x =  random.uniform((used_range[0], used_range[1]))
			else:
				obj.location.x = used_range
			bpy.context.view_layer.update()
		else:
			obj.location.x = random.uniform(used_range[0], used_range[1])
			obj.hide_render = True
				
			bpy.context.view_layer.update()

class ShuffleYPos(ShufflePos):
	def Action(self, obj):
		obj.hide_render = True
		used_range = list(self.Range)
		scale = 1

		if (self.scale_with == "X"):
			scale = abs(obj.location.x)
		if (self.scale_with == "Y"):
			scale = abs(obj.location.y)
		if (self.scale_with == "Z"):
			scale = abs(obj.location.z)
		
		for idx, item in enumerate(used_range):
			used_range[idx] = item * scale

		if self.multiRange:
			used_range = random.choice(used_range)
			if isinstance(Range, list): 
				obj.location.y =  random.uniform((used_range[0], used_range[1]))
			else:
				obj.location.y = used_range
			bpy.context.view_layer.update()
		else:
			obj.location.y = random.uniform(used_range[0], used_range[1])

			obj.hide_render = True

			bpy.context.view_layer.update()

class ShuffleZPos(ShufflePos):
	def Action(self, obj):
		obj.hide_render = False
		used_range = list(self.Range)
		scale = 1

		if (self.scale_with == "X"):
			scale = abs(obj.location.x)
		if (self.scale_with == "Y"):
			scale = abs(obj.location.y)
		if (self.scale_with == "Z"):
			scale = abs(obj.location.z)
		
		for idx, item in enumerate(used_range):
			used_range[idx] = item * scale
			
		if self.multiRange:
			used_range = random.choice(used_range)
			if isinstance(Range, list): 
				obj.location.z =  random.uniform((used_range[0], used_range[1]))
			else:
				obj.location.z = used_range
			bpy.context.view_layer.update()
		else:
			obj.location.z = random.uniform(used_range[0], used_range[1])
			bpy.context.view_layer.update()
