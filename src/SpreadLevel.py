# AnalyseResolutions - SpreadLevel. Tuomo Toljamo (King's College London; DiXiT) at the Huygens ING (KNAW), 2016.
#
# This PhDWare code-sketch was part of a pilot exploring the use and usefulness of image data and visual information in
# the digital opening of an archival series, the Resolutions of the States General 1576‒1796.
#
# DiXiT (Digital Scholarly Editions Initial Training Network) has been funded from the People Programme (Marie Curie Actions)
# of the European Union's Seventh Framework Programme FP7/2007-2013/ under REA grant agreement n° 317436.

import DocumentImageAnalysis as dia
import Levers
import numpy as np
from scipy.ndimage import interpolation,filters
from PIL import Image
import numpy


# ## BINARISATION ##
def SauvolaBinarise(original, filterType):
    """
    Preprocessing: Sauvola binarisation. Utilises the Sauvola algorithm distributed with Breuel's OCRopus (Ocropy) toolkit.
    :param original: facsimile image
    :return: binarised facsimile image
    """

    # Note: The algorithm seems only to accept arrays with even borders at the moment. A kludge below to
    # omit a pixel from either/both dimensions if needed.

    # Let's see if one or both dimensions are not even.
    iOffset = (original.getImage().shape[0] % 2)
    jOffset = (original.getImage().shape[1] % 2)

    # Let's omit a row or column of pixels if needed.
    if (iOffset != 0 and jOffset != 0):
        inp = original.getImage()[:-iOffset, :-jOffset]
    elif (iOffset != 0):
        inp = original.getImage()[:-iOffset, :]
    elif (jOffset != 0):
        inp = original.getImage()[:, :-jOffset]
    else:
        inp = original.getImage()[:, :]

    # gsauvola() extracted and adapted from Breuel's OCRopus
    binImage = gsauvola(inp, 150.0, None, 0.3, filterType, 2.0)

    binarised = dia.Facsimile(binImage, 'binarised', (0,0))
    if Levers.debugFlag:
        binarised.save()

    del binImage

    return binarised


def gsauvola(image,sigma=150.0,R=None,k=0.3,filter='uniform',scale=2.0):
    """Perform Sauvola-like binarization.  This uses linear filters to
    compute the local mean and variance at every pixel."""
    # Note! This Sauvola implementation is borrowed from Breuel's OCRopus (Ocropy) toolkit.
    # See: - https://github.com/tmbdev/ocropy/blob/master/OLD/ocropus-sauvola
    #      - Breuel, T. M. (2008) 'The OCRopus Open Source OCR System'.
    # See also Sauvola, J. & M. Pietikäinen (2000) 'Adaptive Document Image Binarisation' Pattern Recognition 33, 225‒36.

    if image.dtype==np.dtype('uint8'): image = image / 256.0
    if len(image.shape)==3: image = np.mean(image,axis=2)
    if filter=="gaussian":
        filter = filters.gaussian_filter
    elif filter=="uniform":
        filter = filters.uniform_filter
    else:
        pass
    scaled = interpolation.zoom(image,1.0/scale,order=0,mode='nearest')
    s1 = filter(np.ones(scaled.shape),sigma)
    sx = filter(scaled,sigma)
    sxx = filter(scaled**2,sigma)
    avg_ = sx / s1
    stddev_ = np.maximum(sxx/s1 - avg_**2,0.0)**0.5
    s0,s1 = avg_.shape
    s0 = int(s0*scale)
    s1 = int(s1*scale)
    avg = np.zeros(image.shape)
    interpolation.zoom(avg_,scale,output=avg[:s0,:s1],order=0,mode='nearest')
    stddev = np.zeros(image.shape)
    interpolation.zoom(stddev_,scale,output=stddev[:s0,:s1],order=0,mode='nearest')
    if R is None: R = np.amax(stddev)
    thresh = avg * (1.0 + k * (stddev / R - 1.0))
    return np.array(255*(image>thresh),'uint8')


def SauvolaBinariseQuadrants(original):
    # a Kludge to accommodate Win32bit.

    originalArea = original.getImage()
    originalHeight,originalWidth, dim = originalArea.shape

    heightCutoff = (int)(originalHeight/2)
    widthCutoff = (int)(originalWidth/2)

    if (heightCutoff % 2 == 1):
        heightCutoff = heightCutoff -1
    if (widthCutoff % 2 == 1):
        widthCutoff = widthCutoff -1

    baseImage = Image.fromarray(originalArea)

    image11Box = (0, 0, widthCutoff, heightCutoff)
    image11 = baseImage.crop(image11Box)
    image12Box = (widthCutoff+1, 0, originalWidth, heightCutoff)
    image12 = baseImage.crop(image12Box)
    image21Box = (0, heightCutoff+1, widthCutoff, originalHeight)
    image21 = baseImage.crop(image21Box)
    image22Box = (widthCutoff+1, heightCutoff+1, originalWidth, originalHeight)
    image22 = baseImage.crop(image22Box)

    image11 = dia.Facsimile(numpy.array(image11), "tempBin11")
    image12 = dia.Facsimile(numpy.array(image12), "tempBin12")
    image21 = dia.Facsimile(numpy.array(image21), "tempBin21")
    image22 = dia.Facsimile(numpy.array(image22), "tempBin22")

    image11 = SauvolaBinarise(image11).getImage()
    image12 = SauvolaBinarise(image12).getImage()
    image21 = SauvolaBinarise(image21).getImage()
    image22 = SauvolaBinarise(image22).getImage()

    stitchUp = Image.new("L", (originalWidth, originalHeight), "white")
    stitchUpArea = np.array(stitchUp)

    for i in range(0, image11.shape[0]):
        for j in range(0, image11.shape[1]):
            stitchUpArea[i,j] = image11[i,j]

    for i in range(0, image12.shape[0]):
        for j in range(0, image12.shape[1]):
            stitchUpArea[i,j+widthCutoff] = image12[i,j]

    for i in range(0, image21.shape[0]):
        for j in range(0, image21.shape[1]):
            stitchUpArea[heightCutoff+i,j] = image21[i,j]

    for i in range(0, image22.shape[0]):
        for j in range(0, image22.shape[1]):
            stitchUpArea[heightCutoff+i,widthCutoff+j] = image22[i,j]

    binarised = dia.Facsimile(stitchUpArea, "binarised", (0,0))
    if Levers.debugFlag:
        binarised.save()

    return binarised


#def diffImages(facs1, facs2):
#    area1 = facs1.getImage()
#    area2 = facs2.getImage()
#    diffPil = Image.new("RGB", (area1.shape[1], area1.shape[0]), "white")
#    diff = numpy.array(diffPil)
#
#    for i in range(0, area1.shape[0]):
#        for j in range(0, area1.shape[1]):
#
#            if (area1[i][j] == area2[i][j]):
#                diff[i,j] = [area1[i][j], area1[i][j], area1[i][j]]
#                continue
#            if (area1[i][j] == 0 and area2[i][j] == 255):
#                diff[i,j] = [255, 0, 0]
#                continue
#            if (area1[i][j] == 255 and area2[i][j] == 0):
#                diff[i,j] = [0, 255, 0]
#
#    diffFacs = dia.Facsimile(diff, "binDiff")
#    diffFacs.save()
#
#    return diffFacs
