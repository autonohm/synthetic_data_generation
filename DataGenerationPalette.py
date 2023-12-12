import bpy, os
from math import sin, cos, pi
import numpy as np
import sys
import random
from datetime import datetime
import toml

base_dir = os.path.dirname(bpy.data.filepath)
dir = base_dir

if not dir in sys.path:
    sys.path.append(dir)

import boundingBox
import checkVisibility
from Modifications.ShufflePos import ShuffleXPos, ShuffleYPos, ShuffleZPos
from Modifications.ShuffleRot import ShuffleXRot, ShuffleYRot, ShuffleZRot
from Modifications.ShuffleColor import ShuffleRGBColor, ShuffleBackground, ShuffleImageTexture, ShuffleColorSpace
from Modifications.Mask import Mask, MaskComposition
from Modifications.RandomMods import RandomDisappear
from Modifications.CameraMods import ShuffleFocalLength
from Modifications.ShuffleMaterial import ShuffleMaterials, ShuffleMaterialProperties
from Modifications.ShuffleVector import ShuffleVector

from Modifications.MeshMods import CreateHull

## Global variables cause things are getting messy 
base_config = "/mnt/Storage/work/DataGen/DataGenPalettes/configPalette.toml"
config = toml.load(base_config)

def calcVisibilityThresh(obj, config):
	visibility_thresh = config[obj.name]["visibility_thresh_factor"]
	factor = obj.location.z / 2 + visibility_thresh
	return min(factor, 0.8)

# ____________________________________________ Create image

def render(scene, camera_object, mesh_objects, file_prefix="render", folder=None):
	# Rendering
	# https://blender.stackexchange.com/questions/1101/blender-rendering-automation-build-script
	if folder:
		folder = "renders/" + str(folder)
	else:
		 folder = "renders"
	filename = str(file_prefix)
	bpy.context.scene.render.filepath = os.path.join(base_dir+ "/" + folder + "/", filename + '.png')
	bpy.ops.render.render(write_still=True)

# ____________________________________________ Create labels

def createYoloTxtFile(scene, camera_object, visibility_camera, mesh_objects, config, file_prefix="label", folder=None, bounds=None):
	random.shuffle(mesh_objects)
	filename = str(file_prefix)
	if folder:
		folder = "labels/" + str(folder)
	else:
		 folder = "labels"
	path = os.path.join(base_dir+ "/" + folder + "/", filename + '.txt')
	with open(path, 'w+') as file:
		""" Get the bounding box coordinates for each mesh """
		for object in mesh_objects:
			if not object.name in config['Labels']:
				print(object.name + " has no label - not labeling this!")
				continue

			if object.hide_render == True:
				print(object.name + " is hidden - not labeling this!")
				continue
			
			name = config['Labels'][object.name]
			checkVisibility.select_camera_view(scene, visibility_camera, object)
			visibility = checkVisibility.check_visibility(scene, visibility_camera, object)
			checkVisibility.restore_camera(scene, camera_object)

			if visibility < calcVisibilityThresh(object, config):
				print(object.name, "visibilitiy is ", visibility, " -> not visible in render - HIDING this!")
				object.hide_render = True
				continue

			bounding_box = boundingBox.camera_view_bounds_2d(scene, camera_object, object, bounds)
			if bounding_box:
				new_line = str(name) + " " + str(bounding_box[0])+ " " + str(bounding_box[1]) + " " + str(bounding_box[2]) + " " + str(bounding_box[3]) + '\n'
				file.write(new_line)

			else: 
				object.hide_render = True
				print("Hiding ", object.name)


# ____________________________________________ Create Modification

def createCameraMods(camera):
	mods = list()
	cameras = list()
	cameras.append(camera)
	#modFocalLength = ShuffleFocalLength([11, 38], cameras)
	#mods.append(modFocalLength)
	modZRot = ShuffleZRot([0, 360], cameras, False)
	mods.append(modZRot)
	modXRot = ShuffleXRot([60, 110], cameras, False)
	mods.append(modXRot)
	modYRot = ShuffleYRot([-20, 20], cameras, False)
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

				modZRot = ShuffleZRot(config[obj.name]["Rotation"]["Z"], obj_list, False)
				mods.append(modZRot)
				modYRot = ShuffleYRot(config[obj.name]["Rotation"]["Y"], obj_list, False)
				mods.append(modYRot)
				modXRot = ShuffleXRot(config[obj.name]["Rotation"]["X"], obj_list, False)
				mods.append(modXRot)

			if "Position" in config[obj.name]:
				
				modZPos = ShuffleZPos(config[obj.name]["Position"]["Z"], obj_list, config[obj.name]["Position"]["Z_hide_on_intersection"])
				mods.append(modZPos)

				modXPos = ShuffleXPos(config[obj.name]["Position"]["X"], obj_list, config[obj.name]["Position"]["X_hide_on_intersection"], False, config[obj.name]["Position"]["X_normed_to_1m"])
				mods.append(modXPos)
				modYPos = ShuffleYPos(config[obj.name]["Position"]["Y"], obj_list, config[obj.name]["Position"]["Y_hide_on_intersection"], False, config[obj.name]["Position"]["Y_normed_to_1m"])
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
			if "Color" in config[obj.name]:
				color_config  = config[obj.name]["Color"]
				modShuffleColor = ShuffleRGBColor(obj_list, color_config["NodeName"], color_config["PropertyName"], color_config["value1"],color_config["value2"],color_config["value3"], color_config["mode"])
				mods.append(modShuffleColor)
			else:
				print("no color config for ", obj.name)

	modDisappear = RandomDisappear(decoy, 0.3)
	mods.append(modDisappear)
	return mods

def createSpecialObjectMods(special, config):
	mods = list()


	#modZRot = ShuffleZRot([0, 360], special, False)
	#mods.append(modZRot)

	modZRot = ShuffleZRot([-25, 25], special, False)
	mods.append(modZRot)
	modYRot = ShuffleYRot([-30, 30], special, False)
	mods.append(modYRot)
	modXRot = ShuffleXRot([-90, -30], special, False)
	mods.append(modXRot)

	modZPos = ShuffleZPos([-0.3, -0.2], special, True, False)
	mods.append(modZPos)

	modXPos = ShuffleXPos([-0.15, 0.15], special, True, False, False)
	mods.append(modXPos)
	modYPos = ShuffleYPos([-0.3, -0.2], special, True, False, False)
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
			
		if "Color" in config[obj.name]:
			color_config  = config[obj.name]["Color"]
			modShuffleColor = ShuffleRGBColor(obj_list, color_config["NodeName"], color_config["PropertyName"], color_config["value1"],color_config["value2"],color_config["value3"], color_config["mode"])
			mods.append(modShuffleColor)
		else:
			print("no color config for ", obj.name)

	
	return mods

def createObjectMods(objects, config):
	mods = list()

	#modZPos = ShuffleZPos([-0.8, -0.4], objects, True, False)
	
	for obj in objects:
			obj_list = list()
			obj_list.append(obj)

			if "Rotation" in config[obj.name]:

				modZRot = ShuffleZRot(config[obj.name]["Rotation"]["Z"], objects, False)
				mods.append(modZRot)
				modYRot = ShuffleYRot(config[obj.name]["Rotation"]["Y"], objects, False)
				mods.append(modYRot)
				modXRot = ShuffleXRot(config[obj.name]["Rotation"]["X"], objects, False)
				mods.append(modXRot)

			if "Position" in config[obj.name]:
				
				modZPos = ShuffleZPos(config[obj.name]["Position"]["Z"], objects, config[obj.name]["Position"]["Z_hide_on_intersection"])
				mods.append(modZPos)

				modXPos = ShuffleXPos(config[obj.name]["Position"]["X"], objects, config[obj.name]["Position"]["X_hide_on_intersection"], False, config[obj.name]["Position"]["X_normed_to_1m"])
				mods.append(modXPos)
				modYPos = ShuffleYPos(config[obj.name]["Position"]["Y"], objects, config[obj.name]["Position"]["Y_hide_on_intersection"], False, config[obj.name]["Position"]["Y_normed_to_1m"])
				mods.append(modYPos)

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

			if "Color" in config[obj.name]:
				color_config  = config[obj.name]["Color"]
				modShuffleColor = ShuffleRGBColor(obj_list, color_config["NodeName"], color_config["PropertyName"], color_config["value1"],color_config["value2"],color_config["value3"], color_config["mode"])
				mods.append(modShuffleColor)

			if "Disappear" in config[obj.name]:
				modDisappear = RandomDisappear(obj_list, config[obj.name]["Disappear"]["value"])
				mods.append(modDisappear)

			else:
				print("no color config for ", obj.name)

	
	return mods

def createMaskMods(objects, folder, config):
	mods = list()

	index_dict = {}
	for obj in objects:
			print(obj.name, " ID ", config[obj.name]["id"])
			index_dict[obj.name] = config[obj.name]["id"]
	
	if folder:
		folder = "labels/" + str(folder)
	else:
		 folder = "labels"
	modMask = MaskComposition(objects, index_dict, base_path = "/mnt/Storage/work/DataGen/DataGenAtWork/", folder = folder)
	mods.append(modMask)
	return mods

def createWorldMods(config):
	world_obj= list()
	world_mods= list()
	if config['General']['ShuffleWorld']:
		world_obj.append(bpy.context.scene.world)
		world_mods.append(ShuffleBackground(world_obj, config['World']['Backgrounds'], True, shuffle_strength=[0.7, 1.0]))
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

# ____________________________________________ Apply every modification and create image + labels

def batch_render(scene, camera, visibility_camera_object, lamp, objects, decoys, special, steps, config, bounds, folder=None, label = False, mask = False, path = False):
	mods = createMods(camera, lamp, objects, decoys, special, config)
	maskMods = list()

	if mask:
		maskMods = createMaskMods(objects, folder)
		for maskMod in maskMods:
			maskMod.performPreProcessing()
	
	available_steps = range(1, steps+1)
	if path:
		available_steps = range(scene.frame_start,scene.frame_end)

	for k in available_steps:
		print("Starting image no.", k)

		if path: 
			scene.frame_current = k

		for mod in mods:
			mod.performAction()


		file_prefix=datetime.now().strftime('%Y-%m-%d-%H-%M-%S-%f')[:-3]

		if label:
			createYoloTxtFile(scene, camera, visibility_camera_object, objects, config, file_prefix, folder, bounds)
			# dont render the image again if it was already created with the segmentation mask composition
	
		render(scene, camera, objects, file_prefix, folder)
		
		if mask:
			for maskMod in maskMods:
				maskMod.performAction(file_prefix)        
			
			render(scene, camera, objects, file_prefix, folder)

			for maskMod in maskMods:
				maskMod.performPostProcessing()

		print(k, " of ", steps, " done.")

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
	except:
		print("Error loading objects of ", category)
	return mesh_obj

# ____________________________________________ Helper methods

def hideAllObjects(Objs):
	for obj in Objs:
		obj.hide_render = True


# ____________________________________________ Read config values & Load objects

def main():
	bpy.context.view_layer.update()

	config = toml.load(base_config)

	if config['Config']['MultiConfig']:
		for file in os.listdir(os.path.join(base_dir+ "/" + config['Config']['Folder'])):
			if file.endswith(".toml"):
				print("found additional config ", file)
				addition = toml.load(os.path.join(base_dir, config['Config']['Folder'] ,file))

				print(addition)

				print("________________________ \n")

				new_config = toml.load([base_config, os.path.join(base_dir, config['Config']['Folder'], file)])

				print(new_config)

				config = new_config

				folder = config['Files']['Folder']

				if not os.path.exists(os.path.join(base_dir, "renders", config['Files']['Folder'])):
					os.makedirs(os.path.join(base_dir, "renders", config['Files']['Folder']))

				if not os.path.exists(os.path.join(base_dir, "labels" , config['Files']['Folder'])):
					os.makedirs(os.path.join(base_dir, "labels" , config['Files']['Folder']))				

				scene = bpy.data.scenes[config['General']['Scene']]
				camera_object = bpy.data.objects[config['General']['Camera']]
				visibility_camera_object = bpy.data.objects[config['General']['Visibility_Check']]
				steps = config['General']['Steps']
				if 'Boundaries' in config['General']:
					bounds = config['General']['Boundaries']
				else:
					bounds = None
				print("BOUNDARIES ARE ",bounds)		

				lamp_obj = list()
				mesh_obj = list()
				decoy_obj = list()
				special_obj = list()

				lamp_obj = load_objects(config['Objects']['Lamps'], category="Lamps")
				mesh_obj = load_objects(config['Objects']['Names'], config['Objects']['Ignore'], "Objects")
				decoy_obj = load_objects(config['Objects']['Decoy'], category="Decoy")
				special_obj = load_objects(config['Objects']['Special'], category="Special")

				#scene, camera, lamp, objects, steps, config, bounds, folder = None, label = False, mask = False, path = False

				if config['General']['SingleObjects']:
					for obj in mesh_obj:
						hideAllObjects(mesh_obj)
						current_obj = list()
						current_obj.append(obj)
						batch_render(scene, camera_object, visibility_camera_object,lamp_obj, current_obj,decoy_obj, special_obj, int(steps), config, bounds, folder = folder + "_" + config['Labels'][obj.name], label = config['General']['CreateYoloLabels'], mask = config['General']['CreateSegmentationMask'], path = config['General']['AnimateAlongPath'])
				else:
					batch_render(scene, camera_object, visibility_camera_object, lamp_obj, mesh_obj,decoy_obj, special_obj, int(steps), config, bounds, folder = folder, label = config['General']['CreateYoloLabels'], mask = config['General']['CreateSegmentationMask'], path = config['General']['AnimateAlongPath'])
				#return
				

if __name__ == '__main__':
	main()
