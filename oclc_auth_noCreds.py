import requests
import six
import hashlib
import hmac
import time
import base64

### Details for WorldCat APIs
client_id = ""
client_secret = ""
grant_type=""
authenticatingInstitutionId=""
contextInstitutionId=""
scope=""
authorization_base_url = ""
principalID = ""
principalIDNS = ""


def getAccessToken():

    '''
    gets an access token for the WorldCat Metadata API
    '''
    
    q='"'
    qc='"'

    urlParameters = ("grant_type="+ grant_type +
            "&authenticatingInstitutionId=" + authenticatingInstitutionId +
            "&contextInstitutionId=" + contextInstitutionId +
            "&scope=" + scope)

    parameters = {}
    for param in urlParameters.split('&'):
        key = (param.split('='))[0]
        value = (param.split('='))[1]
        parameters[key] = value

    authRequestURL = (authorization_base_url + "?" + urlParameters)

    currentTime = str(int(time.time()))
    nonceTime = str(int(time.time()- 1))
    stringToHash = (client_id + "\n" +
                    currentTime + "\n" +
                    nonceTime + "\n" +
                    "" + "\n" +
                    "POST" + "\n" +
                    "www.oclc.org" "\n" +
                    "443" + "\n" +
                    "/wskey" + "\n")

    """URL encode normalized request per OAuth 2 Official Specification."""
    #This part taken from oclc-python-auth library
    
    for key in sorted(parameters):
        nameAndValue = six.moves.urllib.parse.urlencode({key: parameters[key]})
        nameAndValue = nameAndValue.replace('+', '%20')
        nameAndValue = nameAndValue.replace('*', '%2A')
        nameAndValue = nameAndValue.replace('%7E', '~')
        stringToHash += nameAndValue + '\n'

    digest = hmac.new(client_secret.encode('utf-8'),
                  msg = stringToHash.encode('utf-8'),
                  digestmod=hashlib.sha256).digest()

    signature = str(base64.b64encode(digest).decode())

    ###

    authorization = ("http://www.worldcat.org/wskey/v2/hmac/v1" + " " +
               'clientId=' + q + client_id + qc + "," +
               'timestamp='+ q + currentTime + qc + "," +
               'nonce=' + q + nonceTime + qc + "," +
               'signature=' + q + signature + qc + "," +
               'principalID=' + q + principalID + qc + "," +
               'principalIDNS=' + q + principalIDNS + qc)

    headers = {'Authorization': authorization}
    r = requests.post(authRequestURL, headers=headers)
    response = r.json()
    accessToken = response['access_token']
    
    return accessToken

authorizationToken = getAccessToken()


def readFromMetadataAPI(oclcNumber, recordType):

    '''
    given an oclc number, gets the record from WorldCat Metadata API and extracts needed fields. Requires a generated client credential token.
    '''
    
    global authorizationToken #needed to update global token variable if need to refresh


    if recordType == 'marc':
        acceptHeader = 'application/atom+xml;content="application/vnd.oclc.marc21+xml"'
    elif recordType == 'cdf':
        acceptHeader = 'application/atom+xml;content="application/vnd.oclc.cdf"'
    else:
        return None
    
    recordURL= "https://worldcat.org/bib/data/" + oclcNumber
    headers = {
            'Authorization': "Bearer " + authorizationToken,
            'accept':acceptHeader
    }

    r= requests.get(recordURL, headers=headers)

    if r.status_code == 401:
       
        authorizationToken = getAccessToken()
        print("had to get new token")
        headers = {
            'Authorization': "Bearer " + authorizationToken,
            'accept':acceptHeader
            }
        r= requests.get(recordURL, headers=headers)

        
    if r.status_code == 200:
        return r.text
    else:
        print(r.text)
        return None


