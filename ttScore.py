from pymarc import MARCReader


'''
This is a simplified and slightly modified version of the scoring algorithm described in this article:

Thompson, Kelly, and Stacie Traill. “Leveraging Python to Improve Ebook Metadata Selection,
Ingest, and Management.” The Code4Lib Journal, no. 38 (October 18, 2017). http://journal.code4lib.org/articles/12828.

'''

def getRecordScore(record):

    score = {
                "ISBN":0 ,
                "Authors":0 ,
                "AlternativeTitles":0 ,
                "Edition":0 ,
                "Contributors":0,
                "Series": 0,
                "TOC": 0,
                "Date008":0,
                "Date26X":0,
                "Class":0,
                "LoC":0,
                "FAST":0,
                "Online": 0,
                "LanguageOfResource":0,
                "CountryOfPublication":0,
                "languageOfCataloguing":0,
                "RDA":0,
                "ProviderNeutral":0,
                "DashInClass":0,
                "AllCaps":0,
                "OCLC":0,
                "total":0
                }

    #ISBN
    for f in record.get_fields('020'):
        score['ISBN'] += 1

    #Authors
    for f in record.get_fields('100','110','111'):
        score['Authors'] += 1

    #alternative titles
    for f in record.get_fields('246'):
        score['AlternativeTitles'] += 1

    #edition
    for f in record.get_fields('250'):
        score['Edition'] += 1

    #contributors
    for f in record.get_fields('700','710','711','720'):
        score['Contributors'] += 1

    #series
    for f in record.get_fields('440','490','800','810','830'):
        score['Series'] += 1

    #TOC
    TOC = record.get_fields('505')
    ContentsNote = record.get_fields('520')

    if len(TOC) > 0:
        score['TOC'] += 1
    if len(ContentsNote) > 0:
        score['TOC'] +=1
    

    #Online, LanguageOfResource,Date008
    for f in record.get_fields('008'):
        if f.value()[23] == "o":
            score['Online'] += 1
            
        if f.value()[35:38] in ['eng']:
            score['LanguageOfResource'] += 1
        if f.value()[15:18] not in ['xx ']:
            score['CountryOfPublication'] += 1
        date008 = f.value()[7:11]
        if date008[0] in ["1","2"] and len(date008) == 4:
            score['Date008'] += 1
    
    '''    
    for f in record.get_fields('300'):
        if f.value().find("online resource") != -1:
            score['Online'] += 1
    '''
           

    #date26X
    
    for f in record.get_fields('260','264'):
        for s in f:
            date26X=f.get_subfields("c")
            if len(date26X)>0:
                    cleanDate26X=""
                    for letter in date26X[0]:
                        if letter.isdigit():
                            cleanDate26X +=  letter
                    if len(cleanDate26X) == 4:
                        if cleanDate26X[0] in ["1","2"]:
                            score['Date26X'] += 1
                    if cleanDate26X == date008:
                        score['Date26X'] += 1
                    break

    #Class
    if len(record.get_fields('050','055','060','086','099')) > 0:
        score['Class'] += 1
    for f in record.get_fields('050','055','060','086','099'):
        if f.value().find("-") != -1:
            score['DashInClass'] += -1
        

    #LoC, FAST
    for f in record.get_fields('600','610','611','630','650','651','653'):
        if f.indicators[1] == "0" and f.get_subfields("a")[0].find("Electronic books") == -1:
            score['LoC'] += 1
        elif f.indicators[1] == "7" and f.get_subfields('2')[0] == "fast" and f.get_subfields("a")[0].find("Electronic books") == -1:
            score['FAST'] += 1
    if score['LoC'] > 10:
        score['LoC'] = 10
    if score['FAST'] > 10:
        score['FAST'] = 10

    #ignore FAST headings. Comment out to include.
    score['FAST'] = 0
  

    #LanguageOfCataloging, RDA
    for f in record.get_fields('040'):
        if len(f.get_subfields('b')) > 0:

            if f.get_subfields('b')[0] in ['eng']:
                score['languageOfCataloguing'] += 1
        if len(f.get_subfields('e')) > 0:
            for s in f.get_subfields('e'):
                if s == "rda":
                    score['RDA'] += 1
                #if s == "pn":
                #    score['ProviderNeutral'] += -1
    
    #AllCaps
    for f in record.get_fields('100','245'):
         if any(c.islower() for c in f.value()) is False:
             score['AllCaps'] += -1
    

    #calculate total score for record
    total = 0
    for key, value in score.items():
        total = total + value
    score['total'] = total
    
    #get id from marc 001 field
    score['id'] = record['001'].value()

    return score










                

           
                

                
                        




    
        
            
                
        
        

        
