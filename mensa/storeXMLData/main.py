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

BASE_URL       = environ['BASE_URL']            # https://asta-bochum.de/akafoe
MENSA_RUB_FILE = environ['MENSA_RUB_FILE']      # Mensa_RUB%20K%C3%BCche210.xml
QWEST_FILE     = environ['QWEST_FILE']          # QWest230.xml
ROTE_BETE_FILE = environ['ROTE_BETE_FILE']      # Bistro_Cafebar220.xml
BOCHOLT_MENSA  = environ['BOCHOLT_MENSA']       # Bocholt Mensa375.xml

CAF_BOLOUNGE   = environ['CAF_BOLOUNGE']        # Cafeteria_BoLounge470.xml
CAF_GD         = environ['CAF_GD']              # Cafeteria_Cafeteria GD451.xml
CAF_IB         = environ['CAF_IB']              # Cafeteria_Cafeteria IB441.xml
CAF_ID         = environ['CAF_ID']              # Cafeteria_Cafeteria ID442.xml
CAF_HOCHGES    = environ['CAF_HOCHGES']         # Cafeteria_Hochschule für Gesundheit373.xml

WHS_CAF_NEUBAU = environ['WHS_CAF_NEUBAU']      # Cafeteria_Standort Gelsenkirchen Cafe Neubau 3721.xml
WHS_MENSA      = environ['WHS_MENSA']           # Standort Gelsenkirchen Mensa372.xml
RECKLINGHAUSEN = environ['RECKLINGHAUSEN']      # Standort Recklinghausen374.xml

AW_DATABASE_ID   = environ['AW_DATABASE_ID']    # data
AW_COLLECTION_ID = environ['AW_COLLECTION_ID']  # mensa

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
        bocholtXML = requests.get(f'{BASE_URL}/{BOCHOLT_MENSA}').content
        boloungeXML = requests.get(f'{BASE_URL}/{CAF_BOLOUNGE}').content
        gdXML = requests.get(f'{BASE_URL}/{CAF_GD}').content
        ibXML = requests.get(f'{BASE_URL}/{CAF_IB}').content
        idXML = requests.get(f'{BASE_URL}/{CAF_ID}').content
        hochgesXML = requests.get(f'{BASE_URL}/{CAF_HOCHGES}').content
        whsCafXML = requests.get(f'{BASE_URL}/{WHS_CAF_NEUBAU}').content
        whsMensaXML = requests.get(f'{BASE_URL}/{WHS_MENSA}').content
        recklinghausenXML = requests.get(f'{BASE_URL}/{RECKLINGHAUSEN}').content
    except Exception as e:
        print(f'[-] Failed to download XML files: {e}')
        return None
    print('[#] Downloaded XML files successfully')

    # parse XML
    try:
        mensaRub = ET.fromstring(mensaRubXML)
        roteBete = ET.fromstring(roteBeteXML)
        qwest = ET.fromstring(qwestXML)
        bocholt = ET.fromstring(bocholtXML)
        bolounge = ET.fromstring(boloungeXML)
        gd = ET.fromstring(gdXML)
        ib = ET.fromstring(ibXML)
        id = ET.fromstring(idXML)
        hochges = ET.fromstring(hochgesXML)
        whsCaf = ET.fromstring(whsCafXML)
        whsMensa = ET.fromstring(whsMensaXML)
        recklinghausen = ET.fromstring(recklinghausenXML)
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

    try:
        if not UPDATE_DATA_FAILED: 
            parseAndStoreXML(bocholt, 'bocholt', awDB, #context
                         )
            print('[#] Successfully updated data for Bocholt.')
    except Exception as e:
        UPDATE_DATA_FAILED |= True
        print(f'[-] Failed updated data for Bocholt: {e}')

    try:
        if not UPDATE_DATA_FAILED: 
            parseAndStoreXML(gd, 'caf_gd', awDB, #context
                         )
            print('[#] Successfully updated GD cafeteria data.')
    except Exception as e:
        UPDATE_DATA_FAILED |= True
        print(f'[-] Failed updated GD cafeteria data: {e}')

    try:
        if not UPDATE_DATA_FAILED: 
            parseAndStoreXML(ib, 'caf_ib', awDB, #context
                         )
            print('[#] Successfully updated IB cafeteria data.')
    except Exception as e:
        UPDATE_DATA_FAILED |= True
        print(f'[-] Failed updated IB cafeteria data: {e}')

    try:
        if not UPDATE_DATA_FAILED: 
            parseAndStoreXML(id, 'caf_id', awDB, #context
                         )
            print('[#] Successfully updated ID cafeteria data.')
    except Exception as e:
        UPDATE_DATA_FAILED |= True
        print(f'[-] Failed updated ID cafeteria data: {e}')

    try:
        if not UPDATE_DATA_FAILED: 
            parseAndStoreXML(hochges, 'hochschule_gesundheit', awDB, #context
                         )
            print('[#] Successfully updated "Hochschule für Gesundheit" data.')
    except Exception as e:
        UPDATE_DATA_FAILED |= True
        print(f'[-] Failed updated "Hochschule für Gesundheit" data: {e}')

    try:
        if not UPDATE_DATA_FAILED: 
            parseAndStoreXML(whsCaf, 'whs_caf', awDB, #context
                         )
            print('[#] Successfully updated WHS cafeteria data.')
    except Exception as e:
        UPDATE_DATA_FAILED |= True
        print(f'[-] Failed updated WHS cafeteria data: {e}')

    try:
        if not UPDATE_DATA_FAILED: 
            parseAndStoreXML(whsMensa, 'whs_mensa', awDB, #context
                         )
            print('[#] Successfully updated WHS mensa data.')
    except Exception as e:
        UPDATE_DATA_FAILED |= True
        print(f'[-] Failed updated WHS mensa data: {e}')

    try:
        if not UPDATE_DATA_FAILED: 
            parseAndStoreXML(recklinghausen, 'recklinghausen', awDB, #context
                         )
            print('[#] Successfully updated data for Recklinghausen.')
    except Exception as e:
        UPDATE_DATA_FAILED |= True
        print(f'[-] Failed updated data for Recklinghausen: {e}')
        
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