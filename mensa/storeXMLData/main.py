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

from .parseAndStoreMensaXML import parseAndStoreMensaXML
from .parseAndStoreCafeXML import parseAndStoreCafeXML

from .utils import cloudPrint

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

AW_DATABASE_ID   = environ['AW_DATABASE_ID']    # mensa

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
        cloudPrint(context, f'[-] Failed to download XML files: {e}')
        return None
    cloudPrint(context, '[#] Downloaded XML files successfully')

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
        cloudPrint(context, f'[-] Failed to parse XML files: {e}')
        return None
    cloudPrint(context, '[#] Parsed XML files successfully')
    
    #** Initialize AW Connection

    awClient = ( Client()
        .set_endpoint(environ['AW_ENDPOINT'])
        .set_project(environ['AW_PROJECT_ID'])
        .set_key(environ['AW_API_KEY'])
    )
    awDB = Databases(awClient)
    
    supportedLocales = None
    try:
        supportedLocales = awDB.get_document( database_id = 'data', collection_id = 'config', document_id = 'supportedLocales')['value']
    except:
        cloudPrint('[-] Failed to get supported locales doc. Aborting.')
        return
    
    for locale in supportedLocales:
        #** Store current list of dishes

        # This is used in garbage collection later. Limit is set to 5000 to ensure
        # downloading the full collection. In production, there should be ~1000 dishes in total.
        oldCollection = awDB.list_documents(AW_DATABASE_ID, locale, [Query.limit(5000)])
        cloudPrint(context, f'[#] Current collection has {oldCollection["total"]} dishes.')

        #** Parse and Store Data

        try:
            parseAndStoreMensaXML(mensaRub, 'mensa_rub', awDB, locale, context)
            cloudPrint(context, '[#] Successfully updated RUB Mensa data.')
        except Exception as e:
            UPDATE_DATA_FAILED |= True
            cloudPrint(context, f'[-] Failed updated RUB Mensa data: {e}')

        try:
            if not UPDATE_DATA_FAILED: 
                parseAndStoreMensaXML(roteBete, 'rote_bete', awDB, locale, context)
                cloudPrint(context, '[#] Successfully updated Rote-Bete data.')
        except Exception as e:
            UPDATE_DATA_FAILED |= True
            cloudPrint(context, f'[-] Failed updated Rote-Bete data: {e}')

        try:
            if not UPDATE_DATA_FAILED: 
                parseAndStoreMensaXML(qwest, 'qwest', awDB, locale, context)
                cloudPrint(context, '[#] Successfully updated Q-West data.')
        except Exception as e:
            UPDATE_DATA_FAILED |= True
            cloudPrint(context, f'[-] Failed updated Q-West data: {e}')

        try:
            if not UPDATE_DATA_FAILED: 
                parseAndStoreMensaXML(bocholt, 'bocholt', awDB, locale, context)
                cloudPrint(context, '[#] Successfully updated data for Bocholt.')
        except Exception as e:
            UPDATE_DATA_FAILED |= True
            cloudPrint(context, f'[-] Failed updated data for Bocholt: {e}')

        try:
            if not UPDATE_DATA_FAILED: 
                parseAndStoreMensaXML(whsMensa, 'whs_mensa', awDB, locale, context)
                cloudPrint(context, '[#] Successfully updated WHS mensa data.')
        except Exception as e:
            UPDATE_DATA_FAILED |= True
            cloudPrint(context, f'[-] Failed updated WHS mensa data: {e}')

        try:
            if not UPDATE_DATA_FAILED: 
                parseAndStoreMensaXML(recklinghausen, 'recklinghausen', awDB, locale, context)
                cloudPrint(context, '[#] Successfully updated data for Recklinghausen.')
        except Exception as e:
            UPDATE_DATA_FAILED |= True
            cloudPrint(context, f'[-] Failed updated data for Recklinghausen: {e}')

        if not UPDATE_DATA_FAILED: 
            cloudPrint(context, '[+] Successfully updated all mensa data.')

        #! Do not parse cafeterias due lack of date information.
        # try:
        #     if not UPDATE_DATA_FAILED: 
        #         parseAndStoreCafeXML(gd, 'caf_gd', awDB, context)
        #         cloudPrint(context, '[#] Successfully updated GD cafeteria data.')
        # except Exception as e:
        #     UPDATE_DATA_FAILED |= True
        #     cloudPrint(context, f'[-] Failed updated GD cafeteria data: {e}')

        # try:
        #     if not UPDATE_DATA_FAILED: 
        #         parseAndStoreCafeXML(ib, 'caf_ib', awDB, context)
        #         cloudPrint(context, '[#] Successfully updated IB cafeteria data.')
        # except Exception as e:
        #     UPDATE_DATA_FAILED |= True
        #     cloudPrint(context, f'[-] Failed updated IB cafeteria data: {e}')

        # try:
        #     if not UPDATE_DATA_FAILED: 
        #         parseAndStoreCafeXML(id, 'caf_id', awDB, context)
        #         cloudPrint(context, '[#] Successfully updated ID cafeteria data.')
        # except Exception as e:
        #     UPDATE_DATA_FAILED |= True
        #     cloudPrint(context, f'[-] Failed updated ID cafeteria data: {e}')

        # try:
        #     if not UPDATE_DATA_FAILED: 
        #         parseAndStoreCafeXML(hochges, 'hochschule_gesundheit', awDB, context)
        #         cloudPrint(context, '[#] Successfully updated "Hochschule für Gesundheit" data.')
        # except Exception as e:
        #     UPDATE_DATA_FAILED |= True
        #     cloudPrint(context, f'[-] Failed updated "Hochschule für Gesundheit" data: {e}')

        # try:
        #     if not UPDATE_DATA_FAILED: 
        #         parseAndStoreCafeXML(whsCaf, 'whs_caf', awDB, context)
        #         cloudPrint(context, '[#] Successfully updated WHS cafeteria data.')
        # except Exception as e:
        #     UPDATE_DATA_FAILED |= True
        #     cloudPrint(context, f'[-] Failed updated WHS cafeteria data: {e}')

        #** Garbage collection

        if UPDATE_DATA_FAILED:
            try:
                # Delete new entries / entries that are created while failing
                newCollection = awDB.list_documents(AW_DATABASE_ID, locale, [Query.limit(2000)])
                toDelete = [dish for dish in newCollection['documents'] if dish not in oldCollection['documents']]
                cloudPrint(context, f'[#] Try to delete {len(toDelete)} garbage dishes.')
                for dish in toDelete:
                    awDB.delete_document(AW_DATABASE_ID, locale, dish['$id'])
                cloudPrint(context, '[+] Garbage collection succesfully.')
            except Exception as e:
                cloudPrint(context, f'[-] Failed to delete created dishes while failing to update: {e}')
        else:
            try:
                cloudPrint(context, f'[#] Try to delete {oldCollection["total"]} garbage dishes.')
                # This can take very long depending on garbage count. Should not be more 
                # than ~1000 dishes per run in production. Use with caution while developing!
                for dish in oldCollection['documents']:
                    awDB.delete_document(AW_DATABASE_ID, locale, dish['$id'])
                cloudPrint(context, '[+] Garbage collection succesfully.')
                newCollection = awDB.list_documents(AW_DATABASE_ID, locale, [Query.limit(1)])
                cloudPrint(context, f'[#] Current collection has {newCollection["total"]} dishes.')
            except Exception as e:
                cloudPrint(context, f'[-] Garbage collection failed {e}')

        # required return by AppWrite
        if context != '':
            return context.res.empty()

# Use for local execution
# if __name__ == "__main__":
#     main('')