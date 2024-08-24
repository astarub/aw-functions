# -*- coding: utf-8 -*-

#
#   Imports
#

from utils import  (
    humanizeMenuLineNames,
    mapAdditivesToShortcuts,
    prettifyDishName,
    checkImplicitAddtives
)

from appwrite.id import ID
from appwrite.services.databases import Databases

from os import environ
import xml.etree.ElementTree as ET
from difflib import get_close_matches

#
#   Global Variables
#

ADDITIVE_SKIP    = ['ohne Kennzeichnung']
COMPONETS_SKIP   = ['Diverse Kuchen', 'Div. Kuchen', 'Dessert Buffet', 'Desserttheke RUB NEU']
MENULINES_SKIP   = ['USB','Sauce Extra','Schulessen 1','Schulessen 2', 'Pfannengerichte', 'Hauptgerichte Schwein', 'Hauptgerichte Geflügel', 'Aktion', 'Hauptgerichte Diverses', 'Hauptgerichte Fisch', 'Hauptgerichte Vegetarisch', 'Hauptgerichte Vegan']

AW_DATABASE_ID   = environ['AW_DATABASE_ID']
AW_COLLECTION_ID = environ['AW_COLLECTION_ID']

#
#   Functions
#

def parseAndStoreCafeXML(xml: ET.Element, restaurant: str, awDB: Databases, # context
                     ) -> None:
    """
    This function reads the XML document and will parse them into dish entities.
    The entities are write to the approchiate AppWrite database. 

    Database cleaning like removing old dish entries or avoiding dublicates is not
    in the scope of this function. It will only read the XML and write new documents
    (dish entities) to the database.

    Also it assumes that the coded and provided restaurants are correct collection IDs
    configured in the AppWrite backend. 

    Args:
        xml (ET.Element): AKAFÖ provided XML containing the mensa data.
        restaurant (str): The collection ID and restaurant name.
                          Possible values: mensa_rub, qwest, henkelmann, unikids and rote_bete
        awDB (AppWrite Databases): The AppWrite Database connecter to create new entries.
        context: AppWrite Cloud Function Execution Context
    """    

    #** Read XML File

    for component in xml.findall('Component'):

        date = '2024-08-26'
        try:
            menuName = component.attrib['RecipeGroup']
        except:
            menuName = component.attrib['ComponentGroup']
        dishName = component.attrib['ProductName']
        dishPrice = f"{component.attrib['ProductPrice']}€ / {component.attrib['ProductPrice3']}€"

        if menuName in MENULINES_SKIP:
            continue

        dishAdditives = []
        for additives in component.findall('./ComponentDetails/AdditiveInfo/AdditiveGroup/Additive'):
            # skip useless / unessary information 
            if additives.attrib['name'] in ADDITIVE_SKIP:
                continue
            # Fisch -> append 'F' and 'd'
            if 'Fisch' in additives.attrib['name']:
                dishAdditives.append('F')
            # map internal additive names to one-letter shortcuts
            dishAdditives.append(mapAdditivesToShortcuts(additives.attrib['name']))
            dishAdditives = checkImplicitAddtives(prettifyDishName(dishName), menuName)

#** Write them to ApWrite Database

        # rename raw-data to human readable name
        menuName = humanizeMenuLineNames(menuName)
        
        try:
            document = {
                'date': date,
                'menuName': menuName,
                'dishName': prettifyDishName(dishName),
                'dishPrice': dishPrice,
                'dishAdditives': list(set(dishAdditives)), # remove duplicates
                'restaurant': restaurant
            }
            awDB.create_document(AW_DATABASE_ID, AW_COLLECTION_ID, ID.unique(), document)
        except Exception as e:
            print(f'[-] Failed to create document: {e}')
            continue # should not (!) exit 
        
        print(f'[+] [{restaurant}][{date}]: {menuName} | {prettifyDishName(dishName)} | {dishPrice} | {list(set(dishAdditives))}')