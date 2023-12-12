from collections import Counter
import os
import yaml

IMG_PATH = "/home/vision/Study/DataGenPalettes/test/renders/"
LABEL_PATH = "/home/vision/Study/DataGenPalettes/test/bop_labels/"

NAMES = ["Palette"]


for filename in os.listdir(IMG_PATH):
	if filename.endswith(".png"):
		with open(LABEL_PATH + "gt.yml",'r') as infile:
			infile.seek(0)
			file_data = yaml.load(infile, Loader=yaml.Loader)
			print(file_data[filename[:-4]])
			


