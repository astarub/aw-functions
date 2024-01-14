# -*- coding: utf-8 -*-

#
#   Imports
#

import requests
from os import environ
import xml.etree.ElementTree as ET

from appwrite.id import ID
from appwrite.client import Client
from appwrite.services.databases import Databases

from parseMensaRUBFile import parseMensaRUBFile

#
#   Global Variables
#

BASE_URL         = 'https://asta-bochum.de/akafoe'
AW_DATABASE_ID   = 'data'
AW_COLLECTION_ID = 'mensa'
MENSA_RUB_FILE   = 'Mensa_RUB Küche210.xml'
QWEST_FILE       = 'QWest230.xml'
ROTE_BETE_FILE   = 'Bistro_Cafebar220.xml'

#
#   Functions
#

def main(context):
    """
    Entry point of cloud function.
    """

    #** Download & Parse XML

    # get XML files
    try:
        mensaRubXML = requests.get(f'{BASE_URL}/{MENSA_RUB_FILE}').content
        roteBeteXML = requests.get(f'{BASE_URL}/{QWEST_FILE}').content
        qwestXML = requests.get(f'{BASE_URL}/{ROTE_BETE_FILE}').content
    except Exception as e:
        #context.error(f'Failed to download XML files: {e.message}')
        return None
    #context.log('Downloaded XML files successfully')

    # parse XML
    try:
        mensaRub = ET.fromstring(mensaRubXML)
        roteBete = ET.fromstring(roteBeteXML)
        qwest = ET.fromstring(qwestXML)
    except Exception as e:
        #context.error(f'Failed to parse XML files: {e.message}')
        return None
    #context.log('Parsed XML files successfully')
    
    #** Initialize AW Connection

    # awClient = ( Client()
    #     .set_endpoint('https://api-app.asta-bochum.de/v1')
    #     .set_project(environ['APPWRITE_FUNCTION_PROJECT_ID'])
    #     .set_key(environ['APPWRITE_API_KEY'])
    # )
    # awDB = Databases(awClient)

    #** Parse and Store Data

    parseMensaRUBFile(mensaRub)
    
    
    #context.log('Successfully updated mensa data.')
                

if __name__ == '__main__':
    main('')