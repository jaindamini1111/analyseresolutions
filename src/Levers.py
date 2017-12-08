# AnalyseResolutions - Levers. Tuomo Toljamo (King's College London; DiXiT) at the Huygens ING (KNAW), 2016.
#
# This PhDWare code-sketch was part of a pilot exploring the use and usefulness of image data and visual information in
# the digital opening of an archival series, the Resolutions of the States General 1576‒1796.
#
# DiXiT (Digital Scholarly Editions Initial Training Network) has been funded from the People Programme (Marie Curie Actions)
# of the European Union's Seventh Framework Programme FP7/2007-2013/ under REA grant agreement n° 317436.

# Levers.py.
# Holds many of the tool's settings and processing parameters.

imageIter = 0     # variable used in filenames of saved debug images.
saveDir = "0"     # sub-folder used for saving results

# Directory for the input document images
dir_in = "images/"

# Directory for the output images and other processing results.
dir_out = "results/"

# Input image file extension
file_ext = "jpg"

#
fileName = "default"

#
debugFlag = True

# Kludge: If running on Win32bit, let's binarise the original image in four quadrants.
kludgeWin32bit = False

# Path to style.css for HTML testing pages
style = "C:/testRel/style.css"

# Used in OCR normalisation with regard to meetings' headers.
target_year ="1740."
