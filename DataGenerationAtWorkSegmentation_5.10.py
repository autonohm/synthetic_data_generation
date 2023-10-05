
import sys
import os
from sys import platform

import bpy, os
from math import sin, cos, pi
import numpy as np
import sys
import random
from datetime import datetime
#import toml

sys.path.append('/home/florian/.local/lib/python3.8/site-packages')
import toml
import random
import yaml
import numpy


base_dir = os.path.dirname(bpy.data.filepath)
dir = base_dir

if not dir in sys.path:
	sys.path.append(dir)

import boundingBox
import checkVisibility
import BOP
import GetCameraMatrixK
from Modifications.ShufflePos import ShuffleXPos, ShuffleYPos, ShuffleZPos
from Modifications.ShuffleRotEuler import ShuffleXRotEuler, ShuffleYRotEuler, ShuffleZRotEuler
from Modifications.ShuffleRotQuaternion import ShuffleRotQuaternion
from Modifications.ShuffleColor import ShuffleRGBColor, ShuffleBackground, ShuffleImageTexture, ShuffleColorSpace
from Modifications.Mask import HideInRGB, Mask, MaskComposition
from Modifications.RandomMods import RandomDisappear
from Modifications.CameraMods import ShuffleFocalLength
from Modifications.ShuffleMaterial import ShuffleMaterials, ShuffleMaterialProperties
from Modifications.ShuffleVector import ShuffleVector

from Modifications.MeshMods import CreateHull

## Global variables cause things are getting messy 
base_config = "/home/florian/Desktop/DataGenAtworkSegmentation/configAtWork.toml"
config = toml.load(base_config)

def hide_obj_and_children(obj):
	for child in obj.children:
		hide_obj_and_children(child)
	obj.hide_render = True

def show_obj_and_children(obj):
	for child in obj.children:
		show_obj_and_children(child)
	obj.hide_render = False

def calcVisibilityThresh(obj, config):
	visibility_thresh = config[obj.name]["visibility_thresh_factor"]
	factor = obj.location.z / 2 + visibility_thresh
	return min(factor, 0.8)





def hideInvisibleObjects(scene, camera_object, visibility_camera, mesh_objects, config):
	print ("visibility checks disabled")
	# for object in mesh_objects:
	# 	if object.hide_render == True:
	# 		print(object.name + " is hidden - not labeling this and hiding all children!")
	# 		hide_obj_and_children(object)
	# 		continue
		
		
		# if "visibility_thresh_factor" in config[object.name]:
		#   checkVisibility.select_camera_view(scene, visibility_camera, object)
		#   visibility = checkVisibility.check_visibility(scene, visibility_camera, object)
		#   checkVisibility.restore_camera(scene, camera_object)

		#   # Objekte werden auch zufällig ausgeblendet sonst gibts chaos
		#   #zufall_hide = random.uniform(0.0, 1.0)
		#   #if zufall_hide > 0.5:
		#   	#hide_obj_and_children(object)
		#   	#continue 

		#   if visibility <  config[object.name]["visibility_thresh_factor"]:
		
		#   	print(object.name, "visibilitiy is ", visibility, " -> not visible in render - HIDING this and all children")
		#   	hide_obj_and_children(object)

# ____________________________________________ Create image

def render(scene, camera_object, mesh_objects, path="/home/data/", file_prefix="rgb"):
	# Rendering
	# https://blender.stackexchange.com/questions/1101/blender-rendering-automation-build-script

	filename = str(file_prefix)
	bpy.context.scene.render.filepath = os.path.join(path,  filename + '.png')
	bpy.ops.render.render(write_still=True)

# ____________________________________________ Create labels

def createYoloTxtFile(scene, camera_object, visibility_camera, mesh_objects, config, path="/home/data/", file_prefix="bbox", bounds=None):
	random.shuffle(mesh_objects)
	filename = str(file_prefix)

	path = os.path.join(path, filename + '.txt')
	with open(path, 'w+') as file:
		""" Get the bounding box coordinates for each mesh """
		for object in mesh_objects:
			if object.hide_render == False:
				if not object.name in config['Labels']:
					print(object.name + " has no label - not labeling this!")
					continue			

				name = config['Labels'][object.name]
				show_obj_and_children(object)
				bounding_box = boundingBox.camera_view_bounds_2d(scene, camera_object, object, bounds)
				if bounding_box:
					new_line = str(name) + " " + str(bounding_box[0])+ " " + str(bounding_box[1]) + " " + str(bounding_box[2]) + " " + str(bounding_box[3]) + '\n'
					file.write(new_line)

				else: 
					hide_obj_and_children(object)
					print("Hiding ", object.name, " and all children in YoloTXT_File")


def createBopTxtFile(scene, camera_object, visibility_camera, mesh_objects, config, path="/home/data/", file_prefix="bop", bounds=None, store_in_one_file = True, K = None):
	filename = str(file_prefix)
		 
	if(store_in_one_file):
		ground_truth_file = os.path.join(path, 'gt.yml')
		camera_info_file = os.path.join(path, 'info.yml')
		
	else:
		ground_truth_file = os.path.join(path, str(file_prefix), '_gt.yml')
		camera_info_file = os.path.join(path, str(file_prefix),'_info.yml')

	if not os.path.isfile(ground_truth_file):
		f = open(ground_truth_file, 'w+')
		f.close

	if not os.path.isfile(camera_info_file):
		f = open(camera_info_file, 'w+')
		f.close

	# using int instead of string for efficientpose
	prefix = int(file_prefix)

	#Prepare to open the file with reading capabilities
	with open(ground_truth_file,'r') as infile:
		infile.seek(0)
		file_data = yaml.load(infile, Loader=yaml.Loader)
		if not file_data:
			file_data =  dict()

	for object in mesh_objects:
		if not object.name in config['Labels']:
			continue
		
		if object.hide_render == True:
			continue

		name = config['Labels'][object.name]

		pos = BOP.get_relative_object_position(scene, camera_object, object)
		pos = [round(element * 1000,2) for element in pos]
		
		#pos[2] = pos[2] * -1

		rot = BOP.get_relative_object_rotation(scene, camera_object, object)

		rot_list = np.concatenate( rot.tolist(), axis=0 )
		
		new_data = dict(
				cam_R_m2c = rot_list.tolist(),
				cam_t_m2c = pos,
				obj_id = name
			)
		#print(new_data)
		
		try: 
			#print(file_data[prefix])
			file_data[prefix].append(new_data)
			#print(file_data[prefix])
		except:
			#print(file_data[prefix])
			file_data[prefix] =  list()
			file_data[prefix].append(new_data)
			#print(file_data[prefix])

		#print("\n ______")
		#for efficient pose - otherwise write new_data diredctly
		#data_array = list()
		#data_array.append(new_data)
		#file_data[prefix] = data_array 		

	#print(file_data)
	with open(ground_truth_file, "w") as f:
		yaml.safe_dump(file_data, f, default_flow_style=False)

	print("Wrote ground truth to ", ground_truth_file)


	#Prepare to open the file with reading capabilities
	with open(camera_info_file,'r') as infile:
		infile.seek(0)
		file_data = yaml.load(infile, Loader=yaml.Loader)

	for object in mesh_objects:
		if not object.name in config['Labels']:
			continue

		name = config['Labels'][object.name]

		cam_data = GetCameraMatrixK.get_calibration_matrix_K_from_blender(camera_object.data)

		k_matrix = np.concatenate( cam_data, axis=0 )


		new_data = dict(
				cam_K = k_matrix.tolist(),
				depth_scale = 1
			)
	
		if not file_data:
				file_data =  dict()
			
		file_data[prefix] = new_data			

	with open(camera_info_file, "w") as f:
		yaml.safe_dump(file_data, f, default_flow_style=False)
	
	print("Wrote camera info to ", camera_info_file)

# ____________________________________________ Create Modification

def createCameraMods(camera):
	mods = list()
	cameras = list()
	cameras.append(camera)
	#modFocalLength = ShuffleFocalLength([11, 38], cameras)
	#mods.append(modFocalLength)
	modZRot = ShuffleZRotEuler([0, 360], cameras, False)
	mods.append(modZRot)
	modXRot = ShuffleXRotEuler([0, 360], cameras, False)
	mods.append(modXRot)
	modYRot = ShuffleYRotEuler([0, 360], cameras, False)
	mods.append(modYRot)
	return mods

def createLightMods(lights):
	mods = list()
	modXPos = ShuffleXPos([-200, 200], lights, False)
	mods.append(modXPos)
	modYPos = ShuffleYPos([-200, 200], lights, False)
	mods.append(modYPos)
	return mods

def createDecoyMods(decoy, config):
	mods = list()

	for obj in decoy:
		obj_list = list()
		obj_list.append(obj)

		if "Rotation" in config[obj.name]:

			modZRot = ShuffleZRotEuler(config[obj.name]["Rotation"]["Z"], obj_list, False)
			mods.append(modZRot)
			modYRot = ShuffleYRotEuler(config[obj.name]["Rotation"]["Y"], obj_list, False)
			mods.append(modYRot)
			modXRot = ShuffleXRotEuler(config[obj.name]["Rotation"]["X"], obj_list, False)
			mods.append(modXRot)

		if "Position" in config[obj.name]:
			
			modZPos = ShuffleZPos(config[obj.name]["Position"]["Z"], obj_list, False, False, config[obj.name]["Position"]["Z_normed_to_1m"])
			mods.append(modZPos)

			modXPos = ShuffleXPos(config[obj.name]["Position"]["X"], obj_list, False, False, config[obj.name]["Position"]["X_normed_to_1m"])
			mods.append(modXPos)
			modYPos = ShuffleYPos(config[obj.name]["Position"]["Y"], obj_list, True, False, config[obj.name]["Position"]["Y_normed_to_1m"])
			mods.append(modYPos)
		
		modMetallic = ShuffleMaterialProperties(obj_list, "Principled BSDF", "Metallic", config[obj.name]["PrincipledBSDF"]["Metallic"])
		mods.append(modMetallic)

		modSpecular = ShuffleMaterialProperties(obj_list, "Principled BSDF", "Specular", config[obj.name]["PrincipledBSDF"]["Specular"])
		mods.append(modSpecular)

		modSpecularTint = ShuffleMaterialProperties(obj_list, "Principled BSDF", "Specular Tint", config[obj.name]["PrincipledBSDF"]["SpecularTint"])
		mods.append(modSpecularTint)

		modRoughness = ShuffleMaterialProperties(obj_list, "Principled BSDF", "Roughness", config[obj.name]["PrincipledBSDF"]["Roughness"])
		mods.append(modRoughness)

		modAnisotropic = ShuffleMaterialProperties(obj_list, "Principled BSDF", "Anisotropic", config[obj.name]["PrincipledBSDF"]["Anisotropic"])
		mods.append(modAnisotropic)

		modAnisotropicRotation = ShuffleMaterialProperties(obj_list, "Principled BSDF", "Anisotropic Rotation", config[obj.name]["PrincipledBSDF"]["AnisotropicRotation"])
		mods.append(modAnisotropicRotation)

		modClearcoat = ShuffleMaterialProperties(obj_list, "Principled BSDF", "Clearcoat", config[obj.name]["PrincipledBSDF"]["Clearcoat"])
		mods.append(modClearcoat)

		modClearcoatRoughness = ShuffleMaterialProperties(obj_list, "Principled BSDF", "Clearcoat Roughness", config[obj.name]["PrincipledBSDF"]["ClearcoatRoughness"])
		mods.append(modClearcoatRoughness)
			
		if "ShuffleMaterials" in config[obj.name]:
			modShuffleMaterials = ShuffleMaterials(obj_list)
			mods.append(modShuffleMaterials)


	
		if "ShuffleMaterialConfig" in config[obj.name]:
			for key in config[obj.name]["ShuffleMaterialConfig"]:
				sub_config  = config[obj.name]["ShuffleMaterialConfig"][key]
				print(sub_config)
				mod = ShuffleMaterialProperties(obj_list, sub_config["NodeName"], sub_config["PropertyName"], sub_config["value"], sub_config["material_name"])
				mods.append(mod)
		
		if "Color" in config[obj.name]:
			try:
				for key in config[obj.name]["Color"]:
					color_config  = config[obj.name]["Color"][key]
					print(color_config)
					modShuffleColor = ShuffleRGBColor(obj_list, color_config["NodeName"], color_config["PropertyName"], color_config["value1"],color_config["value2"],color_config["value3"], color_config["mode"], color_config["material_name"])
					mods.append(modShuffleColor)
					print("Shuffling color with keys for ", obj.name)
			except:
				color_config  = config[obj.name]["Color"]
				modShuffleColor = ShuffleRGBColor(obj_list, color_config["NodeName"], color_config["PropertyName"], color_config["value1"],color_config["value2"],color_config["value3"], color_config["mode"], color_config["material_name"])
				mods.append(modShuffleColor)
				print("Shuffling color for ", obj.name)

		if "Disappear" in config[obj.name]:
			modDisappear = RandomDisappear(obj_list, config[obj.name]["Disappear"]["value"])
			mods.append(modDisappear)

		#else:
			#print("no color config for ", obj.name)

		#modDisappear = RandomDisappear(decoy, 0.3)
		#mods.append(modDisappear)

		print("Added decoy ", obj.name)
	return mods

def createSpecialObjectMods(special, config):
	mods = list()


	#modZRot = ShuffleZRotEuler([0, 360], special, False)
	#mods.append(modZRot)

	modZRot = ShuffleZRotEuler([-25, 25], special, False)
	mods.append(modZRot)
	modYRot = ShuffleYRotEuler([-30, 30], special, False)
	mods.append(modYRot)
	modXRot = ShuffleXRotEuler([-90, -30], special, False)
	mods.append(modXRot)

	modZPos = ShuffleZPos([-0.3, -0.2], special, False, False)
	mods.append(modZPos)

	modXPos = ShuffleXPos([-0.15, 0.15], special, False, False, False)
	mods.append(modXPos)
	modYPos = ShuffleYPos([-0.3, -0.2], special, True, True, False)
	mods.append(modYPos)

	#modDisappear = RandomDisappear(special, config[obj.name]["Disappear"]["value"])
	modDisappear = RandomDisappear(special, 0.3)

	#mods.append(modDisappear)

	#mods.append(modZPos)
	for obj in special:

		print("adding mods for special obj ", obj.name)
		obj_list = list()
		obj_list.append(obj)
		
		modMetallic = ShuffleMaterialProperties(obj_list, "Principled BSDF", "Metallic", config[obj.name]["PrincipledBSDF"]["Metallic"])
		mods.append(modMetallic)

		modSpecular = ShuffleMaterialProperties(obj_list, "Principled BSDF", "Specular", config[obj.name]["PrincipledBSDF"]["Specular"])
		mods.append(modSpecular)

		modSpecularTint = ShuffleMaterialProperties(obj_list, "Principled BSDF", "Specular Tint", config[obj.name]["PrincipledBSDF"]["SpecularTint"])
		mods.append(modSpecularTint)

		modRoughness = ShuffleMaterialProperties(obj_list, "Principled BSDF", "Roughness", config[obj.name]["PrincipledBSDF"]["Roughness"])
		mods.append(modRoughness)

		modAnisotropic = ShuffleMaterialProperties(obj_list, "Principled BSDF", "Anisotropic", config[obj.name]["PrincipledBSDF"]["Anisotropic"])
		mods.append(modAnisotropic)

		modAnisotropicRotation = ShuffleMaterialProperties(obj_list, "Principled BSDF", "Anisotropic Rotation", config[obj.name]["PrincipledBSDF"]["AnisotropicRotation"])
		mods.append(modAnisotropicRotation)

		modClearcoat = ShuffleMaterialProperties(obj_list, "Principled BSDF", "Clearcoat", config[obj.name]["PrincipledBSDF"]["Clearcoat"])
		mods.append(modClearcoat)

		modClearcoatRoughness = ShuffleMaterialProperties(obj_list, "Principled BSDF", "Clearcoat Roughness", config[obj.name]["PrincipledBSDF"]["ClearcoatRoughness"])
		mods.append(modClearcoatRoughness)
			
		if "ShuffleMaterials" in config[obj.name]:
			modShuffleMaterials = ShuffleMaterials(obj_list)
			mods.append(modShuffleMaterials)

	
		if "ShuffleMaterialConfig" in config[obj.name]:
			for key in config[obj.name]["ShuffleMaterialConfig"]:
				sub_config  = config[obj.name]["ShuffleMaterialConfig"][key]
				print(sub_config)
				mod = ShuffleMaterialProperties(obj_list, sub_config["NodeName"], sub_config["PropertyName"], sub_config["value"], sub_config["material_name"])
				mods.append(mod)

		if "Color" in config[obj.name]:
			try:
				for key in config[obj.name]["Color"]:
					color_config  = config[obj.name]["Color"][key]
					print(color_config)
					modShuffleColor = ShuffleRGBColor(obj_list, color_config["NodeName"], color_config["PropertyName"], color_config["value1"],color_config["value2"],color_config["value3"], color_config["mode"], color_config["material_name"])
					mods.append(modShuffleColor)
					print("Shuffling color with keys for ", obj.name)
			except:
				color_config  = config[obj.name]["Color"]
				modShuffleColor = ShuffleRGBColor(obj_list, color_config["NodeName"], color_config["PropertyName"], color_config["value1"],color_config["value2"],color_config["value3"], color_config["mode"], color_config["material_name"])
				mods.append(modShuffleColor)
				print("Shuffling color for ", obj.name)

	
	return mods

def createObjectMods(objects, config):
	mods = list()

	distance_z = random.uniform(0.4, 0.8)
	modZPos = ShuffleZPos([-distance_z, -distance_z], objects, True, False)

	fov_x_rad = (53.3/2)*(pi/180) #53
	print ("winkel x in rad", fov_x_rad)
	fov_y_rad =   (40.4/2)*(pi/180)  #41

	visible_range_x = numpy.arctan(fov_x_rad)* distance_z
	print ("visible range x:", visible_range_x, "z_pos: ", distance_z)
	visible_range_y = (3/4) * visible_range_x

	object_position_x = visible_range_x/2
	object_position_y = visible_range_y/2
	print( "object position x:", object_position_x)

	obj_list_random = sorted(objects, key=lambda x: random.random())
	number_of_objects = len(obj_list_random)
	objects_to_place = 4
	already_placed_objects = 0
	#lenght of the largest object is 20,5 cm


	for obj in obj_list_random:
		x= random.uniform(100,1000)
		y = x

		obj_list = list()
		obj_list.append(obj)

		modZPos = ShuffleZPos([-distance_z, -distance_z], obj_list, True, False)
		mods.append(modZPos)

		
		if already_placed_objects==0:
			x = -object_position_x; y = object_position_y; 
			
			print( "Placed Object NR.1:", obj.name)
		elif already_placed_objects==1:
			x = object_position_x; y = object_position_y; 
			print( "Placed Object NR.2:", obj.name)
		elif already_placed_objects==2:
			x = -object_position_x; y = -object_position_y; 
			print( "Placed Object NR.3:", obj.name)
		elif already_placed_objects==3:
			x = + object_position_x; y = - object_position_y
			print( "Placed Object NR.4:", obj.name)
		already_placed_objects+=1
			
		#Debug Output	
		#print ("placing: ", obj.name,"already_placed_objects:", already_placed_objects, "x:", x, " y:",y)
			
		
		modXPos = ShuffleXPos([x, x], obj_list, True, False)
		mods.append(modXPos)

		modYPos = ShuffleYPos([y, y], obj_list, True, False)
		mods.append(modYPos)
		

		# if "Rotation" in config[obj.name]:

		# 	print(config[obj.name]["Rotation"])
		# 	try:
		# 		if config[obj.name]["Rotation"]["mode"] == "Quaternion":
		# 				modQuatRot = ShuffleRotQuaternion(config[obj.name]["Rotation"]["X"],config[obj.name]["Rotation"]["Y"], config[obj.name]["Rotation"]["Z"], obj_list, False)
		# 				mods.append(modQuatRot)
		# 				print("Using quaternions for ", obj.name)
		# 	except:
		# 		# modZRot = ShuffleZRotEuler([0,0], obj_list, False)
		# 		# mods.append(modZRot)
		# 		# modYRot = ShuffleYRotEuler([0,0], obj_list, False)
		# 		# mods.append(modYRot)
		# 		# modXRot = ShuffleXRotEuler([0,0], obj_list, False)
		# 		# mods.append(modXRot)
		# 		# print("Using axis rotation for ", obj.name)
		# 		#modZRot = ShuffleZRotEuler(config[obj.name]["Rotation"]["Z"], obj_list, False)
		# 		#mods.append(modZRot)
		# 		modYRot = ShuffleYRotEuler(config[obj.name]["Rotation"]["Y"], obj_list, False)
		# 		mods.append(modYRot)
		# 		modXRot = ShuffleXRotEuler(config[obj.name]["Rotation"]["X"], obj_list, False)
		# 		mods.append(modXRot)
		# 		print("Using axis rotation for ", obj.name)

		

		if "PrincipledBSDF" in config[obj.name]:
			
			modMetallic = ShuffleMaterialProperties(obj_list, "Principled BSDF", "Metallic", config[obj.name]["PrincipledBSDF"]["Metallic"])
			mods.append(modMetallic)

			modSpecular = ShuffleMaterialProperties(obj_list, "Principled BSDF", "Specular", config[obj.name]["PrincipledBSDF"]["Specular"])
			mods.append(modSpecular)

			modSpecularTint = ShuffleMaterialProperties(obj_list, "Principled BSDF", "Specular Tint", config[obj.name]["PrincipledBSDF"]["SpecularTint"])
			mods.append(modSpecularTint)

			modRoughness = ShuffleMaterialProperties(obj_list, "Principled BSDF", "Roughness", config[obj.name]["PrincipledBSDF"]["Roughness"])
			mods.append(modRoughness)

			modAnisotropic = ShuffleMaterialProperties(obj_list, "Principled BSDF", "Anisotropic", config[obj.name]["PrincipledBSDF"]["Anisotropic"])
			mods.append(modAnisotropic)

			modAnisotropicRotation = ShuffleMaterialProperties(obj_list, "Principled BSDF", "Anisotropic Rotation", config[obj.name]["PrincipledBSDF"]["AnisotropicRotation"])
			mods.append(modAnisotropicRotation)

			modClearcoat = ShuffleMaterialProperties(obj_list, "Principled BSDF", "Clearcoat", config[obj.name]["PrincipledBSDF"]["Clearcoat"])
			mods.append(modClearcoat)

			modClearcoatRoughness = ShuffleMaterialProperties(obj_list, "Principled BSDF", "Clearcoat Roughness", config[obj.name]["PrincipledBSDF"]["ClearcoatRoughness"])
			mods.append(modClearcoatRoughness)

		if "BrickTexture" in config[obj.name]:
			print("BrickTexture for ", obj.name)
			for key in config[obj.name]["BrickTexture"]:
				modBrickTexture = ShuffleMaterialProperties(obj_list, "Brick Texture", config[obj.name]["BrickTexture"][key]["PropertyName"], config[obj.name]["BrickTexture"][key]["value"])
				mods.append(modBrickTexture)

		if "Mapping" in config[obj.name]:
			print("Mapping for ", obj.name)
			for key in config[obj.name]["Mapping"]:
				modMapping = ShuffleVector(obj_list, "Mapping", key, config[obj.name]["Mapping"][key])
				mods.append(modMapping)

		if "ShuffleMaterials" in config[obj.name]:
			modShuffleMaterials = ShuffleMaterials(obj_list)
			mods.append(modShuffleMaterials)


		
		if "ShuffleMaterialConfig" in config[obj.name]:
			for key in config[obj.name]["ShuffleMaterialConfig"]:
				sub_config  = config[obj.name]["ShuffleMaterialConfig"][key]
				print(sub_config)
				mod = ShuffleMaterialProperties(obj_list, sub_config["NodeName"], sub_config["PropertyName"], sub_config["value"], sub_config["material_name"])
				mods.append(mod)
			
		if "Color" in config[obj.name]:
			try:
				for key in config[obj.name]["Color"]:
					color_config  = config[obj.name]["Color"][key]
					print(color_config)
					modShuffleColor = ShuffleRGBColor(obj_list, color_config["NodeName"], color_config["PropertyName"], color_config["value1"],color_config["value2"],color_config["value3"], color_config["mode"], color_config["material_name"])
					mods.append(modShuffleColor)
					print("Shuffling color with keys for ", obj.name)
			except:
				color_config  = config[obj.name]["Color"]
				modShuffleColor = ShuffleRGBColor(obj_list, color_config["NodeName"], color_config["PropertyName"], color_config["value1"],color_config["value2"],color_config["value3"], color_config["mode"], color_config["material_name"])
				mods.append(modShuffleColor)
				print("Shuffling color for ", obj.name)

		if "Disappear" in config[obj.name]:
			modDisappear = RandomDisappear(obj_list, config[obj.name]["Disappear"]["value"])
			mods.append(modDisappear)

			#else:
				#print("no color config for ", obj.name)

	
	return mods

# def createMaskMods(objects, path, config):
#   mods = list()

#   index_dict = {}
#   for obj in objects:
#   		print(obj.name)
#   		print(obj.name, " ID ", config[obj.name]["id"])
#   		index_dict[obj.name] = config[obj.name]["id"]
	
#   modMask = MaskComposition(objects, index_dict, path = path)
#   mods.append(modMask)

#   for obj in objects:
#   		obj_list = list()
#   		obj_list.append(obj)
#   		try:
#   			if config[obj.name]["hide_in_rgb"]:
#   				#print("Hiding ", obj.name, " in RGB ", config[obj.name]["hide_in_rgb"])
#   				print("Hiding ", obj.name, " in RGB ")
#   				modHideInRgb = HideInRGB(obj_list)
#   				mods.append(modHideInRgb)
#   		except:
#   			pass
			

#   return mods

def createWorldMods(config):
	world_obj= list()
	world_mods= list()
	if config['General']['ShuffleWorld']:
		world_obj.append(bpy.context.scene.world)
		#world_mods.append(ShuffleBackground(world_obj, config['World']['Backgrounds'], True, shuffle_strength=[0.8, 1.2]))
		world_mods.append(ShuffleBackground(world_obj, config['World']['Backgrounds'], True, shuffle_strength=[config['World']['Strength']['Min'], config['World']['Strength']['Max']]))
	return world_mods

def createMods(camera, lamp, objects, decoys, special, config):
	mods = list()
	mods.extend(createWorldMods(config))
	mods.extend(createCameraMods(camera))
	mods.extend(createLightMods(lamp))
	mods.extend(createObjectMods(objects, config))
	mods.extend(createDecoyMods(decoys, config))
	mods.extend(createSpecialObjectMods(special, config))
	return mods


def get_latest_index(render_path):
	numbers = list()
	for filename in os.listdir(render_path):
		if filename.endswith(".png"):
			number = int(filename[:-4])
			numbers.append(number)
	
	if not numbers:
		return 1
	else:   
		max_num = max(numbers)
		print("Resuming rendering at ", max_num)
		return max_num


# ____________________________________________ Apply every modification and create image + labels

def batch_render(scene, camera, visibility_camera_object, lamp, objects, decoys, special, steps, config, bounds, render_path = None, bbox_path = None, seg_path = None, bop_path = None , label = False, mask = False, path = False):
	
	"""available_steps = range(1, steps+1)
	for k in available_steps:

		file_prefix=datetime.now().strftime('%Y-%m-%d-%H-%M-%S-%f')[:-3]
		createYoloTxtFile(scene, camera, visibility_camera_object, objects, config, file_prefix, folder, bounds)
		createBopTxtFile(scene, camera, visibility_camera_object, objects, config, file_prefix, folder, bounds)
		render(scene, camera, objects, file_prefix, folder)
		print(k, " of ", steps, " done.")
	

	"""
	print("RENDER PWTH ", render_path)
	print("BBOX PWTH ", bbox_path)
	print("SEG PWTH ", seg_path)
	print("BOP PWTH ", bop_path)

	
	maskMods = list()

	# if mask:
	#   maskMods = createMaskMods(objects, seg_path, config)
	#   for maskMod in maskMods:
	#   	maskMod.performPreProcessing()
	
	#available_steps = range(get_latest_index(render_path), steps+1)
	available_steps = range(get_latest_index(render_path), steps+1)
	if path:
		available_steps = range(scene.frame_start,scene.frame_end)

	for k in available_steps:
		print("\n _____________________ \n")
		print("Starting image no.", k)

		for obj in objects:
			show_obj_and_children(obj)

		if path: 
			scene.frame_current = k

		mods = createMods(camera, lamp, objects, decoys, special, config)

		for mod in mods:
			mod.performAction()


		#file_prefix=datetime.now().strftime('%Y-%m-%d-%H-%M-%S-%f')[:-3]
		file_prefix = f'{k:06}'

		hideInvisibleObjects(scene, camera, visibility_camera_object, objects, config)

	

		if label:
			createYoloTxtFile(scene, camera, visibility_camera_object, objects, config, bbox_path, file_prefix, bounds)
			createBopTxtFile(scene, camera, visibility_camera_object, objects, config, bop_path, file_prefix, bounds)
			# efficientpose:
			#createBopTxtFile(scene, camera, visibility_camera_object, objects, config, k, folder, bounds)
		
		#mask_prefix = file_prefix + "_mask"
		
		if mask:
			for maskMod in maskMods:
				maskMod.performAction(file_prefix)  

			render.use_compositing = True
			render.use_sequencer = False	  
			
			render(scene, camera, objects, render_path, file_prefix)

			for maskMod in maskMods:
				maskMod.performPostProcessing()

		#render.use_compositing = False
		#render.use_sequencer = True

		#bpy.context.scene.view_layers["RenderLayer"].name
	
		#render(scene, camera, objects, file_prefix, folder)

		print(k, " of ", steps, " done.")

	
		"""
		if mask:
			for maskMod in maskMods:
				maskMod.performAction(file_prefix)  

			#render.use_compositing = True
			#render.use_sequencer = False      
			
			render(scene, camera, objects, file_prefix, folder)

			for maskMod in maskMods:
				maskMod.performPostProcessing()
		"""
		#render.use_compositing = False
		#render.use_sequencer = True

		#bpy.context.scene.view_layers["RenderLayer"].name
	
		#render(scene, camera, objects, file_prefix, folder)

		#print(k, " of ", steps, " done.")"""
	

	print("DONE! =)")


def load_objects(names, ignore_names=None, category=""):
	mesh_obj=list()
	if ignore_names != "" and ignore_names is not None:
		available = [obj.name for obj in bpy.data.objects]
		mesh_names = [x for x in available if x not in ignore_names]

	elif names is not None:
		mesh_names = names

	else:
		print("Unable to load ", category)
		return mesh_obj
	try:
		mesh_objects = [bpy.data.objects[name] for name in mesh_names]
		for mesh in mesh_objects:
			mesh_obj.append(mesh)
			print("Loaded " , mesh.name, " class ", category)
	except:
		print("Error loading objects of ", category)
	return mesh_obj

# ____________________________________________ Helper methods

def hideAllObjects(Objs):
	for obj in Objs:
		hide_obj_and_children(obj)


# ____________________________________________ Read config values & Load objects

def main():
	bpy.context.view_layer.update()

	config = toml.load(base_config)

	if config['Config']['MultiConfig']:
		for file in os.listdir(os.path.join(base_dir+ "/" + config['Config']['Folder'])):
			if file.endswith(".toml"):
				print("found additional config ", file)
				addition = toml.load(os.path.join(base_dir, config['Config']['Folder'] ,file))

				#print(addition)

				#print("________________________ \n")

				new_config = toml.load([base_config, os.path.join(base_dir, config['Config']['Folder'], file)])

				#print(new_config)

				config = new_config

				scene = bpy.data.scenes[config['General']['Scene']]
				camera_object = bpy.data.objects[config['General']['Camera']]
				visibility_camera_object = bpy.data.objects[config['General']['Visibility_Check']]
				steps = config['General']['Steps']
				if 'Boundaries' in config['General']:
					bounds = config['General']['Boundaries']
				else:
					bounds = None
				#print("BOUNDARIES ARE ",bounds)		

				lamp_obj = list()
				mesh_obj = list()
				decoy_obj = list()
				special_obj = list()

				lamp_obj = load_objects(config['Objects']['Lamps'], category="Lamps")
				mesh_obj = load_objects(config['Objects']['Names'], config['Objects']['Ignore'], "Objects")
				decoy_obj = load_objects(config['Objects']['Decoy'], category="Decoy")
				special_obj = load_objects(config['Objects']['Special'], category="Special")


				if config['General']['SingleObjects']:
					for obj in mesh_obj:
						
						if obj.name in config['Labels']:

							"""render_path = os.path.join(base_dir, config['Files']['Folder'], str(config['Labels'][obj.name]), "renders")
							bbox_path = os.path.join(base_dir, config['Files']['Folder'], str(config['Labels'][obj.name]), "bbox_labels")
							bop_path = os.path.join(base_dir, config['Files']['Folder'], str(config['Labels'][obj.name]), "bop_labels")
							seg_path = os.path.join(base_dir, config['Files']['Folder'], str(config['Labels'][obj.name]), "seg_labels")"""

							render_path = os.path.join(base_dir, config['Files']['Folder'], str(config['Labels'][obj.name]), "rgb")
							bbox_path = os.path.join(base_dir, config['Files']['Folder'], str(config['Labels'][obj.name]), "bbox_labels")
							bop_path = os.path.join(base_dir, config['Files']['Folder'], str(config['Labels'][obj.name]), "")
							seg_path = os.path.join(base_dir, config['Files']['Folder'], str(config['Labels'][obj.name]), "merged_masks")

							if not os.path.exists(render_path):
								os.makedirs(render_path)

							if not os.path.exists(bbox_path):
								os.makedirs(bbox_path)  

							if not os.path.exists(bop_path):
								os.makedirs(bop_path)   

							if not os.path.exists(seg_path):
								os.makedirs(seg_path)   


							hideAllObjects(mesh_obj)
							current_obj = list()
							current_obj.append(obj)
							batch_render(scene, camera_object, visibility_camera_object,lamp_obj, current_obj,decoy_obj, special_obj, int(steps), config, bounds, render_path = render_path, bbox_path = bbox_path, seg_path = seg_path, bop_path = bop_path, label = config['General']['CreateYoloLabels'], mask = config['General']['CreateSegmentationMask'], path = config['General']['AnimateAlongPath'])
						else:
							continue

				else:

					folder = config['Files']['Folder']

					"""render_path = os.path.join(base_dir, config['Files']['Folder'], "renders")
					bbox_path = os.path.join(base_dir, config['Files']['Folder'], "bbox_labels")
					bop_path = os.path.join(base_dir, config['Files']['Folder'], "bop_labels")
					seg_path = os.path.join(base_dir, config['Files']['Folder'], "seg_labels")"""

					render_path = os.path.join(base_dir, config['Files']['Folder'], "rgb")
					bbox_path = os.path.join(base_dir, config['Files']['Folder'], "bbox_labels")
					bop_path = os.path.join(base_dir, config['Files']['Folder'], "")
					seg_path = os.path.join(base_dir, config['Files']['Folder'], "merged_masks")

					if not os.path.exists(render_path):
						os.makedirs(render_path)

					if not os.path.exists(bbox_path):
						os.makedirs(bbox_path)  

					if not os.path.exists(bop_path):
						os.makedirs(bop_path)   

					if not os.path.exists(seg_path):
						os.makedirs(seg_path)   				

					batch_render(scene, camera_object, visibility_camera_object,lamp_obj, mesh_obj,decoy_obj, special_obj, int(steps), config, bounds, render_path = render_path, bbox_path = bbox_path, seg_path = seg_path, bop_path = bop_path , label = config['General']['CreateYoloLabels'], mask = config['General']['CreateSegmentationMask'], path = config['General']['AnimateAlongPath'])

	else:
		#scene, camera, lamp, objects, steps, config, bounds, folder = None, label = False, mask = False, path = False
		scene = bpy.data.scenes[config['General']['Scene']]
		camera_object = bpy.data.objects[config['General']['Camera']]
		visibility_camera_object = bpy.data.objects[config['General']['Visibility_Check']]
		steps = config['General']['Steps']
		if 'Boundaries' in config['General']:
			bounds = config['General']['Boundaries']
		else:
			bounds = None
		#print("BOUNDARIES ARE ",bounds)		

		lamp_obj = list()
		mesh_obj = list()
		decoy_obj = list()
		special_obj = list()

		lamp_obj = load_objects(config['Objects']['Lamps'], category="Lamps")
		mesh_obj = load_objects(config['Objects']['Names'], config['Objects']['Ignore'], "Objects")
		decoy_obj = load_objects(config['Objects']['Decoy'], category="Decoy")
		special_obj = load_objects(config['Objects']['Special'], category="Special")


		if config['General']['SingleObjects']:
			for obj in mesh_obj:
				
				if obj.name in config['Labels']:

					render_path = os.path.join(base_dir, config['Files']['Folder'], str(config['Labels'][obj.name]), "rgb")
					bbox_path = os.path.join(base_dir, config['Files']['Folder'], str(config['Labels'][obj.name]), "bbox_labels")
					bop_path = os.path.join(base_dir, config['Files']['Folder'], str(config['Labels'][obj.name]), "")
					seg_path = os.path.join(base_dir, config['Files']['Folder'], str(config['Labels'][obj.name]), "merged_masks")

					if not os.path.exists(render_path):
						os.makedirs(render_path)

					if not os.path.exists(bbox_path):
						os.makedirs(bbox_path)  

					if not os.path.exists(bop_path):
						os.makedirs(bop_path)   

					if not os.path.exists(seg_path):
						os.makedirs(seg_path)   


					hideAllObjects(mesh_obj)
					current_obj = list()
					current_obj.append(obj)
					batch_render(scene, camera_object, visibility_camera_object,lamp_obj, current_obj,decoy_obj, special_obj, int(steps), config, bounds, render_path = render_path, bbox_path = bbox_path, seg_path = seg_path, bop_path = bop_path , label = config['General']['CreateYoloLabels'], mask = config['General']['CreateSegmentationMask'], path = config['General']['AnimateAlongPath'])
				else:
					continue

		else:

			folder = config['Files']['Folder']

			render_path = os.path.join(base_dir, config['Files']['Folder'], "rgb")
			bbox_path = os.path.join(base_dir, config['Files']['Folder'], "bbox_labels")
			bop_path = os.path.join(base_dir, config['Files']['Folder'], "")
			seg_path = os.path.join(base_dir, config['Files']['Folder'], "merged_masks")

			if not os.path.exists(render_path):
				os.makedirs(render_path)

			if not os.path.exists(bbox_path):
				os.makedirs(bbox_path)  

			if not os.path.exists(bop_path):
				os.makedirs(bop_path)   

			if not os.path.exists(seg_path):
				os.makedirs(seg_path)   				

			batch_render(scene, camera_object, visibility_camera_object,lamp_obj, mesh_obj,decoy_obj, special_obj, int(steps), config, bounds, render_path = render_path, bbox_path = bbox_path, seg_path = seg_path, bop_path = bop_path , label = config['General']['CreateYoloLabels'], mask = config['General']['CreateSegmentationMask'], path = config['General']['AnimateAlongPath'])

			#batch_render(scene, camera_object, visibility_camera_object, lamp_obj, mesh_obj,decoy_obj, special_obj, int(steps), config, bounds, folder = folder, label = config['General']['CreateYoloLabels'], mask = config['General']['CreateSegmentationMask'], path = config['General']['AnimateAlongPath'])
		#return

if __name__ == '__main__':
	main()
