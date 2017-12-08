# AnalyseResolutions - XMLFactory. Tuomo Toljamo (King's College London; DiXiT) at the Huygens ING (KNAW), 2016.
#
# This PhDWare code-sketch was part of a pilot exploring the use and usefulness of image data and visual information in
# the digital opening of an archival series, the Resolutions of the States General 1576‒1796.
#
# DiXiT (Digital Scholarly Editions Initial Training Network) has been funded from the People Programme (Marie Curie Actions)
# of the European Union's Seventh Framework Programme FP7/2007-2013/ under REA grant agreement n° 317436.


from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
import codecs
import os
import DocumentImageAnalysis as dia
import DocumentImageUnderstanding as diu
from PIL import Image
import numpy as np
import Levers


class Meeting():
    """
    Holds the currently open meeting, where logical sections can be added according to the flow of the document.
    When the next starting sections is found, this meeting is saved into the XML document.
    """
    def __init__(self):
        self.logicalSectionList = []

    def addLogicalSection(self, e):
        self.logicalSectionList.append(e)

    def getLogicalSectionList(self):
        return self.logicalSectionList


class XMLDocument():
    """
    Holds the textual and structural content extracted from the document images.
    """
    def __init__(self):
        self.document = Element('document')
        self.heldMeeting = Meeting()
        self.heldLogicalSection = None

    def addElement(self, elem, attSet=None, text=None):
        if attSet == None:
            newElement = SubElement(self.document, elem)
        else:
            newElement = SubElement(self.document, elem, attSet)

        if text != None:
            newElement.text = text

    def flush(self):
        if (self.heldLogicalSection != None):
            if (len(self.heldLogicalSection.getSectionList()) >= 1):
                self.heldMeeting.addLogicalSection(self.heldLogicalSection)

        if (len(self.heldMeeting.getLogicalSectionList()) != None):
            if (len(self.heldMeeting.getLogicalSectionList()) >= 1):
                if (len(self.heldMeeting.getLogicalSectionList()[0].getSectionList()) >= 1):
                    self.writeMeeting()
                    self.heldMeeting = None
                    self.heldMeeting = Meeting()
                    self.heldLogicalSection = None


    def saveDocument(self, directory, fileName):
        print ("saveDocument -->")

        #Let's make sure the directory exists
        if not os.path.exists(directory):
            os.makedirs(directory)

        f = codecs.open(directory+fileName, "w", "utf-8")

        f.write(self.getDocumentText())
        f.close()

    def getDocumentText(self):

        rough_string = tostring(self.document, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        pretty = reparsed.toprettyxml(indent="    ", newl="\r\n")
        pretty = pretty.replace("<lb/>\r\n                ", "<lb/>")
        pretty = pretty.replace("</hi>\r\n                    ", "</hi>")
        pretty = pretty.replace("</hi>\r\n                ", "</hi>")
        return pretty


    def insertSection(self, e):
        """
        A function for inserting a new section into the document.
        """

        if (self.heldLogicalSection == None):
            # held == None: before content, or after flush.
            # if just facs, pb, cb no need to wrap them in <ab>

            if(isinstance(e, str)):

                if ("facs " in e):
                    self.addElement("facs", {"src":e.replace("facs ", "")})
                if ("pb " in e):
                    sSplit = e.split("##")
                    self.addElement("pb", {"n":sSplit[0].replace("pb ", ""), "text":sSplit[1]})
                if ("cb " in e):
                    self.addElement("cb", {"n": e.replace("cb ", "")})

                return

            self.heldLogicalSection = diu.LogicalSection(e)
            if(isinstance(e, str)):
                return
            else:
                if (e.getInitialCapital() == None and e.getLayout() == "startingSignature"):
                    self.heldLogicalSection.setIdentity("head")
                    #print ("adding section: no initial capital, (layout centred) has starting signature.")
                    return
            return

        if (isinstance(e, str)):
            self.heldLogicalSection.addSection(e)
            return

        if (e.getInitialCapital() == None and e.getLayout() == "justified"):
            self.heldLogicalSection.addSection(e)
            #print ("adding section: no initial cap, layout is justified.")
            return

        if (e.getInitialCapital() != None and e.getLayout() == "justified"):
            self.heldMeeting.addLogicalSection(self.heldLogicalSection)
            self.heldLogicalSection = diu.LogicalSection(e)
            #print("adding section: initial capital, layout justified.")
            return

        if (e.getInitialCapital() == None and e.getLayout() == "startingSignature"):
            # If the current logical section doesn't already contain a centred section.
            # New meeting:
            self.heldMeeting.addLogicalSection(self.heldLogicalSection)
            self.writeMeeting()
            self.heldMeeting = None
            self.heldMeeting = Meeting()
            self.heldLogicalSection = None
            self.heldLogicalSection = diu.LogicalSection(e)
            self.heldLogicalSection.setIdentity("head")
            #print ("adding section: no initial capital, (layout centred) starting signature located.")
            return


    def writeMeeting(self):
        """
        A function for writing the meeting (i.e. the logical sections it contains) into the XML document.
        """
        #print("writeMeeting ->")

        self.saveMeetingImage()

        logicalSectionList = self.heldMeeting.getLogicalSectionList()

        # Let's attach logical labels.
        if (logicalSectionList[0].getIdentity() == "head"):

            if len(logicalSectionList) > 1:
                logicalSectionList[1].setIdentity("resumption")

            if len(logicalSectionList) > 2:
                for i in range(2, len(logicalSectionList)):
                    logicalSectionList[i].setIdentity("resolution")

        sessionElement = SubElement(self.document, "session")

        for i in range(0, len(logicalSectionList)):
            subContainerList = [SubElement(sessionElement, logicalSectionList[i].getIdentity())]

            physicalSectionList = logicalSectionList[i].getSectionList()

            for j in range(0, len(physicalSectionList)):
                s = physicalSectionList[j]

                if (isinstance(s, str)):

                    if ("facs " in s):
                        SubElement(subContainerList[len(subContainerList)-1], "facs", {"src": s.replace("facs ", "")})

                    if ("pb " in s):
                        sSplit = s.split("##")
                        SubElement(subContainerList[len(subContainerList)-1], "pb", {"n": sSplit[0].replace("pb ", ""), "text":sSplit[1]})

                    if ("cb " in s):
                        SubElement(subContainerList[len(subContainerList)-1], "cb", {"n": s.replace("cb ", "")})

                    continue

                if (len(subContainerList) == 1):
                    subContainerList.append(SubElement(subContainerList[len(subContainerList)-1], "p"))

                #print("logical identity: "+logicalSectionList[i].getIdentity())
                if logicalSectionList[i].getIdentity() == "head":
                    s.processTextContent("head")
                if logicalSectionList[i].getIdentity() == "resolution" or logicalSectionList[i].getIdentity() == "resumption" or logicalSectionList[i].getIdentity() == "ab":
                    s.processTextContent("body")

                textContent = s.getTextContent()

                for t in range(0, len(textContent)):
                    if (t == 0 and s.getInitialCapital() != None):
                        tempLb = SubElement(subContainerList[len(subContainerList)-1], "lb")
                        hi = SubElement(subContainerList[len(subContainerList)-1], "hi")
                        hi.attrib["type"] = "initial"

                        hi.text = s.getInitialTextContent()
                        hi.tail = textContent[t]
                    else:
                        tempLb = SubElement(subContainerList[len(subContainerList)-1], "lb")
                        tempLb.tail = textContent[t]


    def saveMeetingImage(self):
        """
        Saves the extracted column sections belonging to a meeting, possibly running across many pages, into a single
        often long image; a bit like making sausage of the resolutions.
        """
        physSectionList = []

        # Let's get the sections
        logicalSectionList = self.heldMeeting.getLogicalSectionList()
        for i in range(0, len(logicalSectionList)):
            physicalSectionList = logicalSectionList[i].getSectionList()
            for j in range(0, len(physicalSectionList)):
                if (isinstance(physicalSectionList[j], str)):
                    continue
                else:
                    physSectionList.append(physicalSectionList[j])

        if len(physSectionList) == 0:
            return

        #Let's find the dimensions
        length = 0
        width = 0
        for i in range(0, len(physSectionList)):
            tempArea = physSectionList[i].getImageArea()
            i, j = tempArea.shape

            if (width < j):
                width = j+1
            length = length + i + 1 + 2

        im = Image.new("L", (width, length), "white")  # grey -> white
        pixMap = np.array(im)

        offset=0

        for s in range(0, len(physSectionList)):
            tempArea = physSectionList[s].getImageArea()

            for i in range(0, tempArea.shape[0]):
                for j in range(0, tempArea.shape[1]):
                    pixMap[offset][j] = tempArea[i][j]
                offset = offset + 1
            offset = offset + 2

        synthImage = dia.Facsimile(pixMap, Levers.fileName.replace(".jpg","")+"_session")
        synthImage.save(Levers.fileName.replace(".jpg","")+"_session_"+str(Levers.imageIter), "finishedSessions")

