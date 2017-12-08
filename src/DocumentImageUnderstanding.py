# AnalyseResolutions - DocumentImageUnderstanding. Tuomo Toljamo (King's College London; DiXiT) at the Huygens ING (KNAW), 2016.
#
# This PhDWare code-sketch was part of a pilot exploring the use and usefulness of image data and visual information in
# the digital opening of an archival series, the Resolutions of the States General 1576‒1796.
#
# DiXiT (Digital Scholarly Editions Initial Training Network) has been funded from the People Programme (Marie Curie Actions)
# of the European Union's Seventh Framework Programme FP7/2007-2013/ under REA grant agreement n° 317436.

import DocumentImageAnalysis as dia
import ColumnLevel as col
import TextProcessing as tp
import codecs
import numpy as np
from PIL import Image
import Levers
#from DocumentImageAnalysis import *
from subprocess import check_output


class LogicalSection():

    def __init__(self, sectionInit):
        self.sectionList = [sectionInit] # Contains: PhysicalSections, Column-breaks, and Page-breaks.
        self.identity = "ab"

    def getIdentity(self):
        return self.identity

    def setIdentity(self, s):
        self.identity = s

    def addSection(self, s):
        self.sectionList.append(s)

    def getSectionList(self):
        return self.sectionList


class PhysicalSection():

    def __init__(self, iTop, jTop, iBottom, jBottom, imgArea=None, initialCap = None, pageI = None, colJ = None):
        self.coordinates = (iTop, jTop, iBottom, jBottom)
        self.type = None
        self.position = None # initial, middle, final, only.
        self.imageArea = imgArea
        self.facsName = Levers.fileName.replace(".jpg", "")
        self.pageI = pageI
        self.colJ = colJ

        self.layout = None # Characteristics of layout: justified / centred. change: startingSignature
        self.startingSection = False
        self.InitialCapital = initialCap # Contains an Initial Capital
        self.initialTextContent = None
        self.textContent = None # Contains the textual content of the physical area.
        self.sessionId= None
        self.imageAreaWithoutInitial = None
        self.lines = None

    def getStart(self):
        return (self.coordinates[0], self.coordinates[1])

    def setPosition(self, pos):
        self.position = pos

    def getPosition(self):
        return self.position

    def setLayout(self, lay):
        self.layout = lay

    def getLayout(self):
        return self.layout

    def getEnd(self):
        return (self.coordinates[2], self.coordinates[3])

    def setInitialCapital(self, initCap):
        self.InitialCapital = initCap

    def getInitialCapital(self):
        return self.InitialCapital

    def getImageArea(self):
        return self.imageArea.copy()

    def setAreaWithoutInitial(self, imgArea):
        self.imageAreaWithoutInitial = imgArea

    def getPageI(self):
        return self.pageI

    def getColJ(self):
        return self.colJ

    def setTextContent(self, tc):
        self.textContent = tc

    def processTextContent(self, type):

        # todo: this should be conditional to body/head; also, wrap better list/list of lists.
        if type=="body":
            self.textContent = tp.processBodyText(self.textContent)
        if type=="head":
            self.textContent = tp.processHeadText(self.textContent)

    def setInitialTextContent(self, tc):
        self.initialTextContent = tc
        aggregate = ""
        for i in range(0, len(self.initialTextContent)):
            aggregate = aggregate + self.initialTextContent[i]

        self.initialTextContent = tp.processInitalText(aggregate)

    def getInitialTextContent(self):

        if (self.initialTextContent == None):
            return ""

        return self.initialTextContent

    def getTextContentString(self):
        aggregate = ""
        for i in range(0, len(self.textContent)):
            aggregate = aggregate + self.textContent[i] + "\r\n"

        return aggregate

    def getTextContent(self):
        return self.textContent

    def setSessionId(self, idIter):
        self.sessionId = idIter

    def getSessionId(self):
        return self.sessionId

    def setLines(self, lines):
        self.lines = lines

    def getLines(self):
        return self.lines

    def setStartingSection(self, b):
        self.startingSection = b

    def getStartingSection(self):
        return self.startingSection


def renderSections(baseFacs, sectionList, facsName, colourIn='default', offsetIn='default'):

    offset=[0,0]
    if offsetIn=='default':
        offset = [0,0]
    else:
        offset[0] = offsetIn[0]
        offset[1] = offsetIn[1]

    imgArray = dia.getRGBArray(baseFacs.getImage())

    for s in range(0, len(sectionList)):
        sec = sectionList[s]
        for i in range(sec.getStart()[0], sec.getEnd()[0]+1):
            for j in range(sec.getStart()[1], sec.getEnd()[1]):
                if (colourIn == 'default'):
                    colour = [255, 0, 0]
                else:
                    colour = colourIn
                imgArray[i+offset[0], j+offset[1]] = colour

    ret = dia.Facsimile(imgArray, facsName, baseFacs.getOffset())
    if Levers.debugFlag:
        ret.save()
    return ret

def getImageArea(baseArea, iTop, jTop, iBottom, jBottom):

    # Get the image to work with; PIL is used to create the image and to perform the crop.
    tempImage = Image.fromarray(baseArea)

    # Crop the image according to the region we specified by searching for the cutoff points.
    box = (jTop, iTop, jBottom, iBottom)
    croppedRegion = tempImage.crop(box)

    return np.array(croppedRegion)


def analyseSections(sectionList):

    toBeRemoved = []

    for t in range(0, len(sectionList)):

        if (t == 0):
            sectionList[t].setPosition("initial")
        if (t == len(sectionList)-1):
            sectionList[t].setPosition("final")
        if (t >= 1 and t < len(sectionList)-1):
            sectionList[t].setPosition("middle")
        if (len(sectionList) == 1):
            sectionList[t].setPosition("only")

        if (sectionList[t].getInitialCapital() != None):
            sectionList[t].setLayout("justified")
        else:
            isStart = col.isStartingSection(-1,-1,sectionList[t].getLines(), sectionList[t].getImageArea().shape[1])
            if isStart:
                sectionList[t].setLayout("startingSignature")
            else:
                sectionList[t].setLayout("justified")

    for t in range(len(toBeRemoved)-1, -1, -1):
        sectionList.remove(sectionList[toBeRemoved[t]])

    return sectionList


def buildElementQueue(sectionList, pagei, colj, datelineText):

    elementQueue = []

    # First: Add column header based on which page and which column are we processing.
    if (pagei==0 and colj==0):
        elementQueue.append("facs "+ Levers.fileName.replace(".jpg",""))
        elementQueue.append("pb "+ Levers.fileName.replace(".jpg","") + "#page" + str(pagei+1) + "##"+datelineText)
        elementQueue.append("cb "+ Levers.fileName.replace(".jpg","") + "#page" + str(pagei+1) + "_col" + str(colj+1))
    if (pagei==0 and colj==1):
        elementQueue.append("cb "+ Levers.fileName.replace(".jpg","") + "#page" + str(pagei+1) + "_col" + str(colj+1))
    if (pagei==1 and colj==0):
        elementQueue.append("pb "+ Levers.fileName.replace(".jpg","") + "#page" + str(pagei+1) + "##"+datelineText)
        elementQueue.append("cb "+ Levers.fileName.replace(".jpg","") + "#page" + str(pagei+1) + "_col" + str(colj+1))
    if (pagei==1 and colj==1):
        elementQueue.append("cb "+ Levers.fileName.replace(".jpg","") + "#page" + str(pagei+1) + "_col" + str(colj+1))

    for t in range(0, len(sectionList)):
        elementQueue.append(sectionList[t])

    return elementQueue


def createInitialImage(initial):

    imin,imax,jmin,jmax = initial.getMinMax()
    pixelList = initial.getInitialCC().getPixelList()

    im = Image.new("L", (jmax-jmin+1+2,imax-imin+1+2), "white")

    pixMap = np.array(im)
    for x in range(0, len(pixelList)):
        (i,j) = pixelList[x]
        pixMap[i-imin+1][j-jmin+1] = 0

    return pixMap


def ocrSections(sectionList):

    for t in range(0, len(sectionList)):
        if (isinstance(sectionList[t], str)):
            continue
        else:

            if sectionList[t].getInitialCapital() == None:
                sectionArea = sectionList[t].getImageArea()
                sectionName = "page"+str(sectionList[t].getPageI()) + "_col" + str(sectionList[t].getColJ())+"_section"+str(t)
                saveTesseractImage(sectionArea, sectionName)

                isStart = col.isStartingSection(-1,-1,sectionList[t].getLines(), sectionList[t].getImageArea().shape[1])
                if isStart == True:
                    sectionList[t].setTextContent(Tesseract(sectionName, "head"))
                else:
                    sectionList[t].setTextContent(Tesseract(sectionName, "body"))
            else:
                # There's an initial, let's OCR it separately.
                sectionName = "page"+str(sectionList[t].getPageI()) + "_col" + str(sectionList[t].getColJ())+"_section"+str(t)

                # create an image for the initial; save it as tif.
                initialArray = createInitialImage(sectionList[t].getInitialCapital())
                saveTesseractImage(initialArray, sectionName+"_i")

                # remove the initial from the section's tif.
                sectionOffset = sectionList[t].getInitialCapital().getSectionOffset()
                sectionArea = sectionList[t].getImageArea()
                imin,imax,jmin,jmax = sectionList[t].getInitialCapital().getMinMax()
                jmin=0
                for i in range(imin, imax):
                    for j in range(jmin, jmax):
                        sectionArea[i-sectionOffset[0]][j] = 255

                saveTesseractImage(sectionArea, sectionName)
                sectionList[t].setTextContent(Tesseract(sectionName, "body"))
                sectionList[t].setInitialTextContent(Tesseract(sectionName+"_i", "initial"))

    return sectionList


def saveTesseractImage(sectionArea, sectionName):
    """ Saves the image area as TIF; the Tesseract binaries in use only accept TIFs.
    :param sectionArea:
    :param sectionName:
    :return:
    """
    sectionArea = filterFragments(sectionArea)
    sectionArea = padTesseractSplice(sectionArea, 20)
    tmpSectionFacs = dia.Facsimile(sectionArea, "tmpSectionFacs")
    tmpSectionFacs.save(sectionName+"_tes", "default", "TIFF")


def Tesseract(sectionName, type='default'):
    """ Runs Tesseract on the input image splice.
    """
    recognisedContent = []

    if type=="default" or "body":
        tesseractConfig="-l custom_body_v2_1740_2+emop_body_v2_1740_2 -psm 6 bodyConfig.txt"
    if type=="dateline":
        tesseractConfig="-l custom_dateline_v1 -psm 4 datelineConfig.txt"
    if type=="head":
        tesseractConfig="-l custom_head_v2_1740_2 -psm 6 headConfig.txt"
    if type=="initial":
        tesseractConfig="-l custom_body_v2_1740_2+emop_body_v2_1740_2 -psm 10"

    # Let's use Tesseract
    command = "tesseract.exe "+Levers.dir_out+str(Levers.saveDir)+"/"+ sectionName+"_tes.tif " + Levers.dir_out+str(Levers.saveDir)+"/"+sectionName+"_tes " + tesseractConfig
    #print ("command", command)

    try:
        output = check_output(command)
        #print(output)
        recognisedContent = readTextFile(Levers.dir_out+str(Levers.saveDir)+"/" + sectionName +"_tes.txt")

    except Exception:
        print("Failed to use Tesseract.")
        #debug("["+fileList[f]+"]: " + "Failed to process the image.")

    # fix: Tesseract fails to read a TIF.
    if len(recognisedContent) == 0:
        recognisedContent.append(" ")

    if type=="dateline":
        if len(recognisedContent) > 1:
            recognisedContent = [' '.join(recognisedContent)]

    return recognisedContent


def padTesseractSplice(areaIn, pix):
    """ Pads the Tesseract splice with extra whitespace.
        Some have suggested that Tesseract's recognition results might worsen if the image is cropped too tightly.
        Let's mitigate that by adding extra padding to all the splices passed to Tesseract.
    :param areaIn:
    :param pix:
    :return:
    """

    #Let's find the dimensions
    i, j = areaIn.shape
    im = Image.new("L", (j+2*pix, i+2*pix), "white")
    pixMap = np.array(im)

    for a in range(0, areaIn.shape[0]):
        for b in range(0, areaIn.shape[1]):
            pixMap[a+pix][b+pix] = areaIn[a][b]

    return pixMap


def filterFragments(imageArea):
    """ Filters noise and other small fragments from the image area.
    :param imageArea:
    :return:
    """

    # Find CC:s with a threshold that cuts-off small CC:s
    cleanArea = imageArea
    ccList = dia.findConnectedComponents(cleanArea, 5)  # note: clears the area; gets CCs above 5pix

    # Let's try a context-sensitive filtering for CCs below a threshold
    ccList = contextSensitiveFilterFragments(ccList, 25)

    # Draws the remaining CCs back
    for l in range(0, len(ccList)):
        pl = ccList[l].getPixelList()
        for p in range(0, len(pl)):
            i,j = pl[p]
            cleanArea[i][j] = 0

    return cleanArea


def contextSensitiveFilterFragments(ccList, maxSize):
    """ Let's try to add a bit of intelligence to the removal of fragments.
    Here, we filter out smallish fragments that are not supported either: 1) by having a larger CC down;
    or 2) by having a larger CC left within a given distance.
    This should keep dots on the i's, and maybe punctuation.

    This filtering is done because OCR can be quite greedy to summon up characters for small fragments it encounters.
    :param ccList:
    :param maxSize:
    :return:
    """
    down = 10
    left = 10
    substantial = 40
    remList = []

    # Let's examine the small CCs, and for each of them, whether they have support or not.
    for i in range(0, len(ccList)):
        cc = ccList[i]

        # if the examined CC is not small enough, let's do nothing.
        if (ccList[i].getPixelCount() > maxSize):
            continue

        imin,imax,jmin,jmax = ccList[i].getMinMax()

        found = False
        for j in range(0, len(ccList)):
            if (i == j):
                continue

            if ccList[j].getPixelCount() < substantial:
                continue

            pixelList = ccList[j].getPixelList()

            # let's test support down
            for k in range(jmin-2, jmax+2):
                for l in range(imax+1, imax+1+down):
                    for m in range(0, len(pixelList)):
                        (a,b) = pixelList[m]
                        if (a==l and b==k):
                            found=True
                            break
                    if (found==True):
                        break
                if (found==True):
                    break
            if (found==True):
                break

            if (found==False):
                # let's test support left, if support down wasn't already found.
                for k in range(jmin, jmin-1-left, -1):
                    for l in range(imin-2, imax+2):
                        for m in range(0, len(pixelList)):
                            (a,b) = pixelList[m]
                            if (a==l and b==k):
                                found=True
                                break
                        if (found==True):
                            break
                    if (found==True):
                        break
                if (found==True):
                    break

        if found == False:
            remList.append(ccList[i])

    # let's filter out the CCs that are not down or left supported.
    for i in range(0, len(remList)):
        ccList.remove( remList[i] )

    return ccList


def readTextFile(fileName):

    content = []
    infile = codecs.open(fileName, "r", "utf-8")
    next = infile.readline()
    content.append(next)
    while next != "":
        next = infile.readline()
        content.append(next)

    infile.close()

    for i in range(0, len(content)):
        content[i] = content[i].replace("\r", "")
        content[i] = content[i].replace("\n", "")

    content = [x for x in content if x]
    return content


def processQueue(elementQueue,pagei,colj, document):
    # Let's feed the elements into XML

    for t in range(0, len(elementQueue)):
        document.insertSection( elementQueue[t] )


def getColumnText(physicalSections):
    colTextContent = []
    for t in range(0, len(physicalSections)):
        if physicalSections[t].getInitialCapital != None:
            initial=physicalSections[t].getInitialTextContent()
        else:
            initial = ""
        text = physicalSections[t].getTextContent()
        for s in range(0, len(text)):
            if s == 0:
                colTextContent.append(initial+text[s])
            else:
                colTextContent.append(text[s])
        colTextContent.append("\r\n")

    del colTextContent[len(colTextContent)-1]
    print (colTextContent)
    return colTextContent

