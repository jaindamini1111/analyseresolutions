# AnalyseResolutions - ColumnLevel. Tuomo Toljamo (King's College London; DiXiT) at the Huygens ING (KNAW), 2016.
#
# This PhDWare code-sketch was part of a pilot exploring the use and usefulness of image data and visual information in
# the digital opening of an archival series, the Resolutions of the States General 1576‒1796.
#
# DiXiT (Digital Scholarly Editions Initial Training Network) has been funded from the People Programme (Marie Curie Actions)
# of the European Union's Seventh Framework Programme FP7/2007-2013/ under REA grant agreement n° 317436.

import DocumentImageAnalysis as dia
import DocumentImageUnderstanding as diu
import Levers
from PIL import Image
import numpy as np


class InitialCapital():
    """
    Holds the large initial capitals identified from the flow of columns.
    """

    def __init__(self, initialCC):
        self.initialCC = initialCC
        self.sectionOffset = (0,0)

    def getInitialCC(self):
        return self.initialCC

    def getPixelList(self):
        return self.initialCC.getPixelList()

    def setSectionOffset(self, iTop, jTop):
        self.sectionOffset = (iTop, jTop)

    def getSectionOffset(self):
        return self.sectionOffset

    def getMinMax(self):
        return self.initialCC.getMinMax()


class TextLine():
    """
    Holds a graphical text line identified during the analysis of column/column section layout.
    """

    def __init__(self, ccList):
        self.ccList = ccList
        self.offset = (0,0)
        self.imin = -1
        self.imax = -1
        self.jmin = -1
        self.jmax = -1

    def getCCList(self):
        return self.ccList

    def getWidth(self):
        if (self.imin != -1):
            return (self.jmax - self.jmin)
        else:
            self.calculateMinMax()
            return (self.jmax - self.jmin)

    def setOffset(self, iTop, jTop):
        self.offset = (iTop, jTop)

    def getOffset(self):
        return self.offset

    def getMinMax(self):
        if (self.imin != -1):
            return (self.imin, self.imax, self.jmin, self.jmax)
        else:
            self.calculateMinMax()
            return (self.imin, self.imax, self.jmin, self.jmax)

    def calculateMinMax(self):
        self.imax = -1
        self.imin = 100000000
        self.jmax = -1
        self.jmin = 100000000
        for i in range(0, len(self.ccList)):
            imin2,imax2,jmin2,jmax2 = self.ccList[i].getMinMax()

            if imin2 < self.imin:
                self.imin = imin2

            if imax2 > self.imax:
                self.imax = imax2

            if jmin2 < self.jmin:
                self.jmin = jmin2

            if jmax2 > self.jmax:
                self.jmax = jmax2


def findInitialCapitalCandidates(baseFacs):
    """
    Searches for candidates for large initial capitals.

    Known issues:
    - On few occasions, letters can be joined from ascenders/descenders and visually seem very much like large initials.
    """
    initialCapCandidateList = []

    leftMostCC = dia.findBorderMostConnectedComponents(baseFacs.getImage(), 'left', 200, "initialCap")

    # Calculate median bounding box
    medianTemp = []
    pixelCountTemp = []

    for i in range (0, len(leftMostCC)):
        (imin,imax,jmin,jmax) = leftMostCC[i].getMinMax()
        medianTemp.append((jmax-jmin)*(imax-imin))
        pixelCountTemp.append(leftMostCC[i].getPixelCount())

    medianTemp.sort()
    pixelCountTemp.sort()
    medianBoxSize = medianTemp[int(len(medianTemp)/2)]
    medianPixelCount = pixelCountTemp[int(len(pixelCountTemp)/2)]

    for i in range(0, len(leftMostCC)):
        imin,imax,jmin,jmax = leftMostCC[i].getMinMax()
        width = jmax-jmin
        length = imax-imin
        boundingBox = width*length

        # RULE: Initial caps need to be closer to the column edge than their widths.
        if (jmin < width):

            # RULE: Initial capital cannot be horizontally length-wise.
            if (width > 2*length):
                continue

            # RULE: Initial cap's bounding box area should be significantly larger than median CC's;
            # RULE: OR its pixel count should be significantly higher.
            if ( boundingBox > 4.5*medianBoxSize or leftMostCC[i].getPixelCount() > 4* medianPixelCount):
                initialCapCandidateList.append(InitialCapital(leftMostCC[i]))
                continue

            # If not found above; additional RULE: If vertically length-wise AND high pixel count.
            if ( length > 2 * width ):
                if (leftMostCC[i].getPixelCount() > 2.5*medianPixelCount):

                    #todo: refine rules to prevent chars joined from the tips of descenders/ascenders?
                    initialCapCandidateList.append(InitialCapital(leftMostCC[i]))

    return initialCapCandidateList


def findVerticalSpaceCandidates(facsIn, forceMinHeight = False):
    """
    Tries to find candidates for the significant vertical spacing between the lines of a column.
    """

    spaceCandidates = []   # Saves vertical coordinates for a space candidate

    cleanArea = facsIn.getImage()
    # Let's find substantial CCs
    ccList = dia.findConnectedComponents(cleanArea, 150)  # note: clears the area

    heightTemp = []

    for l in range(0, len(ccList)):
        (imin,imax,jmin,jmax) = ccList[l].getMinMax()
        # require a min width to be included in the substantials
        if jmax-jmin < 10:
            continue

        heightTemp.append(imax-imin)

        pl = ccList[l].getPixelList()
        # redraws the found substantial CCs
        for p in range(0, len(pl)):
            i,j = pl[p]
            cleanArea[i][j] = 0

    heightTemp.sort()
    medianHeight = heightTemp[ int(len(heightTemp)/2) ]

    if forceMinHeight != False:
        medianHeight = forceMinHeight

    # As vertical spaces, we save a sequence of white runs across the column image.
    spaceStart = 0
    spaceEnd = 0
    for i in range(0, cleanArea.shape[0]):
        isEmpty = True
        for j in range(0, cleanArea.shape[1]):
            if cleanArea[i][j] != 255:
                isEmpty = False
                break

        if (isEmpty):
            # empty line of pixels found, let's continue looking
            spaceEnd = i
        else:
            # line had black pixels, let's save line if it's substantial and reset start pointer.
            spaceEnd = i-1

            # TODO: threshold could be lower; spaces candidates are later validated.
            if (spaceEnd - spaceStart > 0.6*medianHeight):
                if spaceStart != 0:
                    spaceCandidates.append((spaceStart,spaceEnd))
            spaceStart = i+1

    # Saving found candidates for vertical spaces as physical sections.
    candidateSections = []
    for k in range(0, len(spaceCandidates)):
        candidateSections.append(diu.PhysicalSection(spaceCandidates[k][0]+1, 0, spaceCandidates[k][1]-1, cleanArea.shape[1], 'spaceCandidate'))

    return candidateSections


def segmentColumn(colFacs, initialCandidateList, spaceCandidateList, pageI, colJ):
    """
    Segments a column into physical sections according to capital initial and space candidates.
    """

    physicalSectionList = []
    validInitialsList = []
    validSpacesList = []

    # RAW MATERIAL:
    # 1. Column image; 2. Candidates for initial capitals; 3. Candidates for vertical spaces.
    # AIMS:
    # 1. Find physical sections; 2. Validate initial capitals; 3. Validate vertical spaces.

    # RULES:
    # - If a space candidate exists and in the following image area an initial capital is found at the top-left corner,
    #   then that physical section is found, initial capital is valid, and space is valid.
    # - If a space candidate exists, but there is no initial capital, let's check if the 'starting signature' is present.
    # ...
    #
    # Signature: long line, short line, [long line, column break]; all centred, no capital initials.
    #
    # Note: The logic here is that a segment break can only be validated by what it is followed by.

    colArray = colFacs.getImage()
    colArrayWithoutInitials = colFacs.getImage()

    # Let's prepare a column array without initial capitals' pixels.
    for i in range(0, len(initialCandidateList)):
        pixelList = initialCandidateList[i].getPixelList()
        for r in range(0, len(pixelList)):
            i,j = pixelList[r]
            colArrayWithoutInitials[i][j] = 255

    columnLines = findLines(colArrayWithoutInitials)

    # FIRST PASS: Find physical sections and valid spaces/initials according to spaces.
    thisArea = None
    nextArea = None
    thisAreaStart = 0
    lastLineFindStart = 0

    i = 0
    while i < len(spaceCandidateList):

        nextAreaStart = spaceCandidateList[i].getEnd()[0]

        if i < len(spaceCandidateList)-1:
            nextAreaEnd = spaceCandidateList[i+1].getStart()[0]
        else:
            nextAreaEnd = colArray.shape[0]
        nextArea = getImageArea(colArray, nextAreaStart, 0, nextAreaEnd, colArray.shape[1])

        # starting point for finding lines in the middle of the vertical space
        nextAreaLineFindingStartPoint = (spaceCandidateList[i].getEnd()[0]+spaceCandidateList[i].getStart()[0])/2

        # is valid break?
        validBreak = examineArea(nextAreaStart, nextAreaEnd, initialCandidateList, columnLines, colArray.shape[1], colArray.shape[0],
                                 nextAreaLineFindingStartPoint, lastLineFindStart)

        if (validBreak):
            validSpacesList.append(spaceCandidateList[i])

            thisArea = getImageArea(colArray, thisAreaStart, 0, spaceCandidateList[i].getStart()[0], colArray.shape[1])
            initialInArea = isInitialCapitalInArea(thisAreaStart, spaceCandidateList[i].getStart()[0], initialCandidateList)
            if initialInArea != None:
                validInitialsList.append(initialInArea)
                thisAreaWithoutInitial = getImageArea(colArrayWithoutInitials, thisAreaStart, 0, spaceCandidateList[i].getStart()[0], colArray.shape[1])
            else:
                thisAreaWithoutInitial = None
            physSection = diu.PhysicalSection(thisAreaStart, 0, spaceCandidateList[i].getStart()[0], colArray.shape[1], thisArea, initialInArea, pageI, colJ)
            physSection.setAreaWithoutInitial(getImageArea(colArrayWithoutInitials, thisAreaStart, 0, spaceCandidateList[i].getStart()[0], colArrayWithoutInitials.shape[1]))

            # Note: If break validates, it's the previous area that gets saved.
            if thisAreaStart == 0:
                thisAreaLineFindingStartPoint = 0
            else:
                thisAreaLineFindingStartPoint = (spaceCandidateList[i-1].getStart()[0] + spaceCandidateList[i-1].getEnd()[0])/2

            physSection.setLines(getLinesForArea(thisAreaLineFindingStartPoint, nextAreaLineFindingStartPoint, columnLines))
            physicalSectionList.append(physSection)

            thisAreaStart = spaceCandidateList[i].getEnd()[0]
            # kludge
            lastLineFindStart = (spaceCandidateList[i].getStart()[0]+spaceCandidateList[i].getEnd()[0])/2
            i =  i + 1
            continue
        else:
            # invalid spaces need to be removed; otherwise, look ups backward fail.
            spaceCandidateList.remove( spaceCandidateList[i])
            continue

    # Let's worry about the final line here; end of column is always a valid break.
    thisArea = getImageArea(colArray, thisAreaStart, 0, colArray.shape[0], colArray.shape[1])
    initialInArea = isInitialCapitalInArea(thisAreaStart, colArray.shape[0], initialCandidateList)
    if initialInArea != None:
        validInitialsList.append(initialInArea)
        thisAreaWithoutInitial = getImageArea(colArrayWithoutInitials, thisAreaStart, 0, colArray.shape[0], colArray.shape[1])
    else:
        thisAreaWithoutInitial = None
    physSection = diu.PhysicalSection(thisAreaStart, 0, colArray.shape[0], colArray.shape[1], thisArea, initialInArea, pageI, colJ)
    physSection.setAreaWithoutInitial(getImageArea(colArrayWithoutInitials, thisAreaStart, 0, colArray.shape[0], colArrayWithoutInitials.shape[1]))
    physSection.setLines(getLinesForArea(lastLineFindStart, colArray.shape[0], columnLines))
    physicalSectionList.append(physSection)

    return physicalSectionList, validInitialsList, validSpacesList


def examineArea(start, end, initialList, lines, colWidth, colLength, lineFindStart, prevLineFindEnd):
    """
    Examines a given area in helping to segment a column and to validate breaks/initials.
    """
    # Preceding break is valid if the area has an initial capital OR a starting section.
    # Initial cap needs to exist in the _next section_ to be valid.
    if (isInitialCapitalInArea(start, end, initialList) != None):
        return True

    # Starting bit can be found from what follows; however, it would be better to check that if the segmented
    # area only has a single line, then merge it here with the following area.

    # Let's check how many lines are in the prev section; if two or less, then return false.
    if prevLineFindEnd != 0:
        areaLines = getLinesForArea(prevLineFindEnd,lineFindStart,lines)
        if len(areaLines) < 3:
            return False

    if (isStartingSection(lineFindStart, colLength, lines, colWidth) == True):
        return True

    return False


def isInitialCapitalInArea(start, end, initialList):
    """
    Checks if there is initial capital within the boundaries of the area.
    """
    initial = None

    for i in range(0, len(initialList)):
        imin,imax,jmin,jmax = initialList[i].getMinMax()

        if (imin >= start and imax <= end):
            if abs(start-imin) < 50:
                initial = initialList[i]
                initial.setSectionOffset(start,0)
                break

    return initial


def isStartingSection(start, end, lines, colWidth):
    """
    Checks if the sections contains a 'starting signature', which means that it would be the start of the head section
    and start a new session of resolutions.
    """
    # True only if a signature is found.

    finalSection = False
    if start != -1 and end != -1:
        areaLines = getLinesForArea(start,end,lines)
        if len(areaLines) < 2:
            return False
        if areaLines[ len(areaLines)-1 ] == lines[ len(lines) - 1]:
            finalSection = True

    else:
        areaLines = lines

    if len(areaLines) < 2:
        return False

    if (finalSection):
        # two line signature
        return findSignature(areaLines, 2, colWidth)
    else:
        # three line signature; note: only two-line signatures sought for at the moment (tradeoff between recall and precision).
        return findSignature(areaLines,3, colWidth)


def getLinesForArea(start, end, lines):
    """
    Returns lines that reside within the given vertical bounds.
    """
    areaLines = []

    for i in range(0, len(lines)):
        imin,imax,jmin,jmax = lines[i].getMinMax()

        if (imin >= start and imax <= end):
            areaLines.append(lines[i])

    return areaLines


def getImageArea(baseArea, iTop, jTop, iBottom, jBottom):
    """
    Returns the image area according to the given coordinates.
    """

    # Get the image to work with; PIL is used to create the image and to perform the crop.
    tempImage = Image.fromarray(baseArea)

    # Crop the image according to the region we specified by searching for the cutoff points.
    box = (jTop, iTop, jBottom, iBottom)
    croppedRegion = tempImage.crop(box)

    return np.array(croppedRegion)


def findLines(arrayIn):
    """
    Searches for and returns graphical lines from the given column image.
    Note: this function should be re-designed completely (and made yet more robust).
    """
    arrayClean = arrayIn.copy()
    tempArray = dia.getRGBArray(arrayIn)

    # Finds the lines according to left and right-most CCs.
    # Note: Only CCs with immediate neighbours should be accepted.
    leftMostCC = dia.findBorderMostConnectedComponents(arrayClean, 'left', 50, "lineFinding")
    rightMostCC = dia.findBorderMostConnectedComponents(arrayClean, 'right', 50, "lineFinding")

    # Create a temporary combo list
    ccListCombo = []
    for i in range(0, len(leftMostCC)):
        ccListCombo.append(leftMostCC[i])
    for i in range(0, len(rightMostCC)):
        ccListCombo.append(rightMostCC[i])

    # calculate median height
    heightList = []
    for j in range(0, len(ccListCombo)):
        imin,imax,jmin,jmax = ccListCombo[j].getMinMax()
        heightList.append(imax-imin)

    heightList.sort()
    medianHeight = heightList[ int(len(heightList)/2) ]

    # let's examine the combo list
    for i in range(0, len(ccListCombo)):
        imin,imax,jmin,jmax = ccListCombo[i].getMinMax()

        # if over twice the size:
        if ((imax-imin) > (medianHeight*2.5)):   # 2 to 2.5 9th Dec
            # split the CC in the middle (it's a common occurrence that CC's from adjacent lines are entangled)
            pixList = ccListCombo[i].getPixelList()
            pixListTop = []
            pixListBottom = []

            for j in range(0, len(pixList)):
                if pixList[j][0] < (imin+((imax-imin)/2)):
                    pixListTop.append(pixList[j])
                else:
                    pixListBottom.append(pixList[j])

            # remove the old one; add the two new ones.
            if ccListCombo[i] in leftMostCC:
                leftMostCC.remove( ccListCombo[i] )
                newTop = dia.ConnectedComponent(pixListTop)
                newBottom = dia.ConnectedComponent(pixListBottom)
                leftMostCC.append(newTop)
                leftMostCC.append(newBottom)

            else:
                rightMostCC.remove( ccListCombo[i] )
                rightMostCC.append(dia.ConnectedComponent(pixListTop))
                rightMostCC.append(dia.ConnectedComponent(pixListBottom))

    # Complement borderMosts with the next close-by inward CCs to find a more robust seed for the line recognition.
    complementArea = arrayIn.copy()
    for i in range(0, len(leftMostCC)):
        for j in range(0, len(leftMostCC[i].getPixelList())):
            complementArea[leftMostCC[i].getPixelList()[j][0]][leftMostCC[i].getPixelList()[j][1]] = 255
    for i in range(0, len(rightMostCC)):
        for j in range(0, len(rightMostCC[i].getPixelList())):
            complementArea[rightMostCC[i].getPixelList()[j][0]][rightMostCC[i].getPixelList()[j][1]] = 255

    complementCCList = dia.findConnectedComponents(complementArea, 40)

    leftMostCC = complementBorderMosts(leftMostCC, complementCCList)
    rightMostCC = complementBorderMosts(rightMostCC, complementCCList)

    arrayRest = arrayIn.copy()
    for i in range(0, len(leftMostCC)):
        for j in range(0, len(leftMostCC[i].getPixelList())):
            arrayRest[leftMostCC[i].getPixelList()[j][0]][leftMostCC[i].getPixelList()[j][1]] = 255
        imin,imax,jmin,jmax = leftMostCC[i].getMinMax()
        for k in range(imin,imax):
            for l in range(0, jmin):
                arrayRest[k][l] = 255

    for i in range(0, len(rightMostCC)):
        for j in range(0, len(rightMostCC[i].getPixelList())):
            arrayRest[rightMostCC[i].getPixelList()[j][0]][rightMostCC[i].getPixelList()[j][1]] = 255
        imin,imax,jmin,jmax = rightMostCC[i].getMinMax()
        for k in range(imin,imax):
            for l in range(jmax, arrayRest.shape[1]-1):
                arrayRest[k][l] = 255

    pairs = findPairs(arrayIn, leftMostCC, rightMostCC)
    lines = completeLines(arrayRest, pairs)
    lines = dia.sortCCList(lines)
    if Levers.debugFlag:
        tempFacs = visualiseLines(lines, tempArray)
        #fu.nbimage(tempFacs.getImage())

    return lines


def complementBorderMosts(borderMostCC, complementCCList):
    """
    Complements CCs that have been located in the border-most position (i.e. at either edge).
    """
    # Complement identified border mosts with close-by and horizontally level CCs
    # TODO: this is amazingly inefficient in terms of computing time; it compares them all.
    removalList = []
    appendList = []

    for i in range(0, len(borderMostCC)):
        found = False

        for j in range(0, len(complementCCList)):

            imin,imax,jmin,jmax = borderMostCC[i].getMinMax()
            imin2,imax2,jmin2,jmax2 = complementCCList[j].getMinMax()

            # horizontally level
            if (imin > imax2 or imax < imin2):
                # no overlap
                continue
            # near-by
            if imin > imin2:
                overlapStart = imin
            else:
                overlapStart = imin2

            if imax < imax2:
                overlapEnd = imax
            else:
                overlapEnd = imax2

            if (overlapEnd-overlapStart) < 5:
                continue

            dist = dia.calculateCCDistance2(borderMostCC[i], complementCCList[j])
            if (dist < 15):
                # append pixels to leftMostCC
                pixList1 = borderMostCC[i].getPixelList()
                pixList2 = complementCCList[j].getPixelList()
                for k in range(0, len(pixList2)):
                    pixList1.append(pixList2[k])

                removalList.append( borderMostCC[i])
                appendList.append(dia.ConnectedComponent(pixList1))
                found = True
                break
        if (found):
            continue

    for i in range(0, len(removalList)):
        borderMostCC.remove( removalList[i] )

    for i in range(0, len(appendList)):
        borderMostCC.append(appendList[i])

    return borderMostCC


def findPairs(imgArray, leftMostCC, rightMostCC):
    """
    Seeks for CC pairs of left and right border-mosts which have the most substantial overlap.
    :param imgArray:
    :param leftMostCC:
    :param rightMostCC:
    :return:
    """
    pairs = []
    while (len(leftMostCC) + len(rightMostCC) > 0):

        tentativePair = False
        tentativeOverlap = 0
        tentativeLength = 0
        tentativeArea = 0

        for i in range(0, len(leftMostCC)):
            for j in range(0, len(rightMostCC)):

                imin, imax, jmin, jmax = leftMostCC[i].getMinMax()
                imin2, imax2, jmin2, jmax2 = rightMostCC[j].getMinMax()

                if (imin > imax2 or imax < imin2):
                    # no overlap
                    continue

                # let's require at least one of them to be of considerable height. 9th Dec
                if imax-imin < 13 and imax2-imin2 < 13:
                    continue

                commonIMin = -1
                for n in range(imin, imax):
                    if n >= imin2 and n <= imax2:
                        commonIMin = n
                        break
                commonIMax = -1
                for n in range(imax, imin-1, -1):
                    if n <= imax2 and n >= imin2:
                        commonIMax = n
                        break
                if (commonIMin == -1 or commonIMax == -1):
                    continue

                # goodness according to area
                area = (commonIMax-commonIMin)*(jmax2-jmin)
                if (area > tentativeArea):
                    tentativePair = (leftMostCC[i], rightMostCC[j], commonIMin, commonIMax)
                    tentativeArea = area

        if tentativePair != False:
            pairs.append(tentativePair)
            leftMostCC.remove(tentativePair[0])
            rightMostCC.remove(tentativePair[1])

        else:
            break

    return pairs


def sortLinesVertically(lines):
    """
    Sorts the line elements vertically according to an ascending order.
    """
    for j in range(1, len(lines)):
        temp = lines[j]
        i1min, i1max, j1min, j1max = lines[j].getMinMax()
        i = j

        i2min, i2max, j2min, j2max = lines[i-1].getMinMax()
        while (i > 0 and i2min >= i1min):
            lines[i] = lines[i - 1]
            i = i - 1
            if (i > 0):
                i2min, i2max, j2min, j2max = lines[i-1].getMinMax()
        lines[i] = temp

    return lines


def completeLines(arrayRest, pairs):
    """
    Takes the recognised bordermost pairs, and complements the lines by finding the middle CCs.
    """
    lines = []
    heightList = []

    for i in range(0, len(pairs)):
        lineCCList = []
        ccListRest = dia.findConnectedComponents(arrayRest, 50, -1, pairs[i][2], pairs[i][3], 0, arrayRest.shape[1])
        # sanity check: remove CCs that are too high (e.g. joint characters between two lines)

        for j in range(0, len(ccListRest)):
            imin,imax,jmin,jmax = ccListRest[j].getMinMax()
            heightList.append(imax-imin)

        heightList.sort()
        medianHeight = heightList[ int(len(heightList)/2) ]

        for j in range(len(ccListRest)-1, -1, -1):
            imin,imax,jmin,jmax = ccListRest[j].getMinMax()

            if ((imax-imin) > (medianHeight*2)):
                ccListRest.remove( ccListRest[j] )

        # create a TextLine
        lineCCList.append(pairs[i][0])
        for j in range(0, len(ccListRest)):
            lineCCList.append(ccListRest[j])
        lineCCList.append(pairs[i][1])

        lines.append(TextLine(lineCCList))

    return lines


def visualiseLines(lines, tempArray):
    """
    A mere helper function to visualise the recognised lines with alternative colours on top of the column image.
    """

    for i in range(0, len(lines)):
        if i%3==0:
            colour = (255,0,0)
        if i%3==1:
            colour = (0,255,0)
        if i%3==2:
            colour = (0,0,255)
        tempArray = dia.renderArrayCCList(tempArray, lines[i].getCCList(), (0,0), colour)

    if Levers.debugFlag:
        tempFacs = dia.Facsimile(tempArray, "line_candidate")
        tempFacs.save()
    return tempFacs


def isLayoutCentred(lines, colWidth):
    """
    Tests whether the given lines could be said to be centred.
    Note: Only tests the first 5 lines at the moment.
    """
    medianCCWidthList = []
    leftDistanceList = []
    rightDistanceList = []

    for i in range(0, len(lines)):
        for j in range(0, len(lines[i].getCCList())):
            imincc, imaxcc, jmincc, jmaxcc = lines[i].getCCList()[j].getMinMax()
            w = jmaxcc - jmincc
            medianCCWidthList.append(w)
        imin,imax,jmin,jmax = lines[i].getMinMax()
        leftDistanceList.append(jmin)
        rightDistanceList.append(colWidth-jmax)

        # let's only worry about first 5 lines.
        if i == 5:
            break

    medianCCWidthList.sort()
    medianWidth = medianCCWidthList[ int(len(medianCCWidthList)/2) ]
    averageLeftDistance = int(sum(leftDistanceList)/len(leftDistanceList))

    # On the right side, let's remove the largest distance - it could be a partial line.
    averageRightDistance = int((sum(rightDistanceList) - max(rightDistanceList))/(len(rightDistanceList)-1))

    if (averageLeftDistance > 2.7*medianWidth and averageRightDistance > 2.7*medianWidth):
        #print("true")
        return True
    else:
        #print("false")
        return False


def findSignature(lines, nbr, colWidth):
    """
    Finds the 'starting signature' - the signature of a starting bit: (1) centred; and
    (2) starts with a long line (date) followed by a short (year).
    Note: Only two-line signature examined at the moment.
    """
    nbr = 2 # Forces to two line examination; remove me later if needed.

    if isLayoutCentred(lines,colWidth) == False:
        #print("line is not centred")
        return False

    if nbr==2:
        # RULE: Second line must be shorter than the first line.
        if lines[0].getWidth() > 2* lines[1].getWidth():

            imin,imax,jmin,jmax = lines[0].getMinMax()
            imin2,imax2,jmin2,jmax2 = lines[1].getMinMax()

            # RULE: Both lines need to be centred (i.e. indented from both sides).
            if jmin < 50 or jmin2 < 50:
                return False

            if colWidth-jmax < 50 or colWidth-jmax2 < 50:
                return False

            # first line, either side must be well indented.
            if jmin < 70 and colWidth-jmax < 70:
                return False

            # RULE: Second line must start from more inward than the first line.
            if jmin2 - jmin > 30:
                return True
            else:
                return False
        else:
            return False

    #if nbr==3:

    return False
