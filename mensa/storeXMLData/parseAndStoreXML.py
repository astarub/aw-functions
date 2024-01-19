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
MENULINES_SKIP   = ['USB','Sauce Extra','Schulessen 1','Schulessen 2']

AW_DATABASE_ID   = environ['AW_DATABASE_ID']
AW_COLLECTION_ID = environ['AW_COLLECTION_ID']

#
#   Functions
#

def parseAndStoreXML(xml: ET.Element, restaurant: str, awDB: Databases, # context
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

    for weekDay in xml.findall('WeekDays/WeekDay'):
        # week day as format e.g. 'Mo, 10.10.'
        date = f'{weekDay.attrib["Day"][:2]}, {weekDay.attrib["Date"][8:]}.{weekDay.attrib["Date"][5:7]}.'
        for menuLine in weekDay.findall('MenuLine'):
            # skip useless / unessary information 
            if menuLine.attrib['Name'] in MENULINES_SKIP:
                continue
            menuName = menuLine.attrib['Name']

            for details in menuLine.findall('./SetMenu/Component/ComponentDetails'):
                product = details.find('./ProductInfo/Product')
                dishName = details.find('GastDesc').attrib['value']

                # skip useless / unessary information 
                if dishName in COMPONETS_SKIP:
                    continue

                # Not all dishes have individual price (e.g. Nudelteke) so the 
                # menuLine product info contains the nessary information
                if product.attrib['ProductPrice'] == '0.00':
                    menuProduct = menuLine.find('./SetMenu/SetMenuDetails/ProductInfo/Product')
                    # Not all menus contains the nessacary information, so instead of storing 
                    # 0.00€ es price it will be set to a fallback value.
                    if menuProduct.attrib['ProductPrice'] == '0.00':
                        dishPrice = None
                    else:
                        dishPrice = f"{menuProduct.attrib['ProductPrice']}€ / {menuProduct.attrib['ProductPrice3']}€"
                else:
                    # Price = '2.00€ / 3.00€' -> internal / external price
                    dishPrice = f"{product.attrib['ProductPrice']}€ / {product.attrib['ProductPrice3']}€"

                # create a list of allergies and information
                try: 
                    # AKAFÖ lists (sometimes) all components as string in the field for english translations.
                    # This field contains (sometimes as only) the information about vegan or vegetarian.
                    gastDesc = menuLine.find('./SetMenu/SetMenuDetails/GastDesc/GastDescTranslation').attrib['value']
                    # Use string-matches to determine additives that not contained in the field for contains
                    dishAdditives = checkImplicitAddtives(dishName, menuName, get_close_matches(dishName, gastDesc.split('\n'), 1, 0.25)[0])
                except Exception as e:
                    # Ensure definition of dishAdditives
                    dishAdditives = checkImplicitAddtives(dishName, menuName)

                for additives in details.findall('./AdditiveInfo/AdditiveGroup/Additive'):
                    # skip useless / unessary information 
                    if additives.attrib['name'] in ADDITIVE_SKIP:
                        continue
                    # Fisch -> append 'F' and 'd'
                    if 'Fisch' in additives.attrib['name']:
                        dishAdditives.append('F')
                    # map internal additive names to one-letter shortcuts
                    dishAdditives.append(mapAdditivesToShortcuts(additives.attrib['name']))
                # Empty additive list means "ohne Kennzeichnung" only -> should be vegan (hopefully) 
                if len(dishAdditives) == 0: 
                    dishAdditives.append('VG')

    #** Write them to ApWrite Database

                # rename raw-data to human readable name
                menuName = humanizeMenuLineNames(menuName)

                # determine restaurant enum
                if menuName == 'UniKids / Unizwerge' or menuName == "AKAFÖ Kita":
                    _restaurant = 'unikids'
                elif menuName == 'Henkelmann':
                    _restaurant = 'henkelmann'
                else:
                    # reset restaurant for looping
                    _restaurant = restaurant
                
                try:
                    awDB.create_document(AW_DATABASE_ID, AW_COLLECTION_ID, ID.unique(), {
                        'date': date,
                        'menuName': menuName,
                        'dishName': prettifyDishName(dishName),
                        'dishPrice': dishPrice,
                        'dishAdditives': list(set(dishAdditives)), # remove duplicates
                        'restaurant': _restaurant
                    })
                except Exception as e:
                    print(f'[-] Failed to create document: {e}')
                    continue # should not (!) exit 
                
                print(f'[+] [{_restaurant}][{date}]: {menuName} | {prettifyDishName(dishName)} | {dishPrice} | {list(set(dishAdditives))}')