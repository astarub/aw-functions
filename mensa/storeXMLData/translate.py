# -*- coding: utf-8 -*-

import json
import aiohttp
import asyncio
from os import environ
from .utils import cloudPrint

async def translateText(text: str, sourceLang: str, targetLang: str, context):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            'https://translate.app.asta-bochum.de/translate', 
            json={
                'q': text,
                'source': sourceLang,
                'target': targetLang,
                'format': 'text',
                'api_key': environ['TRANSLATE_API_KEY']
            }, 
            headers={
                'Content-Type': 'application/json'
            }
        ) as response:
            if response.status != 200: 
               cloudPrint(context, f'[-] Translation server error. Status code: {response.status_code}. Body {response.text}')
               raise Exception('Translation server error.')
           
            rbytes = await response.read()
            
            json_response = json.loads(rbytes.decode('utf-8'))
            
            return json_response['translatedText']