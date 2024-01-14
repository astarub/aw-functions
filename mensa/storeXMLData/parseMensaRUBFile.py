# -*- coding: utf-8 -*-

#
#   Imports
#

import utils

import xml.etree.ElementTree as ET
from difflib import get_close_matches

#
#   Global Variables
#

ADDITIVE_SKIP    = ['ohne Kennzeichnung']
COMPONETS_SKIP   = ['Diverse Kuchen', 'Dessert Buffet', 'Desserttheke RUB NEU']
MENULINES_SKIP   = ['USB','Sauce Extra','Schulessen 1','Schulessen 2']

#
#   Functions
#

def parseMensaRUBFile(mensaRub: ET.Element):
    #** Read Mensa RUB

    for weekDay in mensaRub.findall('WeekDays/WeekDay'):
        # week day as format e.g. 'Mo, 10.10.'
        date = f'{weekDay.attrib["Day"][:2]}, {weekDay.attrib["Date"][8:]}.{weekDay.attrib["Date"][5:7]}.'
        for menuLine in weekDay.findall('MenuLine'):
            # skip useless / unessary information 
            if menuLine.attrib['Name'] in MENULINES_SKIP:
                continue
            menuName = menuLine.attrib['Name']

            for details in menuLine.findall('./SetMenu/Component/ComponentDetails'):
                product = details.find('./ProductInfo/Product')
                dishName = product.attrib['name']

                # Nudeltheke is differently used in XML document structure
                if menuName == 'Nudeltheke':
                    dishName = details.find('GastDesc').attrib['value']

                # skip useless / unessary information 
                if dishName in COMPONETS_SKIP:
                    continue

                # Not all dishes have individual price (e.g. Nudelteke) so the 
                # menuLine product info contains the nessary information
                if product.attrib['ProductPrice'] == '0.00': # default value if not set
                    menuProduct = menuLine.find('./SetMenu/SetMenuDetails/ProductInfo/Product') 
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
                    dishAdditives = utils.checkImplicitAddtives(dishName, menuName, get_close_matches(dishName, gastDesc.split('\n'), 1, 0.25)[0])
                except Exception as e:
                    # Ensure definition of dishAdditives
                    dishAdditives = utils.checkImplicitAddtives(dishName, menuName)

                for additives in details.findall('./AdditiveInfo/AdditiveGroup/Additive'):
                    # skip useless / unessary information 
                    if additives.attrib['name'] in ADDITIVE_SKIP:
                        continue
                    # Fisch -> append 'F' and 'd'
                    if 'Fisch' in additives.attrib['name']:
                        dishAdditives.append('F')
                    # map internal additive names to one-letter shortcuts
                    dishAdditives.append(utils.mapAdditivesToShortcuts(additives.attrib['name']))
                # Empty additive list means "ohne Kennzeichnung" only -> should be vegan (hopefully) 
                if len(dishAdditives) == 0: 
                    dishAdditives.append('VG')

    #** Write them to ApWrite Database

                # rename raw-data to human readable name
                menuName = utils.humanizeMenuLineNames(menuName)

                # determine restaurant enum
                restaurant = 'mensa_rub'
                if menuName == 'UniKids / Unizwerge':
                    restaurant = 'unikids'
                elif menuName == 'Henkelmann':
                    restaurant = 'henkelmann'
                
                try:
                    # awDB.create_document(AW_DATABASE_ID, AW_COLLECTION_ID, ID.unique(), {
                    #     'date': date,
                    #     'menuName': menuName,
                    #     'dishName': utils.prettifyDishName(dishName),
                    #     'dishAdditives': list(set(dishAdditives)), # remove duplicates
                    #     'restaurant': restaurant
                    # })
                    pass
                    print(f'[{date}][{restaurant}] {menuName} | {utils.prettifyDishName(dishName)} | {dishPrice} | {list(set(dishAdditives))}')
                except Exception as e:
                    #context.error(f'Failed to create document: {e.message}')
                    continue
                #context.log(f'Wrote {dishName} ({date}) successfully to collection {restaurant}.')