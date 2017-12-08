# AnalyseResolutions - HelperFunctions. Tuomo Toljamo (King's College London; DiXiT) at the Huygens ING (KNAW), 2016.
#
# This PhDWare code-sketch was part of a pilot exploring the use and usefulness of image data and visual information in
# the digital opening of an archival series, the Resolutions of the States General 1576‒1796.
#
# DiXiT (Digital Scholarly Editions Initial Training Network) has been funded from the People Programme (Marie Curie Actions)
# of the European Union's Seventh Framework Programme FP7/2007-2013/ under REA grant agreement n° 317436.

from os import listdir
from numpy import array
import codecs
from PIL import Image
import Levers
from time import strftime


class HTMLTestingPage():
    """
    A HTML testing page to render the results of processing per a document spread.
    """

    def __init__(self, fileName, originalFacsimileName):
        self.fileName = fileName
        self.originalFacsimileName = originalFacsimileName
        self.f = self.openFile()
        self.preamble = ["<!DOCTYPE html PUBLIC \"-//W3C//DTD XHTML 1.0 Transitional//EN\" \"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd\">",
                         "<html xmlns=\"http://www.w3.org/1999/xhtml\">",
                         "<head>",
                         "<meta http-equiv=\"Content-Type\" content=\"text/html; charset=utf-8\" />",
                         "<style type=\"text/css\">",
                         "@import url(\"file:///"+Levers.style+"\");",
                         "</style>",
                         "<title>"+self.originalFacsimileName+"</title>",
                         "</head>",
                         "<body>"]

        self.postamble = ["</body>", "</html>"]
        self.addStringList(self.preamble)

    def openFile(self):
        f = codecs.open(self.fileName, "w", "utf-8")
        return f

    def addStringList(self, content):
        for i in range(0, len(content)):
            self.f.write(content[i]+"\n")

    def addString(self, line):
        self.f.write(line+"\n")

    def close(self):
        self.addStringList(self.postamble)
        self.f.close()

    def addOriginal(self, originalFileName):
        content = ["<div class=\"wrapper\">",
                   "<div class=\"bar\">" + originalFileName + "</div>",
                   "<div class=\"centre\">",
                   "<p style=\"text-align:center\">",
                   "<a href=\""+originalFileName+"\" target=\"_blank\">",
                   "<img src=\""+originalFileName+"\" style=\"max-height:100%; width:55%\"/>",
                   "</a>",
                   "</p>",
                   "</div>",
                   "</div>"]
        self.addStringList(content)

    def addColumn(self, columnTitle, columnFileName, columnText):
        contentStart = ["<div class=\"wrapper\">",
                   "<div class=\"bar\">"+columnTitle+"</div>",
                   "<div class=\"left\">",
                   "<a href=\""+columnFileName+"\" target=\"_blank\">",
                   "<img src=\""+columnFileName+"\" style=\"height:100%\"/>",
                   "</a>",
                   "</div>",
                   "<div class=\"right\">"]
        self.addStringList(contentStart)
        for i in range(0, len(columnText)):
            self.addString("<br/>"+columnText[i])

        contentEnd = ["</div>",
                      "</div>"]
        self.addStringList(contentEnd)


class Page():
    """
    Page - Helps to store information processed of a document spread e.g. for generating a HTML testing page.
    """
    def __init__(self):
        self.colTextDictionary = {}
        self.colTextDictionary["0"] = [""]
        self.colTextDictionary["1"] = [""]
        self.colTextDictionary["2"] = [""]
        self.colTextDictionary["3"] = [""]

        nullArray=[]
        self.physSectionDictionary = {}
        self.physSectionDictionary["0"] = [nullArray]
        self.physSectionDictionary["1"] = [nullArray]
        self.physSectionDictionary["2"] = [nullArray]
        self.physSectionDictionary["3"] = [nullArray]

    def addColText(self, n, text):
        self.colTextDictionary[str(n)] = text

    def getColText(self, n):
        return self.colTextDictionary[str(n)]

    def addPhysSections(self, n, secArray):
        self.physSectionDictionary[str(n)] = secArray

    def getPhysSections(self, n):
        return self.physSectionDictionary[str(n)]


def getFiles(dir_in, file_ext):
    """
    Returns a list of file names with a given extension from a given directory.
    """
    file_names = []
    for file in listdir(dir_in):
        if file.endswith(file_ext):
            file_names.append(file)
            
    #print ("Found " + str(len(file_names)) + " files.")
    return file_names


def loadImage(dir_in, file_name):
    """
    Loads an image and returns it as an array.
    """
    img = array(Image.open(dir_in + file_name))
    #img = img.convert('RGB')
    return img


def nbimage( data, vmin = None, vmax = None, vsym = False, saveas = None ):
    """
    (From https://balle.io/blog/134)
    Display raw data as a notebook inline image.

    Parameters:
    data: array-like object, two or three dimensions. If three dimensional,
          first or last dimension must have length 3 or 4 and will be
          interpreted as color (RGB or RGBA).
    vmin, vmax, vsym: refer to rerange()
    saveas: Save image file to disk (optional). Proper file name extension
            will be appended to the pathname given. [ None ]
    """
    from IPython.display import display, Image
    from PIL.Image import fromarray
    from io import StringIO, BytesIO
    data = rerange( data, vmin, vmax, vsym )
    data = data.squeeze()
    # try to be smart
    if data.ndim == 3 and 3 <= data.shape[ 0 ] <= 4:
        data = data.transpose( ( 1, 2, 0 ) )
    s = BytesIO()
    fromarray( data ).save( s, 'png' )
    if saveas is not None:
        open( saveas + '.png', 'wb' ).write( s )
    display( Image( s.getvalue() ) )
    
    
def rerange( data, vmin = None, vmax = None, vsym = False ):
    """
    (From https://balle.io/blog/134)
    Rescale values of data array to fit the range 0 ... 255 and convert to uint8.

    Parameters:
    data: array-like object. if data.dtype == uint8, no scaling will occur.
    vmin: original array value that will map to 0 in the output. [ data.min() ]
    vmax: original array value that will map to 255 in the output. [ data.max() ]
    vsym: ensure that 0 will map to gray (if True, may override either vmin or vmax
          to accommodate all values.) [ False ]
    """
    from numpy import asarray, uint8, clip
    data = asarray( data )
    if data.dtype != uint8:
        if vmin is None:
            vmin = data.min()
        if vmax is None:
            vmax = data.max()
        if vsym:
            vmax = max( abs( vmin ), abs( vmax ) )
            vmin = -vmax
        data = ( data - vmin ) * ( 256 / ( vmax - vmin ) )
        data = clip( data, 0, 255 ).astype( uint8 )
    return data


def normaliseList(l):
    """
    Normalises a list according to its max value to a range of [0,100].
    """
    maxL = max(l)*1.0
    if maxL != 0:
        for n in range(0, len(l)):
            l[n] = int((l[n]/maxL)*100)
    return l


def readTextFile(fileName):
    """
    Reads a text file as UTF-8, returns the lines of content in a list.
    :param fileName:
    :return:
    """

    content = []
    infile = codecs.open(fileName, "r", "utf-8")
    next = infile.readline()
    content.append(next)
    while next != "":
        #print(next)
        next = infile.readline()
        content.append(next)

    infile.close()
    return content


def debug(msg):
    """
    Saves debug print to a file. (Very much underused at the moment.)
    :param msg:
    :return:
    """

    logFile = open(Levers.dir_out+'log.txt', 'a')

    try:
        outString = "\r\n"
        outString = outString + strftime("%d/%m/%Y") + " " + strftime("%H:%M:%S") + ": "
        outString = outString + msg
        logFile.write(outString)

    finally:
        logFile.close()

