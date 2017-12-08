# AnalyseResolutions - DocumentImageAnalysis. Tuomo Toljamo (King's College London; DiXiT) at the Huygens ING (KNAW), 2016.
#
# This PhDWare code-sketch was part of a pilot exploring the use and usefulness of image data and visual information in
# the digital opening of an archival series, the Resolutions of the States General 1576‒1796.
#
# DiXiT (Digital Scholarly Editions Initial Training Network) has been funded from the People Programme (Marie Curie Actions)
# of the European Union's Seventh Framework Programme FP7/2007-2013/ under REA grant agreement n° 317436.

from PIL import Image
import numpy
import os
import Levers
import DocumentImageUnderstanding as diu
import HelperFunctions as fu
import ColumnLevel as col
import math


class Facsimile():
    """
    Holds the loaded or generated document images; keeps track of their type, a cascading coordinate offset
    to the original facsimile, and optionally a reference to the parent image.
    """

    def __init__(self, inputImage, imageType, offset=None, parent=None):
        self.image = inputImage
        self.imageType = imageType
        self.offset = offset
        self.parent = parent

    def getImage(self):
        return self.image.copy()

    def setImage(self, imageArea):
        self.image = imageArea

    def setOffset(self, offsetLeft, offsetTop):
        self.offset = (offsetLeft, offsetTop)

    def getOffset(self):
        return self.offset

    def setParent(self, parent):
        self.parent = parent

    def getParent(self):
        return self.parent

    def save(self, fileName="default", directory="default", fileType = "default"):
        imageToSave = Image.fromarray(self.image)

        if directory == "default":
            dire = str(Levers.saveDir)
        else:
            dire = directory

        if fileName == "default":
            fname = str(Levers.imageIter) + "_" + self.imageType
        else:
            fname = fileName

        if fileType == "default":
            fname = fname + ".png"
            fswitch = "PNG"
        elif fileType == "TIFF":
            fname = fname+".tif"
            fswitch = "TIFF"
        else:
            fname = fname + ".png"
            fswitch = "PNG"
            print ("Not implemented yet.")

        #Let's make sure saveDir exists
        if not os.path.exists(Levers.dir_out+dire):
            os.makedirs(Levers.dir_out+dire)

        imageToSave.save("results/" + dire + "/" + fname, fswitch)
        Levers.imageIter += 1


class ConnectedComponent():
    """
    Holds a list of pixels and associated functions to a Connected Component (8-connected), i.e. a grouping of
    adjacent pixels (from a binarised image).

    CCs are simple, but very useful in imposing low-level structure to image data and helping one to work with it.
       - For reference, see any book covering the basics of computer vision (e.g. Gonzalez and Woods. 2002. Digital Image Processing.)
    """

    def __init__(self, pixList):
        self.pixelList = pixList
        self.borderPixels = []
        self.maxDist = 0
        self.iMin = -1
        self.iMax = -1
        self.jMin = -1
        self.jMax = -1

    def getPixelCount(self):
        return len(self.pixelList)

    def getPixelList(self):
        return self.pixelList

    def getBorderPixels(self):
        if len(self.borderPixels) == 0:
            self.calculateBorderPixels()
        return self.borderPixels

    def calculateBorderPixels(self):
        """
        Calculates poor man's border pixels, i.e. pixels which are not completely surrounded by other of the CC's pixels.
        The border pixels are calculated because only they need to be examined e.g. when calculating a distance
        between two CCs.
        :return:
        """

        for i in range(0, len(self.pixelList)):
            count = 0  # count = 8 if surrounded
            found = False
            (a,b) = self.pixelList[i]

            for j in range(a-1, a+2):
                for k in range(b-1, b+2):

                    for t in range(0, len(self.pixelList)):
                        if (a == j and b == k):
                            continue #let's not test the pixel on itself.
                        t1,t2 = self.pixelList[t]
                        if j==t1 and k==t2:
                            count = count +1
                            break

                    if (count == 8):
                        found = True
                        break
                if (found == True):
                    break

            if (found == False):
                self.borderPixels.append( self.pixelList[i] )

    def getMinMax(self):
        """
        Returns the minimum and maximum i and j coordinates of the CC. (imin, imax, jmin, jmax).
        :return:
        """
        if self.iMin == -1:
            self.calculateMinMax()
        return (self.iMin, self.iMax, self.jMin, self.jMax)

    def calculateMinMax(self):
        """
        Calculates the minimum and maximum i and j coordinates of the CC.
        :return:
        """
        jmax = 0
        jmin = 1000000
        imax = 0
        imin = 1000000

        for x in range(0, len(self.pixelList)):
            (i, j) = self.pixelList[x]
            if imax < i:
                imax = i
            if imin > i:
                imin = i
            if jmax < j:
                jmax = j
            if jmin > j:
                jmin = j

        self.iMin = imin
        self.iMax = imax
        self.jMin = jmin
        self.jMax = jmax


def findConnectedComponents(binImg, minimumSize = 0, findUntil = -1, startI =-1, endI = -1, startJ = -1, endJ = -1):
    """
    Identifies Connected Components in a binarised image.
    :param binImg: binarised image array
    :param minimumSize: omits returning connected components with a pixel count less than required
    :param findUntil is only used in situations, where one needs to find that more than a given nbr of CCs exist in the area
    :return: a list of connected components
    """
    ccList = []

    if (startI == -1 and endI == -1):
        startI = 0
        endI = binImg.shape[0]
    if (startJ == -1 and endJ == -1):
        startJ = 0
        endJ = binImg.shape[1]

    # Let's look for black pixels; when encountered, ...
    for i in range(startI, endI):
        for j in range(startJ, endJ):

            if binImg[i, j] == 0:
                # Found black pixel.
                binImg, foundCC = findCC(binImg, i, j, minimumSize)

                if (foundCC != None):
                    ccList.append(foundCC)

                    if findUntil != -1:
                        if len(ccList) > findUntil:
                            return ccList

    return ccList


def findCC(binImg, i, j, minimumSize):
    """
    Starts to search for a Connected Component from the given pixel position onwards;
    searches all adjacent pixels (eight-connected).
    :param binImg: binarised image array
    :param i: where to start inspection
    :param j: where to start inspection
    :param minimumSize: a threshold for accepting a found CC
    :return:
    """
    searchDistance = 1  # Default for CC's would be 1
    pixelList = []

    toCheck = set()
    toCheck.add((i, j))

    while not len(toCheck) == 0:
        (i, j) = toCheck.pop()
        if (binImg[i, j] == 255):
            continue
        binImg[i, j] = 255
        pixelList.append((i, j))

        for x in range((searchDistance * -1), searchDistance + 1):
            for y in range((searchDistance * -1), searchDistance + 1):
                if (i + x < binImg.shape[0] and j + y < binImg.shape[1] and i + x >= 0 and j + y >= 0):
                    toCheck.add((i + x, j + y))

    ret = None
    if len(pixelList) > minimumSize:
        ret = ConnectedComponent(pixelList)

    return binImg, ret


def findCC2(binImg, toCheckIn):
    """
    A variant of findCC(). (@redundant code; poor naming, etc.).
    Used by cleanBorders() and findBorderMostCC().
    :param binImg:
    :param toCheckIn:
    :return:
    """
    searchDistance = 1  # Default for CC's would be 1
    pixelList = []

    toCheck = set()
    toCheck.add(toCheckIn)

    while not len(toCheck) == 0:
        (j, i) = toCheck.pop()
        if (binImg[j, i] == 255):
            continue
        binImg[j, i] = 255
        pixelList.append((j, i))

        for x in range((searchDistance * -1), searchDistance + 1):
            for y in range((searchDistance * -1), searchDistance + 1):
                if (j + x < binImg.shape[0] and i + y < binImg.shape[1] and j + x >= 0 and i + y >= 0):
                    toCheck.add((j + x, i + y))

    return ConnectedComponent(pixelList)


def calculateCCDistance2(p1, p2):
    """
    Calculates a minimum distance between two CCs by examining all of their border pixels (poor).
    """
    pixels1 = p1.getBorderPixels()
    pixels2 = p2.getBorderPixels()

    minDist = 10000000

    for x in range(0, len(pixels1)):
        for y in range(0, len(pixels2)):
            c11, c12 = pixels1[x]
            c21, c22 = pixels2[y]
            dist = int(round(math.sqrt(math.pow((c11 - c21), 2) + math.pow((c12 - c22), 2))))
            if (minDist > dist):
                minDist = dist

    return minDist


def getProjections(facs, facsName, visualise=True):
    """
    Calculates horizontal and vertical projections and optionally visualises the normalised distributions by
    expanding the input image with [+101, +101] pixels.

    Returns normalised lists of projection's pixel counts and the generated image.
    """
    img = facs.getImage()
    verticalList = []
    horizontalList = []

    # Calculates vertical pixel counts across the image.
    for j in range(0, img.shape[1]):
        count = 0
        for i in range(0, img.shape[0]):
            if (img[i, j] == 0):
                count = count + 1
        verticalList.append(count)

    # Calculates horizontal pixel counts down the image.
    for i in range(0, img.shape[0]):
        count = 0
        for j in range(0, img.shape[1]):
            if (img[i, j] == 0):
                count = count + 1
        horizontalList.append(count)

    # Normalises the lists.
    normHorList = fu.normaliseList(horizontalList)
    normVerList = fu.normaliseList(verticalList)

    # (i,j) = img.shape

    if (visualise):
        # Creates a new image on which the projection profiles are visualised.
        # Kludge: Using PIL to create an image because, for reasons I'm too tired to debug, image saving fails if the
        # array is created with np.zeros().
        # (proj = numpy.zeros((i+101,j+101), dtype=np.int))
        # im = Image.new('L', (j+101,i+101), 255)
        im = Image.new("RGB", (j + 101, i + 101), "white")
        proj = numpy.array(im)

        # Pastes in the existing image.
        for i in range(0, img.shape[0]):
            for j in range(0, img.shape[1]):
                proj[i, j] = [img[i, j], img[i, j], img[i, j]]

        # Draws the horizontal distribution.
        for i in range(0, img.shape[0]):
            for j in range(0, normHorList[i]):
                proj[i, img.shape[1] + j] = [255, 0, 0]

        # Draws the vertical distribution.
        for j in range(0, img.shape[1]):
            for i in range(0, normVerList[j]):
                proj[img.shape[0] + i, j] = [255, 0, 0]

        ret = Facsimile(proj, facsName)
        if Levers.debugFlag:
            ret.save()
        return (normHorList, normVerList, ret)
    else:
        return (normHorList, normVerList, None)


def findFirstPeak(li, minDrop=10):
    """
    Tries to find the first peak in a normalised list containing a projection profile's pixel counts.
    (This is very much an amateur effort, but it was found to work alright. @add proper maths.)
    """
    startSearch = 0

    for x in range(0, len(li)):
        if (startSearch == 0):
            if (abs(li[x] - li[0]) >= minDrop):
                startSearch = 1

        if (startSearch == 1):

            if (x - 1 >= 0 and x + 1 < len(li)):
                # pixel-wise local maximum; larger than its immediate neighbours.
                if (li[x] >= li[x - 1] and li[x] >= li[x + 1]):
                    # Search left and right; true if more change than minDrop before finding any value that is larger.
                    if (searchTest(li, x - 1, -1, li[x]) and searchTest(li, x + 1, +1, li[x])):
                        # returning the index to the first peak
                        return x


def searchTest(li, k, step, testMax):
    """
    A function used by findFirstPeak().

    :return:
    """
    minDrop = 10

    if (step == -1):
        end = -1
    if (step == 1):
        end = len(li)

    for x in range(k, end, step):
        if (li[x] > testMax):
            return False
        if (abs(testMax - li[x]) >= minDrop):
            return True

    return False


def getCutoffIndex(li, startIndex, requiredChange=40, step=20, tries = 1):
    """
    Given an index of the maximum value in a peak, seeks to locate the next plateu and returns the index for cutoff.
    Enough change needs to have happened for the cutoff to be sought for; then, once a sliding window detects no more
    change it triggers and selects the cutoff point.
    """
    initialValue = li[startIndex]
    lastValue = initialValue
    change = -1

    windowSizes = [step, 10, 5, 25]
    changeSizes = [requiredChange, 30, 20]

    for c in range(0, len(changeSizes)):
        for w in range(0, len(windowSizes)):
            for i in range(startIndex, len(li), windowSizes[w]):  # note: in some circumstances, this windowing might not work.
                change = abs(lastValue - li[i])
                lastValue = li[i]
                if (initialValue - li[i] >= changeSizes[c]):
                    if (change <= 4 and change != -1):
                        return i

    # We're about to return None
    print ("WARNING: Could not find cutoff index.")
    return None


def getReverseCutoffIndex(li, startIndex, requiredChange=40):
    """
    Traverses the peak backwards; returns an index on the original list.
    """
    revLi = li
    revLi.reverse()
    revIndex = len(li) - 1 - startIndex
    ind = getCutoffIndex(revLi, revIndex, requiredChange)

    return len(li) - 1 - ind


def cropBorderShadows(binFacs, facsName):
    """
    Crops the dark borders that have resulted from image acquisition.
    :param binFacs: binarised facsimile of a spread
    :param facsName:
    :return:
    """

    # Sometimes the adaptive binarisation fails in cases when there are lighter and darker shadows. A work-around
    # is to beforehand blacken bands immediately next to each image border.
    tempArray = binFacs.getImage()
    bi,bj = tempArray.shape

    for j in range(0, 50):
        for i in range(0, bi):
            tempArray[i][j] = 0

    for j in range(bj-51, bj):
        for i in range(0, bi):
           tempArray[i][j] = 0

    for i in range(0, 50):
        for j in range(0, bj):
            tempArray[i][j] = 0

    for i in range(bi-51, bi):
        for j in range(0, bj):
            tempArray[i][j] = 0

    tempFacs = Facsimile(tempArray, "tempBinImg", binFacs.getOffset)
    if Levers.debugFlag:
        tempFacs.save()

    # Let's get the projections.
    (normHorList, normVerList, binarisedProj) = getProjections(tempFacs, 'binarisedProj', False)

    # Let's find the coordinates after the peaks which are assumed to be present in every edge.
    # Let's eat away 50px more. todo: the names are wrong way. cropTop = left, etc.
    cropTop = getCutoffIndex(normVerList, 0) + 50
    cropBot = getReverseCutoffIndex(normVerList, len(normVerList) - 1) - 50
    cropLeft = getCutoffIndex(normHorList, 0) + 50
    cropRight = getReverseCutoffIndex(normHorList, len(normHorList) - 1) - 50

    # Get the image to work with; PIL is used to create the image and to perform the crop.
    tempImage = Image.fromarray(binFacs.getImage())

    # Crop the image according to the region we specified by searching for the cutoff points.
    box = (cropTop, cropLeft, cropBot, cropRight)
    croppedRegion = tempImage.crop(box)

    # Creating a new Facsimile
    binOffset = binFacs.getOffset()
    remBorders = Facsimile(numpy.array(croppedRegion), facsName, (cropLeft + binOffset[0], cropTop + binOffset[1]))
    if Levers.debugFlag:
        remBorders.save()

    return remBorders


def prepareSpread(facsIn):
    """
    Prepares a temporary image for the spread by whitening the content area; this helps to e.g. detect gutter shadow.
    Used by extractPages().
    :param facsIn:
    :return:
    """
    arrayIn = facsIn.getImage()

    (normHorList, normVerList, facsInProj) = getProjections(facsIn, 'facsInProj', Levers.debugFlag)

    topCut = findFirstPeak(normHorList)

    if topCut == None:
        topCut = int(len(normHorList) * 0.2)
    normHorList.reverse()
    bCut = findFirstPeak(normHorList)

    if bCut == None:
        bCut = int(len(normHorList) * 0.2)

    bottomCut = len(normHorList) - bCut

    # Whitens the area where the textual signal resides.
    for i in range(topCut, bottomCut):
        if (i > topCut and i < bottomCut):
            for j in range(0, arrayIn.shape[1]):
                arrayIn[i, j] = 255

    # fu.nbimage(arrayIn)
    return Facsimile(arrayIn, 'tmp', facsIn.getOffset())


def extractPages(remBorders):
    """
    Separates and extracts the two pages of an opening using the gutter shadow or a mathematical centrepoint.
    Returns two page facsimiles.
    :param remBorders:
    :return:
    """
    tempFacs = Facsimile(remBorders.getImage(), 'tempFacs', remBorders.getOffset())
    # Generates a temp image, where textual content detected in the middle is removed (whitened).
    tempFacs = prepareSpread(tempFacs)
    if Levers.debugFlag == True:
        tempFacs.save()

    # Generates a projection profile image for the cropped image.
    (normHorList, normVerList, remBordersProj) = getProjections(tempFacs, 'preparedSpreadProj', Levers.debugFlag)

    # Let's find the regions of the two pages by finding the shadow of the gutter. The assumption is that that is the highest peak.
    # Find index of highest peak - the index gives the horizontal coordinate for the vertical peak.
    # Page 2 starts after the peak.
    peakIndex = normVerList.index(max(normVerList))
    page2Start = getCutoffIndex(normVerList, peakIndex)

    # Page 1 ends just before the peak.
    page1End = getReverseCutoffIndex(normVerList, peakIndex)

    # Requirement: peakIndex +-10% from the spread's horizontal centre-point.
    window = remBorders.getImage().shape[1] / 10
    centrepoint = int(remBorders.getImage().shape[1] / 2)

    if (abs(centrepoint - peakIndex) > window):
        print ("WARNING. There is an indication that gutter shadow was not detected correctly. Using mathematical centrepoint for page cutting.")
        page1End = centrepoint - 1
        page2Start = centrepoint + 1

    # Let's crop the page images.
    crp = Image.fromarray(remBorders.getImage())
    p1 = (0, 0, page1End, remBorders.getImage().shape[0])
    p2 = (page2Start, 0, remBorders.getImage().shape[1], remBorders.getImage().shape[0])

    pag1 = crp.crop(p1)
    pag2 = crp.crop(p2)

    rbOffset = remBorders.getOffset()

    page1Img = Facsimile(numpy.array(pag1), 'page1Img', (rbOffset[0], rbOffset[1]))
    page2Img = Facsimile(numpy.array(pag2), 'page2Img', (rbOffset[0], page2Start + rbOffset[1]))

    if Levers.debugFlag:
        page1Img.save()
        page2Img.save()

    return [page1Img, page2Img]


def applyMask(pageImg, facsName):
    """
    Enhances the textual signal for further processing by bloating the text CCs with a mask.
    The idea is to fill small white regions in-between text, and thus strengthen the profile signal of the text area.
    The mask doesn't extend the text area sideways when bordered by whitespace; but it can slightly expand
    characters vertically.
    :param pageImg:
    :param facsName:
    :return:
    """
    img = pageImg.getImage()

    # Let's run the mask through the image. The central pixel is changed only if both left and right regions contain ink.
    for j in range(0, img.shape[1]):
        for i in range(0, img.shape[0]):
            if (img[i, j] == 255):
                if (searchBlack(img, i - 1, j - 4) and searchBlack(img, i - 1, j + 1)):
                    img[i, j] = 0

    maskedPage = Facsimile(img, facsName, pageImg.getOffset())
    if Levers.debugFlag:
        maskedPage.save()

    return maskedPage


def searchBlack(img, i, jin):
    """
    Searches for a region for black pixels. If found, returns True; else False.
    Used by applyMask().
    """
    for i in range(i, i + 3):
        j = jin
        for j in range(j, j + 4):
            if (i >= 0 and i < img.shape[0] and j >= 0 and j < img.shape[1]):
                if (img[i, j] == 0):
                    return True
    return False


def cleanBorders(facsIn):
    """
    Removes connected components adjacent to the input image's vertical edges.
    :param facsIn:
    :return:
    """
    binImg = facsIn.getImage()
    (i, j) = binImg.shape

    ccList = []
    toCheck = set()

    for x in range(0, i):
        if (binImg[x, 0] == 0):
            toCheck.add((x, 0))

    for x in range(0, i):
        if (binImg[x, j - 1] == 0):
            toCheck.add((x, j - 1))

    while not len(toCheck) == 0:
        ccList.append(findCC2(binImg, toCheck.pop()))

    for x in range(0, len(ccList)):
        l = ccList[x].getPixelList()
        for y in range(0, len(l)):
            (a, b) = l[y]
            binImg[a, b] = 255

    ret = Facsimile(binImg, facsIn.imageType + "Cleaned", facsIn.getOffset())
    return ret


def cleanBorders2(arrayIn):
    """
    This is used from the main ipynb.
    :param arrayIn:
    :return:
    """

    filterList = []

    leftMostCC = findBorderMostConnectedComponents(arrayIn.copy(), 'left')
    for i in range(0, len(leftMostCC)):
        imin,imax,jmin,jmax = leftMostCC[i].getMinMax()
        if jmin<6:
            if jmax-jmin < 10:
                filterList.append(leftMostCC[i])

    rightMostCC = findBorderMostConnectedComponents(arrayIn.copy(), 'right')
    for i in range(0, len(rightMostCC)):
        imin,imax,jmin,jmax = rightMostCC[i].getMinMax()
        if arrayIn.shape[1]-jmax < 6:
            if jmax-jmin < 10:
                filterList.append(rightMostCC[i])

    for i in range(0, len(filterList)):
            pixList = filterList[i].getPixelList()
            for j in range(0, len(pixList)):
                a,b = pixList[j]
                arrayIn[a][b] = 255

    return arrayIn


def analyseSkewDetectionArea(facsIn):
    """
    Analyses the top 20% of the image by calculating its connected components: if too few are detected, the page
    is deemed blank.
    :param facsIn:
    :return:
    """
    # Let's get top 20% of the masked page
    pilImg = Image.fromarray(facsIn.getImage())
    cropBox = (0, 0, facsIn.getImage().shape[1], int(facsIn.getImage().shape[0] * 0.20))
    croppedRegion = pilImg.crop(cropBox)
    topArea = numpy.array(croppedRegion)
    topPart = Facsimile(topArea, 'skewDetectionArea', (0, 0))
    if Levers.debugFlag:
        topPart.save()

    ret = topPart

    # Searches only up and until the required threshold.
    ccList = findConnectedComponents(topPart.getImage(), 30, 30)

    #print ("Detected number of CCs >", len(ccList))
    if len(ccList) < 30:
        ret = None

    return ret


def calculateDividerAngle(dividerCC):
    """
    Calculates the angle of the divider, which is later used in page-level skew correction.
    :param dividerCC:
    :return:
    """
    imin,imax,jmin,jmax = dividerCC.getMinMax()

    pixList = dividerCC.getPixelList()

    # If the length is not sufficient, let's use the old method.
    if imax-imin < 500:
        print("Warning: Cannot use divider angle in skew estimation - the detected divider is too short.")
        return None

    # Get starting point
    startingPoint = -1,-1
    for i in range(0, len(pixList)):
        if pixList[i][0] == imin:
            startingPoint = pixList[i]
            break

    # Get a point near 90% mark (reason: sometimes there's a slight curve towards the very end of the printed divider)
    endPoint = -1,-1
    for i in range(0, len(pixList)):
        if pixList[i][0]-imin >= (imax-imin)*0.85 and pixList[i][0]-imin <= (imax-imin)*0.95:
            endPoint = pixList[i]
            break

    # Calculates the angle from the two points.
    adjacent = endPoint[0]-startingPoint[0]
    opposite = endPoint[1]-startingPoint[1]
    divAngle = math.degrees( math.atan( (opposite/adjacent) ) )

    divAngle = round((divAngle/1.0), 2)

    return divAngle


def detectSkew(facsIn, topPart):
    """
    Detects the skew from a partial area of the facsimile. The detection is based on a property of the normalised
    projection signal, where a sharper line detection lessens the total signal area.
    Note: Although this method worked alright with up to 90%-95%+ of cases, this is now secondary; a divider-based
    method gives more accurate results.

    :param facsIn:
    :param topPart:
    :return:
    """

    # If there are errors, consider the following:
    # - Only detect skew based on the outward 50% of the page image (i.e. using different area to detect skew);
    # - If clearly delineated peaks are not found, then do not rotate the image at all.
    #   The first peak must be within a certain height, otherwise do not rotate? (i.e. detecting failure).

    smallestSum = topPart.getImage().shape[0] * 100
    bestAngle = -1

    # Tests different angles.
    for i in range(-3, 2, 1):
        for j in range(0, 4): #2 to 4
            if (j == 0):
                angle = i
            else:
                angle = i + 0.25 #0.5 to 0.25

            rotPart = rotateImage(topPart, angle, 'rotTopPart' + str(angle))
            # rotPart.save()

            (normHorList, normVerList, rotProj) = getProjections(rotPart, 'rotProj', None)

            if (sum(normHorList) < smallestSum):
                smallestSum = sum(normHorList)
                bestAngle = angle

    #print ("best angle:", bestAngle)
    return bestAngle


def rotateImage(facsIn, angle, facsName):
    """
    Rotates the input image according to the desired angle.
    :param facsIn:
    :param angle:
    :param facsName:
    :return:
    """
    # @rewrite.
    arrayIn = facsIn.getImage()
    for a in range(0, arrayIn.shape[0]):
        for b in range(0, arrayIn.shape[1]):
            if (arrayIn[a, b] == 0):
                arrayIn[a, b] = 127
    pilImg = Image.fromarray(arrayIn)
    pilImg = pilImg.rotate(angle)

    arrayIn = numpy.array(pilImg)
    for a in range(0, arrayIn.shape[0]):
        for b in range(0, arrayIn.shape[1]):
            if (arrayIn[a, b] == 0):
                arrayIn[a, b] = 255
            if (arrayIn[a, b] == 127):
                arrayIn[a, b] = 0

    rotPart = Facsimile(arrayIn, facsName, facsIn.getOffset())
    #rotPart.save()
    return rotPart


def findDateLine(facsIn, facsName):
    """
    Tries to find the dateline from the top 20% of the input image according to 1) horizontal projection
    profile; and 2) examination of connected components in that area.

    Todo: redesign this function; it's way too cumbersome as it is.

    :param facsIn: binarised facsimile in
    :param facsName: name for output facsimile
    :return:
    """
    # Let's get top 20% of the masked page
    pilImg = Image.fromarray(facsIn.getImage())
    cropBox = (0, 0, facsIn.getImage().shape[1], int(facsIn.getImage().shape[0] * 0.20))
    croppedRegion = pilImg.crop(cropBox)
    topArea = numpy.array(croppedRegion)
    topPart = Facsimile(topArea, 'dateLineDetectionArea', (0, 0))
    if Levers.debugFlag:
        topPart.save()

    # Let's generate a projection profile for the masked image.
    (normHorList, normVerList, maskedPageProj) = getProjections(topPart, 'dateLineDetectionAreaProj', Levers.debugFlag)

    # Let's find the first peak, and cut-off points before and after it.
    ind = findFirstPeak(normHorList, 10)
    cutoff = getCutoffIndex(normHorList, ind, 10)
    cutoff2 = getReverseCutoffIndex(normHorList, ind, 10)

    # Enforces a max_limit for the peak.
    if (cutoff-cutoff2) > 75:  # 100 to 75
        cutoff = cutoff2+75

    # Let's find the substantial connected components from the area.
    ccList = findConnectedComponents(facsIn.getImage(), 40, -1, cutoff2, cutoff)

    # Filter CCs that are too long.
    for y in range(len(ccList)-1,-1,-1):
        imin,imax,jmin,jmax = ccList[y].getMinMax()

        if imax-imin > 70:
            ccList.remove(ccList[y])


    ccList = sortCCList(ccList, 'vertical')  # Note: direction not implemented.

    # Let's find the first CC with at least three other CC:s on the same level horizontally; and return a list
    # of them.
    tentativeList = []
    for i in range(0, len(ccList)):

        tentativeList.append(ccList[i])
        imin, imax, jmin, jmax = ccList[i].getMinMax()

        for j in range(0, len(ccList)):
            if (ccList[i] != ccList[j]):
                # if the CC is within the area specified by the first CC, then add to the list;
                # i.e. if the two min to maxs overlap.
                i2min, i2max, j2min, j2max = ccList[j].getMinMax()

                # if either of the values is in the range; or bigger.
                if (i2min >= imin and i2min <= imax):
                    tentativeList.append(ccList[j])
                    if (i2min < imin):
                        imin = i2min
                    if (i2max > imax):
                        imax = i2max
                    continue
                elif (i2max >= imin and i2max <= imax):
                    tentativeList.append(ccList[j])
                    if (i2min < imin):
                        imin = i2min
                    if (i2max > imax):
                        imax = i2max
                    continue
                elif (i2min < imin and i2max > imax):
                    tentativeList.append(ccList[j])
                    if (i2min < imin):
                        imin = i2min
                    if (i2max > imax):
                        imax = i2max
                    continue

        if (len(tentativeList) > 3):
            break
        else:
            tentativeList = []

    # A dateline was not found.
    if len(tentativeList) == 0:
        return None, None

    # Crop a new region for the dateline according to the actual line
    lineMin = 1000000
    lineMax = 0

    widthTemp = []
    for i in range(len(tentativeList)):
        imin, imax, jmin, jmax = tentativeList[i].getMinMax()
        widthTemp.append(jmax-jmin)
        if (imin < lineMin):
            lineMin = imin
        if (imax > lineMax):
            lineMax = imax

    widthTemp.sort()

    medianWidth = widthTemp[ int(len(widthTemp)/2) ]
    # TODO: always when medianWidth/Height are used, there should be a maximum value set for them as a constraint.
    merge = True

    while (merge and len(tentativeList) > 1):
        merge = False

        # Let's connect dateline CC:s less than a medianWidth away from each other, if one is small and smaller.
        for i in range(len(tentativeList)-1, -1, -1):
            loppu = False
            for j in range(len(tentativeList)-1, -1, -1):
                if (i != j):

                    if (calculateCCDistance2(tentativeList[i], tentativeList[j]) <= (medianWidth)):

                        pcount1 = tentativeList[i].getPixelCount()
                        pcount2 = tentativeList[j].getPixelCount()

                        if (pcount1 < (pcount2/2) or pcount2 < (pcount1/2)):
                            if (pcount1 < 150 or pcount2 < 150):
                                #print ("merging")
                                cc1 = tentativeList[i]
                                cc2 = tentativeList[j]
                                pl1 = tentativeList[i].getPixelList()
                                pl2 = tentativeList[j].getPixelList()
                                newlist = []

                                for z in range(0, len(pl1)):
                                    newlist.append(pl1[z])
                                for z in range(0, len(pl2)):
                                    newlist.append(pl2[z])

                                mrg = ConnectedComponent(newlist)

                                tentativeList.remove(cc1)
                                tentativeList.remove(cc2)
                                tentativeList.append(mrg)
                                loppu = True
                                merge = True
                                break
            if (loppu):
                break

    # Filter insubstantial CC after the above merging; less than 150pix overall;
    # Note: this could be the threshold for the look-up of CCs, but this allows fragments to be merged.
    for y in range(len(tentativeList)-1,-1,-1):
        if (tentativeList[y].getPixelCount() < 150):
            tentativeList.remove(tentativeList[y])
            continue

    # Filter small loner-CCs that aren't supported by a close CC
    for y in range(len(tentativeList)-1, -1, -1):
        supported=False

        # if height larger than 25, let's skip.
        imin,imax,jmin,jmax = tentativeList[y].getMinMax()
        if (imax-imin) > 25:
            continue

        for z in range(len(tentativeList)-1, -1, -1):
            if (y != z):
                if (calculateCCDistance2(tentativeList[y], tentativeList[z]) <= (medianWidth*3)):
                    supported=True
                    break
        if supported == False:
            tentativeList.remove(tentativeList[y])

    cropBox2 = (0, lineMin-1, facsIn.getImage().shape[1], lineMax+1)
    croppedRegion2 = pilImg.crop(cropBox2)

    mOffset = facsIn.getOffset()

    dateLine = Facsimile(numpy.array(croppedRegion2), facsName, (mOffset[0] + lineMin, mOffset[1]))

    if Levers.debugFlag==True:
        dateLine.save()

    return dateLine, tentativeList


def getRGBArray(baseFacs):
    """
    A helper function to create a white RGB image and paste in the contents from a greyscale/binarised image.
    :param baseFacs:
    :return:
    """
    imgArray = numpy.array(Image.new("RGB", (baseFacs.shape[1], baseFacs.shape[0]), "white"))
    baseFacsImg = baseFacs

    # Pasting in existing contents from baseFacs
    for i in range(0, imgArray.shape[0]):
        for j in range(0, imgArray.shape[1]):
            val = baseFacsImg[i, j]
            if (isinstance(val, int)):
                val = [val, val, val]
            imgArray[i, j] = val
    return imgArray


def renderFacsCC(baseFacs, cc, facsName, offset, colourIn='default'):
    """
    A helper function to render CCs on top of the facsimile.
    """
    imgArray = getRGBArray(baseFacs.getImage())
    imgArray = renderArrayCC(imgArray, cc, offset, colourIn)
    ret = Facsimile(imgArray, facsName, baseFacs.getOffset())
    if Levers.debugFlag:
        ret.save()
    return ret


def renderArrayCC(imgArray, cc, offset, colourIn='default'):
    """
    A helper function to render an array of CCs on top of the image array.
    """
    pixlist = cc.getPixelList()
    for p in range(0, len(pixlist)):
        (i, j) = pixlist[p]
        if (colourIn == 'default'):
            colour = [255, 0, 0]
        else:
            colour = colourIn
        imgArray[i + offset[0], j + offset[1]] = colour

    return imgArray


def renderFacsCCList(baseFacs, cclist, facsName, offset, colourIn='default'):
    """
    A helper function to render a list of CCs on top of the facsimile.
    """
    imgArray = getRGBArray(baseFacs.getImage())

    for i in range(0, len(cclist)):
        imgArray = renderArrayCC(imgArray, cclist[i], offset, colourIn)
    ret = Facsimile(imgArray, facsName, baseFacs.getOffset())
    if Levers.debugFlag:
        ret.save()
    return ret


def renderArrayCCList(imgArray, cclist, offset, colourIn='default'):
    """
    A helper function to render a list of CCs on top of the image array.
    """
    for i in range(0, len(cclist)):
        imgArray = renderArrayCC(imgArray, cclist[i], offset, colourIn)
    return imgArray


def renderFacsCCClusters(baseFacs, clusters, facsName, offset, colourIn='default'):
    """
    A helper function to render CC clusters on top of the facsimile with a rotating colour.
    """
    imgArray = getRGBArray(baseFacs.getImage())

    for k in range(0, len(clusters)):
        if (colourIn == 'default'):
            if (k % 3 == 0):
                colour = [255, 0, 0]
            if (k % 3 == 1):
                colour = [0, 255, 0]
            if (k % 3 == 2):
                colour = [0, 0, 255]
        else:
            colour = colourIn

        imgArray = renderArrayCCList(imgArray, clusters[k], offset, colour)

    ret = Facsimile(imgArray, facsName, baseFacs.getOffset())
    if Levers.debugFlag:
        ret.save()

    return ret


def findDatelineClusters(ccList):
    """
    Sorts the detected connected components of the dateline into logical clusters.

    Requirements: sorts dateline components into three clusters for resolutions, two for index; selects the centre
    cluster correctly;
    :param ccList: sorted list of dateline's connected components
    :return: a list of lists with ccList divided into "clusters"
    """
    # Todo: One could also use two longest horizontal spaces to separate CCs into clusters as long as the spacess are
    # 1) between two CCs; 2) between a CC and the gutter (or the gutter and a CC)

    widthTemp = []
    for l in range(0, len(ccList)):
        (imin,imax,jmin,jmax) = ccList[l].getMinMax()
        widthTemp.append(jmax-jmin)

    widthTemp.sort()
    medianWidth = widthTemp[ int(len(widthTemp)/2) ]

    clusters = []
    new_cluster = []
    new_cluster.append(ccList[0])

    for i in range(1, len(ccList)-1):

        distanceBackward = calculateCCDistance2(ccList[i], new_cluster[ len(new_cluster)-1])
        distanceForward = calculateCCDistance2(ccList[i], ccList[i+1])

        appended = True
        if (distanceBackward > 220):
            if (distanceBackward > 2* distanceForward):
                clusters.append(new_cluster)
                new_cluster = []
                new_cluster.append(ccList[i])
                appended = False
        if (appended):
            new_cluster.append(ccList[i])

    # Examine the last one. Might cause a break.
    append=True
    lastDistanceBackward = calculateCCDistance2(ccList[ len(ccList) -1 ], ccList[ len(ccList) -2 ])
    prevDistanceBackward = calculateCCDistance2(ccList[ len(ccList) -2 ], ccList[ len(ccList) -3 ])
    if lastDistanceBackward > 1.5 * prevDistanceBackward:
        if lastDistanceBackward > 4.5*medianWidth:
            clusters.append(new_cluster)
            new_cluster = []
            new_cluster.append( ccList[ len(ccList) -1 ])
            append=False

    if append:
        new_cluster.append( ccList[ len(ccList) -1 ])
    clusters.append( new_cluster )

    return clusters


def sortCCListHorizontally(cclist):
    """
    Sorts a list of connected components horizontally in ascending order.
    :param cclist: a list of connected components
    :return: the list sorted horizontally in ascending order
    """

    # Let's arrange the list according to their first cc's first pixel coordinate's j-pixel
    for j in range(1, len(cclist)):
        temp = cclist[j]
        a, b = cclist[j].getPixelList()[0]
        i = j
        c, d = cclist[i - 1].getPixelList()[0]
        while (i > 0 and d >= b):
            cclist[i] = cclist[i - 1]
            i = i - 1
            if (i > 0):
                c, d = cclist[i - 1].getPixelList()[0]
        cclist[i] = temp

    return cclist


def sortCCList(cclist, direction='vertical'):
    """
    Sorts a CC list in a vertical direction.
    Todo: remove redundant code (cf. sortCCListHorizontally()); implement horizontal direction.
    """

    for j in range(1, len(cclist)):
        temp = cclist[j]
        i1min, i1max, j1min, j1max = cclist[j].getMinMax()
        i = j

        i2min, i2max, j2min, j2max = cclist[i-1].getMinMax()
        while (i > 0 and i2min >= i1min):
            cclist[i] = cclist[i - 1]
            i = i - 1
            if (i > 0):
                i2min, i2max, j2min, j2max = cclist[i-1].getMinMax()
        cclist[i] = temp

    return cclist


def spliceDividerArea(facsIn, dateLineIn, middleCluster):
    """
    The column divider is situated under the page number component of a dateline. In an effort to find the column
    divider, let's splice the page image according to dateline's middle component.
    """
    # Find the area specified by the dateline component.
    leftMost = facsIn.getImage().shape[1]
    rightMost = 0
    bottomMost = 0

    for i in range(0, len(middleCluster)):
        cc = middleCluster[i]
        imin, imax, jmin, jmax = cc.getMinMax()

        if (jmin < leftMost):
                leftMost = jmin
        if (jmax > rightMost):
                rightMost = jmax

    # Bottom most from the whole dateline, not only the centre cluster.
    bottomMost = dateLineIn.getOffset()[0]+dateLineIn.getImage().shape[0]-facsIn.getOffset()[0]

    spliceImage = Image.fromarray(facsIn.getImage())
    splicer = (leftMost, bottomMost+1, rightMost, facsIn.getImage().shape[0])
    splice = spliceImage.crop(splicer)
    #fu.nbimage(array(splice))
    dlOffset = dateLineIn.getOffset()

    columnDividerSplice = Facsimile(numpy.array(splice), 'columnDividerSplice', (facsIn.getOffset()[0]+bottomMost+1, facsIn.getOffset()[1]+leftMost))
    if Levers.debugFlag:
        columnDividerSplice.save()

    return columnDividerSplice


def getCentreCluster(facsIn, clusters):
    """
    Gets and returns the centre cluster of CCs of a dateline.

    """

    centrePoint = int(facsIn.getImage().shape[1]/2)  #horizontal centre point

    tempDistance = facsIn.getImage().shape[1]
    tempIndex = 0
    for i in range(0, len(clusters)):
        cclist = clusters[i]

        for j in range(0, len(cclist)):
            cc = cclist[j]

            # todo: do I really need to iterate the pixel list? no.
            if ( abs(centrePoint - cc.getPixelList()[0][1]) < tempDistance ):
                    tempDistance = abs(centrePoint - cc.getPixelList()[0][1])
                    tempIndex = i

    return clusters[tempIndex]


def applyVerticalMask(facsIn, facsName):
    """
    Applies a vertical bloating mask to enhance the signal, because e.g. rotation of a binarised image can break lines.
    See applyMask() for horizontal; @remove redundant code.
    """

    img = facsIn.getImage()

    # Let's run the mask through the image. The central pixel is changed only if both left and right regions contain ink.

    for i in range(0, img.shape[0]):
        for j in range(0, img.shape[1]):
            if (img[i,j] == 255):
                if (searchVerticalBlack(img,i-4, j-1) and searchVerticalBlack(img, i+1, j-1)):
                    img[i,j] = 0

    maskedPage = Facsimile(img, facsName, facsIn.getOffset())
    if Levers.debugFlag:
        maskedPage.save()

    return maskedPage


def searchVerticalBlack(img, iin,j):
    """
    Searches for a region for black pixels. If found, returns True; else False.
    @remove redundant code.
    """
    for j in range(j, j+3):
        i = iin
        for i in range(i, i+4):
            if (j >= 0 and j < img.shape[1] and i >= 0 and i < img.shape[0]):
                if (img[i,j] == 0):
                    return True
    return False


def findDividingLine(columnDividerSplice):
    """
    Tries to locate the dividing line in the input splice.
    :param columnDividerSplice:
    :return:
    """

    dividerArea = columnDividerSplice.getImage()

    ccList = findConnectedComponents(columnDividerSplice.getImage(), 30)

    # Remove the ones that touch the splice borders horizontally
    for y in range(len(ccList)-1,-1,-1):

        # If lengthwise, let's not remove it.
        (imin, imax, jmin, jmax) = ccList[y].getMinMax()
        iLen = imax-imin
        jLen = jmax-jmin

        if jmin == 0 or jmax == dividerArea.shape[1]-1:

            # if it spans the whole splice, remove.
            if jmin == 0 and jmax == dividerArea.shape[1]-1:
                ccList.remove(ccList[y])
                continue

            # let's not remove it if its length-wise
            if iLen > 3*jLen:
                continue
            ccList.remove(ccList[y])
            continue

    # Remove the ones that are not "lengthwise"
    for y in range(len(ccList)-1,-1,-1):

        (imin, imax, jmin, jmax) = ccList[y].getMinMax()
        iLen = imax-imin
        jLen = jmax-jmin

        if iLen < 3*jLen:
            ccList.remove(ccList[y])

    # Get the longest CC; merge others to it if they share direction. Or, that is, if they are in less than n px away from each other.
    # Actually, the direction is the same because of the lengthwise test. Here, just test the proximity.

    # merge others to the longest CC if they are close by
    merge = True

    while (merge and len(ccList) > 1):

        merge = False
        #print "Starting again. Length: ", len(ccList2)
        for i in range(len(ccList)-1, -1, -1):
            loppu = False
            #print "i",i
            for j in range(len(ccList)-1, -1, -1):
                #print "j",j
                if (ccList[i] != ccList[j]):
                    if (calculateEndpointDistance(ccList[i], ccList[j]) < 35): #30 to 35, Dec 9th;
                        # TODO: calculate distance from vertical endpoints only.
                        # no vertical overlap allowed
                        imin1,imax1,jmin1,jmax1 = ccList[i].getMinMax()
                        imin2,imax2,jmin2,jmax2 = ccList[j].getMinMax()

                        if (imin1 > imin2 and imin1 < imax2) or (imax1 > imin2 and imax1 < imax2) or (imin1 <= imin2 and imax1 >= imax2):
                            #overlap
                            #print ("overlap")
                            pass
                        else:
                            #print "merging"

                            cc1 = ccList[i]
                            cc2 = ccList[j]
                            pl1 = ccList[i].getPixelList()
                            pl2 = ccList[j].getPixelList()

                            for z in range(0, len(pl2)):
                                pl1.append(pl2[z])

                            mrg = ConnectedComponent(pl1)
                            mrg.calculateMinMax()
                            ccList.remove(cc1)
                            ccList.remove(cc2)
                            ccList.append(mrg)
                            loppu = True
                            merge = True
                            break
            if (loppu):
                break

    #get the longest CC
    longIndex = -1
    length = -1
    for y in range(0, len(ccList)):
        cc = ccList[y]
        (imin, imax, jmin, jmax) = cc.getMinMax()
        l = imax-imin
        if (l > length):
            length = l
            longIndex = y

    dividerCC = None
    if (longIndex >= 0 and longIndex < len(ccList)):
        dividerCC = ccList[longIndex]

    return dividerCC


def getCCEndpoints(ccIn, dir='vertical'):
    """
    Gets and returns the furthestmost endpoints of CCs.
    """

    minCoords = []
    maxCoords = []

    pixList = ccIn.getBorderPixels()

    minPoint = 10000000
    maxPoint = -10000000

    for i in range(0, len(pixList)):

        if dir == 'vertical':
            if pixList[i][0] < minPoint:
                minPoint = pixList[i][0]
                minCoords = []
                minCoords.append(pixList[i])
                continue
            if pixList[i][0] == minPoint:
                minCoords.append(pixList[i])
                continue
            if pixList[i][0] > maxPoint:
                maxCoords = []
                maxCoords.append(pixList[i])
                continue
            if pixList[i][0] == maxPoint:
                maxCoords.append(pixList[i])
                continue

    coords = []
    for i in range(0, len(minCoords)):
        coords.append(minCoords[i])
    for i in range(0, len(maxCoords)):
        coords.append(maxCoords[i])

    return coords


def calculateEndpointDistance(p1, p2):
    """
    Calculates CC distance based on the identified endpoints.
    """
    pixels1 = getCCEndpoints(p1)
    pixels2 = getCCEndpoints(p2)

    minDist = 10000000

    for x in range(0, len(pixels1)):
        for y in range(0, len(pixels2)):
            c11, c12 = pixels1[x]
            c21, c22 = pixels2[y]
            dist = int(round(math.sqrt(math.pow((c11 - c21), 2) + math.pow((c12 - c22), 2))))
            if (minDist > dist):
                minDist = dist

    return minDist


def extractColumns(pageIn, columnDividerSplice, dividerCC, columnMin, columnMax, unmaskedPage):
    """
    Extracts columns along the line of the divider.
    """
    imin,imax,jmin,jmax = dividerCC.getMinMax()
    topPixel = None
    bottomPixel = None

    for i in range(0, len(dividerCC.getPixelList())):
        pix = dividerCC.getPixelList()[i]
        if pix[0] == imin:
            topPixel = pix
        if pix[0] == imax:
            bottomPixel = pix
        if topPixel != None and bottomPixel != None:
            break

    # Calculate equation: j = start + i*step
    step = (bottomPixel[1]-topPixel[1])/(bottomPixel[0]-topPixel[0])

    start = topPixel[1] + step*topPixel[0]

    copyLeft = pageIn.getImage()
    copyRight = pageIn.getImage()
    copyUnmaskedLeft = unmaskedPage.getImage()
    copyUnmaskedRight = unmaskedPage.getImage()

    offsetI = columnDividerSplice.getOffset()[0]-pageIn.getOffset()[0]
    offsetJ = columnDividerSplice.getOffset()[1]-pageIn.getOffset()[1]

    # todo: limit looping below later according to top and bottom limits, etc.
    # clear left
    for i in range(0, copyLeft.shape[0]):
        jstart = int(start + (i * step))
        for j in range(jstart, jmax+5):
            copyLeft[i][j+offsetJ] = 255
            copyUnmaskedLeft[i][j+offsetJ] = 255

    # clear right
    for i in range(0, copyRight.shape[0]):
        jend = int(start + (i * step))
        for j in range(jmin-5, jend):
            copyRight[i][j+offsetJ] = 255
            copyUnmaskedRight[i][j+offsetJ] = 255

    # clear divider
    for i in range(0, len(dividerCC.getPixelList())):
        a,b = dividerCC.getPixelList()[i]
        copyLeft[a+offsetI][b+offsetJ] = 255
        copyRight[a+offsetI][b+offsetJ] = 255
        copyUnmaskedLeft[a+offsetI][b+offsetJ] = 255
        copyUnmaskedRight[a+offsetI][b+offsetJ] = 255

    if columnMin != -1:
        topCutoff = columnMin-pageIn.getOffset()[0]
    else:
        topCutoff = columnDividerSplice.getOffset()[0]-pageIn.getOffset()[0]

    divLeftCutoff = jmax + columnDividerSplice.getOffset()[1]-pageIn.getOffset()[1]-5
    divRightCutoff = jmin +columnDividerSplice.getOffset()[1]-pageIn.getOffset()[1]+5

    # Let's define the regions for the two columns according to the cutoff points, and crop the page images accordingly.

    baseLeft = Image.fromarray(copyLeft)
    baseRight = Image.fromarray(copyRight)
    if columnMax != -1:
        bottomCutoff = columnMax - pageIn.getOffset()[0]
        col1Box = (0,topCutoff,divLeftCutoff, bottomCutoff)
        col2Box = (divRightCutoff,topCutoff,copyRight.shape[1], bottomCutoff)

    else:
        col1Box = (0,topCutoff,divLeftCutoff, copyLeft.shape[0])
        col2Box = (divRightCutoff,topCutoff,copyRight.shape[1], copyRight.shape[0])

    col1 = baseLeft.crop(col1Box)
    col2 = baseRight.crop(col2Box)

    mpOffset = pageIn.getOffset()

    col1Img = Facsimile(numpy.array(col1), 'col1Img', (mpOffset[0]+topCutoff, mpOffset[1]))
    col2Img = Facsimile(numpy.array(col2), 'col2Img', (mpOffset[0]+topCutoff, divRightCutoff+mpOffset[1]))
    if Levers.debugFlag:
        col1Img.save()
        col2Img.save()

    copyUnmaskedLeftFacs = Facsimile(copyUnmaskedLeft, 'copyUnmaskedLeft', unmaskedPage.getOffset())
    copyUnmaskedRightFacs = Facsimile(copyUnmaskedRight, 'copyUnmaskedLeft', unmaskedPage.getOffset())

    return [col1Img, col2Img], (copyUnmaskedLeftFacs, copyUnmaskedRightFacs)


def findBorderMostConnectedComponents(binImg, direction, substantialLimit = 100, mode='default'):

    # Let's find all right-most, left-most and bottom-most _substantial_ connected components.
    # If there are problems, I could use a stronger bloating mask later.

    if (direction=='left'):
        start = 0
        end = binImg.shape[0]
        start2 = 0

        step = 10
        end2 = int(binImg.shape[1]/2)
        step2 = 1

    if (direction=='right'):
        start=0
        end = binImg.shape[0]
        start2 = binImg.shape[1]-1
        if mode != "lineFinding":
            end2 = int(binImg.shape[1]/2)
            step = 10
        else:
            end2 = 50 #binImg.shape[1]
            step = 2
        step2 = -1
    if (direction == 'bottom'):
        start = 0
        end = binImg.shape[1]
        step = 10
        start2 = binImg.shape[0]-1
        end2 = int(binImg.shape[0]/2)
        step2 = -1

    ccList = []
    toCheck = set()

    verticalStopList = []
    horizontalStopList = []

    for j in range(start, end, step):
        for i in range(start2, end2, step2):
            if (direction == 'right' or direction == 'left'):
                if (binImg[j,i] == 0):
                    toCheck.add((j,i))
                    break
            else:
                if (binImg[i,j] == 0 ):
                    toCheck.add((i,j))
                    break

    while not len(toCheck) == 0:
        ccList.append(findCC2(binImg, toCheck.pop()))

    # Filter tiny CC; less than the limit (default 100pix) overall
    for y in range(len(ccList)-1,-1,-1):
        if (ccList[y].getPixelCount() < substantialLimit):
            ccList.remove(ccList[y])

    # for left, filter out according to height as well. (added 16.10.)
    if direction=='left':
        for y in range(len(ccList)-1,-1,-1):
            imin,imax,jmin,jmax = ccList[y].getMinMax()
            if (imax-imin) < 14:
                ccList.remove(ccList[y])

    # Filter overlapping more inward CCs
    filtered = True
    while (filtered):
        filtered=False
        loppu = False

        for i in range(len(ccList)-1, -1, -1):
            for j in range(len(ccList)-1,-1,-1):
                if (i != j):

                    i_imin, i_imax, i_jmin, i_jmax = ccList[i].getMinMax()
                    j_imin, j_imax, j_jmin, j_jmax = ccList[j].getMinMax()

                    if (direction == "right"):
                        for p in range(i_imin, i_imax):
                            if (p >= j_imin and p <= j_imax):
                                if (i_jmax > j_jmax):
                                    ccList.remove(ccList[j])
                                    loppu = True
                                    filtered=True
                                    break
                    if (direction == "left"):
                        for p in range(i_imin, i_imax):
                            if (p >= j_imin and p <= j_imax):
                                if (i_jmin < j_jmin):
                                    if (mode=="initialCap"):
                                        # only remove if they overlap substantially
                                        i_height = i_imax - i_imin
                                        j_height = j_imax - j_imin
                                        if (abs(i_height-j_height) < 0.5*i_height):
                                            ccList.remove(ccList[j])
                                            loppu = True
                                            filtered=True
                                            break
                                    else:
                                        ccList.remove(ccList[j])
                                        loppu = True
                                        filtered=True
                                        break
                    if (direction == "bottom" and mode=="default"):
                        for p in range(i_jmin, i_jmax):
                            if (p >= j_jmin and p <= j_jmax):
                                if (i_imax > j_imax):
                                    ccList.remove(ccList[j])
                                    loppu = True
                                    filtered=True
                                    break
                if (loppu):
                    break
            if (loppu):
                break

    return ccList


def removeCatchwords(facsIn):
    """ removes catchwords and printers markings that are present only on right-hand side columns on both pages
        as the last line.
    :return:
    """
    facsArea = facsIn.getImage()
    # (1) find the lowest-most substantial CC; (2) find other CCs on the same horizontal line; (3) remove them from the image
    # starting from their highest location.
    bottomMostCC = findBorderMostConnectedComponents(facsIn.getImage(), 'bottom', 50, "catchWord") # 10 to 50

    # find lowest CC; require it to be substantial.
    lowestCoordinate = 0
    lowestCC = None
    for i in range(0, len(bottomMostCC)):
        cc = bottomMostCC[i]
        imin,imax,jmin,jmax = cc.getMinMax()
        if (imax > lowestCoordinate and cc.getPixelCount() > 50):

            # also, let's require it to be entirely on the right-60% of the image
            if jmin > int(0.4*facsArea.shape[1]):

                # also: it needs to be of sufficient height.
                if imax-imin > 18:
                    # and sufficient width
                    if jmax-jmin > 15:
                        lowestCoordinate = imax
                        lowestCC = cc

    bottomMostCC.remove(lowestCC)

    # find bottom-line
    bottomLine = [lowestCC]
    imin,imax,jmin,jmax = lowestCC.getMinMax()

    # Instead, I could find the bottom line by cascading sideways from the bottomMost and always selecting the nearest
    # neighbour according to overlap of the vertical bottom half (would give it more skew resistance).

    for i in range(0, len(bottomMostCC)):
        for j in range(imin+int((imax-imin)/2), imax):
            imin2,imax2,jmin2,jmax2 = bottomMostCC[i].getMinMax()

            if (j >= imin2 and j <= imax2):
                bottomLine.append(bottomMostCC[i])
                break

    catchWordImage = renderFacsCCList(facsIn, bottomLine,'catchword', (0,0))

    bottomMostCoordinate = 0
    redFlag = False
    for i in range(0, len(bottomLine)):
        imin,imax,jmin,jmax = bottomLine[i].getMinMax()
        if imax > bottomMostCoordinate:
            bottomMostCoordinate = imax

        if (jmin < 100):
            # a component is near the left-edge. shouldn't happen with real catchwords.
            redFlag = True
            #print ("redFlag with catchword finding; aborting.")
            break

    if redFlag == False:
        # remove the identified catchword CCs
        for i in range(0, len(bottomLine)):
            pixList = bottomLine[i].getPixelList()
            for j in range(0, len(pixList)):
                a,b = pixList[j]
                facsArea[a][b] = 255

        # also, remove anything below
        a,b = facsArea.shape
        for i in range(bottomMostCoordinate, a):
            for j in range(0, b):
                facsArea[i][j] = 255

    facsIn.setImage(facsArea)
    return facsIn


def removeExtraWhitespace(col1Img, colNbr, leftMostCC, rightMostCC, bottomMostCC):

    tempArray = col1Img.getImage()
    # Limit the column so that all the bordering components, but no more are behind the limit. In order to find the cutoff point,
    # let's examine the CC: a cutoff point needs to be supported for it to be selected, i.e. it needs to have close neighbours.
    # This is to prevent a single blob detected as CC from determining the cutoff point.
    # For example, needs to have two additional CC:s within 20px radius.

    # read all the left_most values into a list. Sort that list. Pick a value.
    leftValues = []
    for i in range (0, len(leftMostCC)):
        (imin,imax,jmin,jmax) = leftMostCC[i].getMinMax()
        leftValues.append(jmin)

    rightValues = []
    for i in range (0, len(rightMostCC)):
        (imin,imax,jmin,jmax) = rightMostCC[i].getMinMax()
        rightValues.append(jmax)

    bottomValues = []
    for i in range (0, len(bottomMostCC)):
        (imin,imax,jmin,jmax) = bottomMostCC[i].getMinMax()
        bottomValues.append(imax)

    leftValues.sort()
    rightValues.sort()
    rightValues.reverse()
    bottomValues.sort()
    bottomValues.reverse()

    # Condition: next two values on the list within 50px
    leftCutoff = 0
    for i in range(0, len(leftValues)-2):
        if (abs(leftValues[i+1] - leftValues[i])<= 50 and abs(leftValues[i+2] - leftValues[i]) <= 50):
            leftCutoff = leftValues[i]-1
            break

    rightCutoff = col1Img.getImage().shape[1]
    for i in range(0, len(rightValues)-2):
        if (abs(rightValues[i] - rightValues[i+1]) <= 50 and abs(rightValues[i]-rightValues[i+2]) <= 50):
            rightCutoff = rightValues[i]+1
            break

    bottomCutoff = col1Img.getImage().shape[0]

    for i in range(0, len(bottomValues)-1):

        breakFlag = False
        # kludge: a sufficiently long CC works fine without support (e.g. a merged word)
        for j in range(0, len(bottomMostCC)):
            imin,imax,jmin,jmax = bottomMostCC[j].getMinMax()
            if bottomValues[i] == imax:
                width = jmax-jmin
                if width > 40:
                    #print("bottomCC width more than 40; validates without support.")
                    bottomCutoff = bottomValues[i]+1
                    breakFlag = True
                    break
        if breakFlag:
            break
        if (abs(bottomValues[i] - bottomValues[i+1]) <= 20):
            bottomCutoff = bottomValues[i]+1
            break

    baseTmp = Image.fromarray(tempArray)
    col1Box = (leftCutoff,0,rightCutoff, bottomCutoff)
    col1 = baseTmp.crop(col1Box)
    mpOffset = col1Img.getOffset()
    col1ImgCropped = Facsimile(numpy.array(col1), 'col1ImgCropped', (mpOffset[0], mpOffset[1]+leftCutoff))
    if Levers.debugFlag:
        col1ImgCropped.save()
    return col1ImgCropped


def unmaskFacsimile(baseFacs, maskedFacs, facsName):
    # Get the corresponding area from the 'binarised image' or from the 'rotated binarised page image'

    baseOrig = Image.fromarray(baseFacs.getImage())

    (i1,j1) = baseFacs.getOffset()
    (i2,j2) = maskedFacs.getOffset()
    (i,j) = (i2-i1, j2-j1)

    (a,b) = maskedFacs.getImage().shape
    cropBox = (j, i, j+b, i+a)
    unmasked = baseOrig.crop(cropBox)
    maskedFacsUnmasked = Facsimile(numpy.array(unmasked), facsName, maskedFacs.getOffset())
    if Levers.debugFlag:
        maskedFacsUnmasked.save()

    return maskedFacsUnmasked


def drawRegionBorders(arrayIn, facsIn, colour, width):

    offset = facsIn.getOffset()
    regionIn = facsIn.getImage().shape

    for w in range(0,width):

        for x in range(0, regionIn[0]):
            arrayIn[offset[0]+x, offset[1]+w] = colour

        for y in range(0, regionIn[1]):
            arrayIn[offset[0]+w, offset[1]+y] = colour

        for x in range(0, regionIn[0]):
            arrayIn[offset[0]+x, offset[1]+regionIn[1]-w] = colour

        for y in range(0, regionIn[1]):
            arrayIn[offset[0]+regionIn[0]-w, offset[1]+y] = colour

    arrayOut = arrayIn
    return arrayOut


def overlayRegion(baseIn, overlayFacs):

    offset = overlayFacs.getOffset()
    overlay = overlayFacs.getImage()

    for i in range(0, overlay.shape[0]):
        for j in range(0, overlay.shape[1]):

            val = overlay[i,j]
            if (isinstance(val,int)):
                val = [val,val,val]
            baseIn[i+offset[0],j+offset[1]] = val

    return baseIn


def analyseDivider(dividerCC, baseFacs, dividerFacs):
    """
    Performs a naive analysis of the recognised column divider line; acts if it's either markedly distant from
    the dateline or from the bottom of the page.

    :param dividerCC:
    :param baseFacs:
    :param dividerFacs:
    :return:
    """
    # CR: I could pass the heading area to Tesseract and save it into XML as <ab>...</ab>.
    columnMin = -1
    columnMax = -1
    baseArea = baseFacs.getImage()

    # Divider's min and max i coordinates:
    dividerMin,dividerMax,jmin,jmax = dividerCC.getMinMax()

    # The coordinate is relative to the columnDividerArea, which starts just under the dateline.
    # In normal cases, the divider starts very close to the column divider area's top.
    if dividerMin < 500 and dividerFacs.getImage().shape[0]-dividerMax < 600:
        return (columnMin,columnMax)

    if dividerMin >= 500:

        #print ("According to analysis of the divider, the page is possibly the starting page of the body of resolutions.")

        # Let's check if there's a vertical white space across the image.
        # Create a test area
        baseOffsetI, baseOffsetJ = baseFacs.getOffset()
        dividerOffsetI, dividerOffsetJ = dividerFacs.getOffset()

        # Calculate relative offset
        offsetI = dividerOffsetI - baseOffsetI

        testImage = Image.fromarray(baseArea)
        testAreaBox = (0,offsetI,baseArea.shape[1],dividerMin+50+offsetI)
        testArea = numpy.array(testImage.crop(testAreaBox))

        testFacs = Facsimile(testArea, "testAreaTop")
        #fu.nbimage(testFacs.getImage())

        spaceCand = col.findVerticalSpaceCandidates(testFacs, 20)

        # Find the space with the shortest distance to dividerITop
        closestSpace = None
        distanceTemp = 10000000
        for t in range(0, len(spaceCand)):
            botI, botJ = spaceCand[t].getEnd()
            distance = abs(dividerMin - botI)
            if distance < distanceTemp:
                distanceTemp = distance
                closestSpace = spaceCand[t]

        if closestSpace != None:
            # Let's get the space's end coordinate.
            botI, botJ = closestSpace.getEnd()


            if distanceTemp < 50:
                # Changing the divider offset; this will be used in the next processing stage to cut the columns accordingly.
                columnMin = dividerFacs.getOffset()[0]+botI-1

    if dividerFacs.getImage().shape[0]-dividerMax >= 600:
        #print ("According to analysis of the divider, the page is possibly the starting page of the body of resolutions.")

        # Let's check if there's a vertical white space across the image.
        # Create a test area
        baseOffsetI, baseOffsetJ = baseFacs.getOffset()
        dividerOffsetI, dividerOffsetJ = dividerFacs.getOffset()

        # Calculate relative offset
        offsetI = dividerOffsetI - baseOffsetI

        testImage = Image.fromarray(baseArea)
        testAreaBoxTop = (0, dividerMax-50+offsetI, baseArea.shape[1], baseArea.shape[0])
        testAreaTop = numpy.array(testImage.crop(testAreaBoxTop))
        testFacs = Facsimile(testAreaTop, "testAreaTop")
        #fu.nbimage(testFacs.getImage())

        spaceCand = col.findVerticalSpaceCandidates(testFacs, 46)

        renderCands = diu.renderSections(testFacs, spaceCand, "cands", (127,0,0))

        # Find the space with the shortest distance to dividerMax
        closestSpace = None
        distanceTemp = 10000000
        for t in range(0, len(spaceCand)):
            begI, begJ = spaceCand[t].getStart()
            distance = abs(50 - begI)
            if distance < distanceTemp:
                distanceTemp = distance
                closestSpace = spaceCand[t]

        if closestSpace != None:

            # Let's get the space's end coordinate.
            botI, botJ = closestSpace.getEnd()

            if distanceTemp < 50:
                # Changing the divider offset; this will be used in the next processing stage to cut the columns accordingly.
               columnMax = dividerMax + distanceTemp + 1 + dividerFacs.getOffset()[0]

    return (columnMin, columnMax)

