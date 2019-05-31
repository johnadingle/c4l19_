import oclc_auth #oclc authorization functions
import ttScore #Thompson-Traill score calculation

import os
import sys
import time

from pymarc import MARCReader
from difflib import SequenceMatcher
import xml.etree.ElementTree as ET
import io
from pymarc import parse_xml_to_array

import re

OCLCregex = re.compile(r"\(OCoLC\) *(ocm|on|ocn|OCM|OCN|ON|ocl7)*0*")

###Various functions for comparing records
        
def checkEbook(record):

    '''
    takes a pymarc record, checks to see if it is electronic
    '''

    if record.get_fields('007'):
        if record['007'].value()[0] == "c" and record.get_fields("856"):
            return "ebook"
    else:
        return "not an ebook"


def checkBRX(record):

    '''
    takes a pymarc record, checks to see if it is BRX-catalogued
    '''

    if record.get_fields('040'):
        if record['040']['a'] == "BRX":
            return "BRX"
        else:
            return "OTHER"
    else:
        return "OTHER"

    
def processOCLCRecord(oclcNumber):

    root = ET.fromstring(oclc_auth.readFromMetadataAPI(str(oclcNumber),'marc'))

    string = ET.tostring(root).decode()

    records = parse_xml_to_array(io.StringIO(string))

    record = records[0]    

    return record


def normalizeOCLC(OCLCregex, oclc035field):

    return re.sub(OCLCregex,"(OCoLC)",oclc035field)

    

def similar(a, b):
    # Checks how similar two strings are, returns a ratio
    return SequenceMatcher(None, a, b).ratio()

def cleanDate(date):
    # Cleans date coming from 008 field
    
    output = ""
    if date != None:
        for char in date:
            if char in ["1","2","3","4","5","6","7","8","9","0"]:
                output += char
        if len(output) == 4:
            return int(output)
        
    return None


def checkSubjectHeadings(localRecord, oclcRecord):

    oclcRecordSubjects = []
    missingSubjects = []

    for f in oclcRecord.subjects():
        oclcRecordSubjects.append(f.value())

    for f in localRecord.subjects():
        if f.value() not in oclcRecordSubjects:
            missingSubjects.append(f)

    return missingSubjects

def checkIdentifiers(localRecord, oclcRecord):

    oclcRecordIdentifiers = []
    localRecordIdentifiers = []

    if oclcRecord.get_fields('020'):
        for f in oclcRecord.get_fields('020'):
            for sf in f.get_subfields('a','z'):
                oclcRecordIdentifiers.append(sf)
    if localRecord.get_fields('020'):
        for f in localRecord.get_fields('020'):
            for sf in f.get_subfields('a','z'):
                localRecordIdentifiers.append(sf)
    matches = set(localRecordIdentifiers) & set(oclcRecordIdentifiers)

    print("OCLC ISBNs: " + ", ".join(oclcRecordIdentifiers))
    print("Local ISBNs: " + ", ".join(localRecordIdentifiers))

    if matches:
        return "ISBN Match: " + ", ".join(matches)
        
    else:
        return "No matches"


    return None
            
            


# tallies number of records flagged for investigate
tally = 0
bibsToInvestigate = []
problems = []
totalLocal = 0
totalOCLC = 0



if __name__ == "__main__":
    #print("Resolving..." + "\n")
    for f in os.listdir(os.getcwd()):
        if f[-3:] == "mrc":
            infile = f
            break
    try:
        infile

    except:
        print("No file found")
        sys.exit()

    #starts going through provided .mrc file
    with open(infile, 'rb') as fh:
        reader = MARCReader(fh)
        for record in reader:
                print("")
                time.sleep(3)
                
                issue = False
                
                #Get OCLC number from record 
                try:
                    oclcNum = record['035']['a'].replace('(OCoLC)',"")
                    print("OCLC Number: " + str(oclcNum))
                except:
                    continue

                tally += 1

                #Get matching WorldCat Record
                oclcRecord = processOCLCRecord(oclcNum)

                #check to make sure Metadata API returned something, if not log bib to investigate 
                if oclcRecord == None:
                    problems.append(record['001'].value())
                    continue

                #Get TT scores and add to running totals
                oclcScore = ttScore.getRecordScore(oclcRecord)['total']
                localScore = ttScore.getRecordScore(record)['total']

                totalOCLC += oclcScore
                totalLocal += localScore


                #Compare record elements for differences
                title = record.title().lower()
                oclcTitle = oclcRecord.title().lower()
                pubyear = record['008'].value()[7:11]
                ###if record['008'].value()[6] == "p" #### finish this, need to check for reprint date
                oclcPubYear = oclcRecord['008'].value()[7:11]

                #print(title)
                #print(oclcTitle)

                print(checkIdentifiers(record, oclcRecord))
                
                # checks to see if there are any issues with the match

                titleDifference = similar(title, oclcTitle)
                #print(titleDifference)
                #print(cleanDate(pubyear), cleanDate(oclcPubYear))
                #print("")
                
                #compare publication years. If difference is greater than 1, flag as a problem
                if cleanDate(pubyear) != None and cleanDate(oclcPubYear) != None:
                    if abs(cleanDate(pubyear) - cleanDate(oclcPubYear)) > 1:
                        problems.append(record['001'].value())
                        print("Problem Flagged")

                        #print("")
                        print("From OCLC")
                        print("Title: " + oclcTitle)
                        print("Date: " + oclcPubYear)
                        print("")
                        print("Original")
                        print("Title: " + title)
                        print("Date:" + pubyear)
                
                #compare title difference. Flag for follow up if different.
                if titleDifference < 0.7:
                    print("To Investigate")
                    bibsToInvestigate.append({record['001'].value():{'title': title, 'date': pubyear, 'OclcTitle':oclcTitle, 'OclcDate':oclcPubYear}})
                    #print("")
                    print("From OCLC")
                    print("Title: " + oclcTitle)
                    print("Date: " + oclcPubYear)
                    print("")
                    print("Original")
                    print("Title: " + title)
                    print("Date:" + pubyear)
                #print(tally)

                if tally % 50 == 0:
                    print(totalOCLC / tally)
                    print(totalLocal / tally)

    
    # list any problematic records to follow up
    for bib in bibsToInvestigate:
        for k,v in bib.items():
            print(k)
            for key, value in v.items():
                print(key)
                print(value)
            print("")
            toInvestigate = input("Flag this as an issue? (y/n) ")
            if toInvestigate == "y":
                problems.append(k)
            else:
                continue
            
            
    problems = list(sorted(set(problems)))
    print(len(problems))
    print(tally)

    for bib in problems:
        print(bib)






    
					







