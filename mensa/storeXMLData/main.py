# -*- coding: utf-8 -*-

#
#   Imports
#

import requests
from os import environ
import xml.etree.ElementTree as ET

from appwrite.client import Client
from appwrite.services.databases import Databases
from appwrite.query import Query

from parseAndStoreXML import parseAndStoreXML

#
#   Global Variables
#

BASE_URL       = environ['BASE_URL']
MENSA_RUB_FILE = environ['MENSA_RUB_FILE']
QWEST_FILE     = environ['QWEST_FILE']
ROTE_BETE_FILE = environ['ROTE_BETE_FILE']

AW_DATABASE_ID   = environ['AW_DATABASE_ID']
AW_COLLECTION_ID = environ['AW_COLLECTION_ID']

#
#   Functions
#

def main(context):
    """
    Entry point of cloud function.
    """

    # local variable that ensure garbage collection on 
    # error in parsing XML file to dishes
    UPDATE_DATA_FAILED = False

    #** Download & Parse XML

    # get XML files
    try:
        mensaRubXML = requests.get(f'{BASE_URL}/{MENSA_RUB_FILE}').content
        roteBeteXML = requests.get(f'{BASE_URL}/{ROTE_BETE_FILE}').content
        qwestXML = requests.get(f'{BASE_URL}/{QWEST_FILE}').content
    except Exception as e:
        print(f'[-] Failed to download XML files: {e}')
        return None
    print('[#] Downloaded XML files successfully')

    # parse XML
    try:
        mensaRub = ET.fromstring(mensaRubXML)
        roteBete = ET.fromstring(roteBeteXML)
        qwest = ET.fromstring(qwestXML)
    except Exception as e:
        print(f'[-] Failed to parse XML files: {e}')
        return None
    print('[#] Parsed XML files successfully')
    
    #** Initialize AW Connection

    awClient = ( Client()
        .set_endpoint(environ['AW_ENDPOINT'])
        .set_project(environ['AW_PROJECT_ID'])
        .set_key(environ['AW_API_KEY'])
    )
    awDB = Databases(awClient)

    #** Store current list of dishes

    # This is used in garbage collection later. Limit is set to 5000 to ensure
    # downloading the full collection. In production, there should be ~1000 dishes in total.
    oldCollection = awDB.list_documents(AW_DATABASE_ID, AW_COLLECTION_ID, [Query.limit(5000)])
    print(f'[#] Current collection has {oldCollection["total"]} dishes.')

    #** Parse and Store Data

    try:
        parseAndStoreXML(mensaRub, 'mensa_rub', awDB, #context
                         )
        print('[#] Successfully updated mensa data.')
    except Exception as e:
        UPDATE_DATA_FAILED |= True
        print(f'[-] Failed updated mensa data: {e}')
        
    try:
        if not UPDATE_DATA_FAILED: 
            parseAndStoreXML(roteBete, 'rote_bete', awDB, #context
                         )
            print('[#] Successfully updated rote bete data.')
    except Exception as e:
        UPDATE_DATA_FAILED |= True
        print(f'[-] Failed updated rote bete data: {e}')
        
    try:
        if not UPDATE_DATA_FAILED: 
            parseAndStoreXML(qwest, 'qwest', awDB, #context
                         )
            print('[#] Successfully updated Q-West data.')
    except Exception as e:
        UPDATE_DATA_FAILED |= True
        print(f'[-] Failed updated Q-West data: {e}')
        
    if not UPDATE_DATA_FAILED: 
        print('[+] Successfully updated all mensa data.')

    #** Garbage collection
    
    if UPDATE_DATA_FAILED:
        try:
            # Delete new entries / entries that are created while failing
            newCollection = awDB.list_documents(AW_DATABASE_ID, AW_COLLECTION_ID, [Query.limit(5000)])
            toDelete = set(newCollection['documents']).difference(oldCollection['documents'])
            for dish in toDelete:
                awDB.delete_document(AW_DATABASE_ID, AW_COLLECTION_ID, dish.id)
            print('[+] Garbage collection succesfully.')
        except Exception as e:
            print(f'[-] Failed to delete created dishes while failing to update: {e}')
    else:
        try:
            print(f'[#] Try to delete {oldCollection["total"]} garbage dishes.')
            # This can take very long depending on garbage count. Should not be more 
            # than ~1000 dishes per run in production. Use with caution while developing!
            for dish in oldCollection['documents']:
                awDB.delete_document(AW_DATABASE_ID, AW_COLLECTION_ID, dish['$id'])
            print('[+] Garbage collection succesfully.')
            newCollection = awDB.list_documents(AW_DATABASE_ID, AW_COLLECTION_ID, [Query.limit(1)])
            print(f'[#] Current collection has {newCollection["total"]} dishes.')
        except Exception as e:
            print(f'[-] Garbage collection failed {e}')

if __name__ == "__main__":
    main('')