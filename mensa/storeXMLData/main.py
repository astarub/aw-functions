# -*- coding: utf-8 -*-

#
#   Imports
#

import requests
from os import environ
import xml.etree.ElementTree as ET

from appwrite.client import Client
from appwrite.services.databases import Databases

from .parseAndStoreXML import parseAndStoreXML

#
#   Global Variables
#

BASE_URL       = environ['BASE_URL']
MENSA_RUB_FILE = environ['MENSA_RUB_FILE']
QWEST_FILE     = environ['QWEST_FILE']
ROTE_BETE_FILE = environ['ROTE_BETE_FILE']

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
        roteBeteXML = requests.get(f'{BASE_URL}/{ROTE_BETE_FILE}').content
        qwestXML = requests.get(f'{BASE_URL}/{QWEST_FILE}').content
    except Exception as e:
        context.error(f'[-] Failed to download XML files: {e}')
        return None
    context.log('[#] Downloaded XML files successfully')

    # parse XML
    try:
        mensaRub = ET.fromstring(mensaRubXML)
        roteBete = ET.fromstring(roteBeteXML)
        qwest = ET.fromstring(qwestXML)
    except Exception as e:
        context.error(f'[-] Failed to parse XML files: {e}')
        return None
    context.log('[#] Parsed XML files successfully')
    
    #** Initialize AW Connection

    awClient = ( Client()
        .set_endpoint(environ['AW_ENDPOINT'])
        .set_project(environ['AW_PROJECT_ID'])
        .set_key(environ['AW_API_KEY'])
    )
    awDB = Databases(awClient)

    #** Parse and Store Data

    try:
        parseAndStoreXML(mensaRub, 'mensa_rub', awDB, context)
        context.log('[#] Successfully updated mensa data.')
    except Exception as e:
        context.error(f'[-] Failed updated mensa data: {e}')
        
    try:
        parseAndStoreXML(roteBete, 'rote_bete', awDB, context)
        context.log('[#] Successfully updated rote bete data.')
    except Exception as e:
        context.error(f'[-] Failed updated rote bete data: {e}')
        
    try:
        parseAndStoreXML(qwest, 'qwest', awDB, context)
        context.log('[#] Successfully updated Q-West data.')
    except Exception as e:
        context.error(f'[-] Failed updated Q-West data: {e}')
        
    context.log('[#] Successfully updated all mensa data.')