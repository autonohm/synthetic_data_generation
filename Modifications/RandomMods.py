import bpy
import random
import bmesh
import mathutils
import math
from mathutils.bvhtree import BVHTree
from Modifications.Modification import Modification
from numpy.random import choice


class RandomDisappear(Modification):
    def __init__(self,  objects=[], probability=0.5):
        self.probability  = probability
        print("ADDED DISAPPER MOD WITH PROB ", probability)
        super(RandomDisappear, self).__init__(objects)

    def Action(self, obj):
        chance = choice([0,1], 1,replace=False, p=[1-self.probability, self.probability] )
        print("CHANCE ", chance)
        if chance:
            hide_obj_and_children(obj)

    def PostProcessing(self, obj):
        show_obj_and_children(obj)
    
def hide_obj_and_children(obj):
    for child in obj.children:
        print("HIDING CHILD ", child.name)
        hide_obj_and_children(child)
    obj.hide_render = True

def show_obj_and_children(obj):
	for child in obj.children:
		show_obj_and_children(child)
	obj.hide_render = False