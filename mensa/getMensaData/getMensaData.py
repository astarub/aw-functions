# -*- coding: utf-8 -*-

#
#   Imports
#

from os import environ

from appwrite.client import Client
from appwrite.services.databases import Databases
from appwrite.query import Query

#
#   Global Variables
#

AW_DATABASE_ID   = environ['AW_DATABASE_ID']
AW_COLLECTION_ID = environ['AW_COLLECTION_ID']

RESTAURANT_ENUM = ['mensa_rub', 'henkelmann', 'unikids', 'rote_bete', 'qwest']

#
#   Functions
#

def main(context):

    #** Parse Request

    # return 400 is query isn't json
    if context.req.query['type'] != 'json':
        context.error(f'[-] Failed to read request: No JSON')
        return context.req.send('', 400)

    # expecting the format: { "restaurant": "[AW_COLLECTION_ID]" }
    try: 
        restaurant = context.req.body.restaurant
    except Exception as e:
        context.error(f'[-] Failed to parse request body: {e}')
        return context.req.send('', 400)
    
    if restaurant not in RESTAURANT_ENUM:
        context.error(f'[-] Unreconized restaurant: {restaurant}')
        return context.req.send('', 400)

    #** Initialize AW Connection

    awClient = ( Client()
        .set_endpoint(environ['AW_ENDPOINT'])
        .set_project(environ['AW_PROJECT_ID'])
        .set_key(environ['AW_API_KEY'])
    )
    awDB = Databases(awClient)

    #** Read Database

    try:
        restaurantData = awDB.list_documents(
            AW_DATABASE_ID, 
            AW_COLLECTION_ID, 
            [Query.limit(500), Query.search('restaurant', restaurant)]
        )
    except Exception as e:
        context.error(f'[-] Failed to read {restaurant} from {AW_COLLECTION_ID} collection: {e}')
        return context.response.send('', 500)
    
    #** Return Data

    # TODO: return data from collection to use in app ...
    # TODO: what would be a food datastructure -> adjust in frontend too?