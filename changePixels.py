from PIL import Image
import os

PATH = "/home/vision/Study/DataGenAtWorkSegmentation/seg_labels"

for filename in os.listdir(PATH):
	if filename.endswith(".png"):

		input_image = Image.open(PATH + "/" + filename)

		# Extracting pixel map:
		pixel_map = input_image.load()
		  
		# Extracting the width and height 
		# of the image:
		width, height = input_image.size
		  
		# taking half of the width:
		for i in range(width):
			for j in range(height):

				# getting the RGB pixel value.
				r, g, b = input_image.getpixel((i, j))

				# Apply formula of grayscale:
				new = (0.299*r + 0.587*g + 0.114*b)

				# setting the pixel value.
				pixel_map[i, j] = (int(5 * r), int(5 * g), int(5 * b))

		# Saving the final output
		# as "grayscale.png":
		input_image.save(PATH + "/" + filename, format="png")
