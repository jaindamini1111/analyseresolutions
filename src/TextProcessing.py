# AnalyseResolutions - TextProcessing. Tuomo Toljamo (King's College London; DiXiT) at the Huygens ING (KNAW), 2016.
#
# This PhDWare code-sketch was part of a pilot exploring the use and usefulness of image data and visual information in
# the digital opening of an archival series, the Resolutions of the States General 1576‒1796.
#
# DiXiT (Digital Scholarly Editions Initial Training Network) has been funded from the People Programme (Marie Curie Actions)
# of the European Union's Seventh Framework Programme FP7/2007-2013/ under REA grant agreement n° 317436.
#
# TextProcessing.py.
# A haphazard collection of normalisations operations trialled with the generated OCR text;
# proper post-processing routines could be installed here later.

import re
import Levers


def processHeadText(textArrayIn):
    """
    Performs few simple text normalisation operations on text recurring in head sections.
    :param textArrayIn:
    :return:
    """
    #print("processHeadText ->")
    for i in range(0, len(textArrayIn)):

        textArrayIn[i] = normalisePunctuation(textArrayIn[i])

        if (textArrayIn[i] != "PRAESIDE,"):
            textArrayIn[i],v = tryStringFit(textArrayIn[i], "PRAESENTIBUS,", 12, 25, 8)

        if (textArrayIn[i] != "PRAESENTIBUS,"):
            if (textArrayIn[i].find("B") == -1 or textArrayIn[i].find("U") == -1):
                textArrayIn[i],v = tryStringFit(textArrayIn[i], "PRAESIDE,", 7, 20, 6)

        if (textArrayIn[i] == "PRAESIDE," and i >= 2):
            textArrayIn[i-2] = normaliseDate(textArrayIn[i-2])

        #textArrayIn[i],v = tryStringFit(textArrayIn[i], "1740.", 4, 7, 2)
            textArrayIn[i],v = tryStringFit(textArrayIn[i], Levers.target_year, 4, 7, 2)

    return textArrayIn


def processDatelineText(contentList):
    """ OCR post-processing by normalisation.
    :param contentList:
    :return:
    """
    #print("processDatelineText ->")
    for j in range(0, len(contentList)):
        contentList[j] = fitWordsDateline(contentList[j])

    return contentList


def fitWordsDateline(contentString):
    #print (contentString)
    # word, min len, max len, min hits, stop-letters.

    tobeFitted = [("Den", 3, 4, 2),
                  ("January", 6, 10, 5),
                  ("February", 6, 9, 6),
                  ("Maart", 4, 7, 4),
                  ("April", 3, 7, 3),
                  ("Mey", 2, 4, 1, "DnJu"),
                  ("Juny", 4, 6, 4),
                  ("July", 4, 6, 4),
                  ("Augusty", 4, 9, 4),
                  ("September", 6, 11, 6, "ND"),
                  ("October", 5, 9, 5),
                  ("November", 6, 10, 5, "DS"),
                  ("December", 6, 10, 6, "NS")]

    components = contentString.split(" ")

    for i in range(0, len(components)):
        for j in range(0, len(tobeFitted)):

            continueFlag = False
            if len(tobeFitted[j]) == 5:

                for k in range(0, len(tobeFitted[j][4])):
                    if (tobeFitted[j][4][k] in components[i]):
                        continueFlag = True

            if continueFlag:
                continue

            if len(components[i]) < len(tobeFitted[j][0])-1 or len(components[i]) > len(tobeFitted[j][0])+1:
                continue

            if components[i] != tobeFitted[j][0]:
                replacer, value = tryStringFit(components[i], tobeFitted[j][0], tobeFitted[j][1], tobeFitted[j][2], tobeFitted[j][3])
                if (value):
                    contentString = contentString.replace(components[i], replacer)

    return contentString


def normaliseDate(dateString):
    """

    :param dateString:
    :return:
    """
    # decompose by splitting
    components = dateString.split(" ")
    days = False
    den = False
    months = False

    for i in range(0, len(components)):
        if days == False:
            components[i],v = fitDays(components[i])
            if v == True:
                days = True
                continue
        if den == False:
            components[i],v = tryStringFit(components[i], "den", 3, 4, 2)
            if v == True:
                den = True
                continue
        if months == False:
            components[i],v = fitMonths(components[i])
            if v == True:
                months = True
                continue

    # recompose
    recomposed = ""
    for i in range(0, len(components)):
        if (i != 0):
            recomposed = recomposed + " "
        recomposed = recomposed + components[i]

    return recomposed


def fitDays(stringIn):
    """

    :param stringIn:
    :return:
    """
    stringIn,v = tryStringFit(stringIn, "Veneris", 6, 9, 5)
    if v == True:
        return stringIn, v
    stringIn,v = tryStringFit(stringIn, "Sabbathi", 7, 10, 5)
    if v == True:
        return stringIn, v
    stringIn,v = tryStringFit(stringIn, "Dominica",8, 10, 5)
    if v == True:
        return stringIn, v
    stringIn,v = tryStringFit(stringIn, "Lunae", 4, 6, 3)
    if v == True:
        return stringIn, v
    stringIn,v = tryStringFit(stringIn, "Martis",4, 9, 5)
    if v == True:
        return stringIn, v
    stringIn,v = tryStringFit(stringIn, "Mercurii", 6, 10, 6)
    if v == True:
        return stringIn, v
    stringIn,v = tryStringFit(stringIn, "Jovis", 4,7, 3)

    return stringIn,v


def fitMonths(stringIn):
    """

    :param stringIn:
    :return:
    """
    stringIn,v = tryStringFit(stringIn, "January", 6, 9, 5)
    if v == True:
        return stringIn, v
    stringIn,v = tryStringFit(stringIn, "February", 6, 10, 5)
    if v == True:
        return stringIn, v
    if (stringIn != "Martis"):
        stringIn,v = tryStringFit(stringIn, "Maart", 4, 7, 4)
        if v == True:
            return stringIn, v
    stringIn,v = tryStringFit(stringIn, "April", 3,7, 3)
    if v == True:
        return stringIn, v
    stringIn,v = tryStringFit(stringIn, "Mey", 2, 4, 2)
    if v == True:
        return stringIn, v
    stringIn,v = tryStringFit(stringIn, "Juny", 4, 6, 4)
    if v == True:
        return stringIn, v
    stringIn,v = tryStringFit(stringIn, "July",4, 6, 4)
    if v == True:
        return stringIn, v
    stringIn,v = tryStringFit(stringIn, "Augusty", 4,9, 4)
    if v == True:
        return stringIn, v
    stringIn,v = tryStringFit(stringIn, "September",6, 11, 7)
    if v == True:
        return stringIn, v
    if (stringIn.find("N") == -1):
        stringIn,v = tryStringFit(stringIn, "October",5, 9, 5)
        if v == True:
            return stringIn, v
    stringIn,v = tryStringFit(stringIn, "November",6, 10, 6)
    if v == True:
        return stringIn, v
    stringIn,v = tryStringFit(stringIn, "December",6, 10, 7)

    return stringIn,v


def tryStringFit(baseStringIn, testStringIn, minLen, maxLen, minHits):
    """

    :param baseStringIn:
    :param testStringIn:
    :param minLen:
    :param maxLen:
    :param minHits:
    :return:
    """
    if len(baseStringIn) > maxLen:
        #print("false")
        return baseStringIn, False
    if len(baseStringIn) < minLen:
        #print("false")
        return baseStringIn, False

    for i in range(0, len(testStringIn)-minHits+1):
        testSubString = testStringIn[i:]
        hits = 0

        kmin = 0
        for j in range(0, len(testSubString)):

            for k in range(kmin, len(baseStringIn)):

                if (testSubString[j] == baseStringIn[k]):
                    hits = hits + 1
                    if (hits >= minHits):
                        #print("true")
                        #print("Replacing: " + baseStringIn + " with " + testStringIn)
                        return testStringIn, True
                    kmin = k
                    break

    return baseStringIn, False


def normalisePunctuation(stringIn):
    """

    :param stringIn:
    :return:
    """

    stringIn = stringIn.replace("‚", ",")
    stringIn = stringIn.replace(" , ", ", ")
    stringIn = stringIn.replace(" . ", ". ")
    stringIn = stringIn.replace(" : ", ": ")
    stringIn = stringIn.replace(" ; ", "; ")

    if (stringIn[ len(stringIn)-1] == "—"):
        stringIn = stringIn[0:len(stringIn)-1] + "-"

    if (stringIn[ 0 ] == "{"):
        stringIn = "s" + stringIn[1:]

    return stringIn


def processInitalText(textStringIn):
    """ Normalises possible faulty results of OCR on the large initial capitals.
    :param textStringIn:
    :return:
    """
    textStringIn = textStringIn.replace("1", "I")
    textStringIn = textStringIn.replace("l", "I")
    textStringIn = textStringIn.replace("|", "I")
    textStringIn = textStringIn.replace("]", "I")
    textStringIn = textStringIn.replace("[", "I")
    textStringIn = textStringIn.replace("Ë", "I")
    textStringIn = textStringIn.replace("0", "O")
    textStringIn = textStringIn.replace("o", "O")
    textStringIn = textStringIn.replace("€", "O")
    textStringIn = textStringIn.replace("Û", "O")
    textStringIn = textStringIn.replace("Ü", "O")
    textStringIn = textStringIn.replace("8", "B")

    return textStringIn


def processBodyText(contentList):
    """ OCR post-processing.
    :param contentList:
    :return:
    """
    # line-based actions
    for j in range(0, len(contentList)):
        contentList[j] = normalisePunctuation(contentList[j])
        contentList[j] = fitWords(contentList[j])
        contentList[j] = re.sub("W\W*A\W*A\W*R", "WAAR", contentList[j])
        contentList[j] = re.sub("-\W*WAAR", ". WAAR", contentList[j])
        contentList[j] = contentList[j].replace("suppliant", "Suppliant")
        contentList[j] = contentList[j].replace("staaten", "Staaten")
        contentList[j] = contentList[j].replace("Van", "van")
        contentList[j] = contentList[j].replace("- ", ". ")
        contentList[j] = contentList[j].replace(" ,s ", " 's ")
        contentList[j] = contentList[j].replace(" ,s-", " 's-")
        contentList[j] = contentList[j].replace(" ,t ", " 't ")
        contentList[j] = contentList[j].replace(" Miffive ", " Missive ")


        if contentList[j][ len(contentList[j])-1 ] == "j":
            contentList[j] = contentList[j][:-1] + ","

    # last line of splice
    line = contentList[len(contentList)-1]
    if line[len(line)-1] == "-" and len(line) < 32:
        rev = contentList[len(contentList)-1][::-1]
        rev = rev.replace("-", ".", 1)
        contentList[len(contentList)-1] = rev[::-1]

        # case normalisation
        contentList = normaliseCase(contentList)
        contentList = removeNumbersFromMiddle(contentList)

    return contentList


def removeNumbersFromMiddle(contentList):
    """

    :param contentList:
    :return:
    """
    # find this; replace to this if alpha before; to this is alpha after (but not before).
    toRemove = [("0", "o", "O"), ("1", "l", "I")]
    for i in range(0, len(contentList)):
        #text = "0th"
        for j in range(0, len(toRemove)):

            if toRemove[j][0] in contentList[i]:
                location = contentList[i].find(toRemove[j][0])
                if location > 1:
                    if contentList[i][location-1].isalpha():
                        contentList[i] = contentList[i][0:location]+toRemove[j][1]+contentList[i][location+1:]
                        continue
                if location < len(contentList[i])-2:
                    if contentList[i][location+1].isalpha():
                        contentList[i] = toRemove[j][2]+contentList[i][1:]

    # also remove 'I' if lower-case alpha on both sides.
    return contentList


def normaliseCase(contentList):
    """

    :param contentList:
    :return:
    """

    wordsToLower = ["Zal", "Zyn", "Zynde", "Op", "Om", "Zelve", "Zelver", "Zullen", "Wel", "Werden"]

    # lower the above words, if they are not preceded by a full-stop or a beginning of the line.
    # i.e. there must be an alphabet before them

    for i in range(0, len(wordsToLower)):

        for j in range(0, len(contentList)):

            index = contentList[j].find(wordsToLower[i])
            if (index != -1):

                # find an alphabet before

                found = False
                for k in range(index-1, 0, -1):
                    if contentList[j][k] == ".":
                        found=False
                        break
                    if contentList[j][k].isalpha():
                        found=True
                        break

                if found:
                    if index+len(wordsToLower[i]) < len(contentList[j]):
                        if (contentList[j][index+len(wordsToLower[i])].isalpha() == False):
                            print(contentList[j])
                            contentList[j] = contentList[j][0:index] + wordsToLower[i].lower()+ contentList[j][index+len(wordsToLower[i]):]
                            print(contentList[j])
                    else:
                        print(contentList[j])
                        contentList[j] = contentList[j][0:index] + wordsToLower[i].lower()+ contentList[j][index+len(wordsToLower[i]):]
                        print(contentList[j])

    return contentList


def fitWords(contentString):
    """

    :param contentString:
    :return:
    """
    # word, min len, max len, min hits, stop-letters.
    tobeFitted = [("Missive", 7, 7, 6), ("Depesches", 9, 9, 8), ("Ntfangen", 8, 8, 6), ("sijne", 5, 5, 4),
                  ("voorschreeve", 10, 13, 10), ("Resident", 8, 8, 7), ("Resolutie", 9, 9, 8, "r"), ("sijn", 4, 4, 3)]
    testString = contentString.replace(".", "").replace(",", "").replace(":", "").replace(";", "").replace("-", "")
    components = testString.split(" ")

    for i in range(0, len(components)):
        for j in range(0, len(tobeFitted)):

            continueFlag = False
            if len(tobeFitted[j]) == 5:

                for k in range(0, len(tobeFitted[j][4])):
                    if (tobeFitted[j][4][k] in components[i]):
                        continueFlag = True


            if continueFlag:
                continue

            if len(components[i]) < len(tobeFitted[j][0])-1 or len(components[i]) > len(tobeFitted[j][0])+1:
                continue

            if components[i] != tobeFitted[j][0]:
                replacer, value = tryStringFit(components[i], tobeFitted[j][0], tobeFitted[j][1], tobeFitted[j][2], tobeFitted[j][3])
                if (value):
                    contentString = contentString.replace(components[i], replacer)

    return contentString

