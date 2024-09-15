import requests
import json
from os import environ
from .utils import cloudPrint

def translateText(text: str, sourceLang: str, targetLang: str, context):
    response = requests.post(
        'https://translate.app.asta-bochum.de/translate', 
        headers= {'Content-Type': 'application/json'}, 
        json = {
            'q': text,
            'source': sourceLang,
            'target': targetLang,
            'format': 'text',
            'api_key': environ['TRANSLATE_API_KEY']
        }
    )
    
    if response.status_code == 200:
        json_response = json.loads(response.content.decode('utf-8'))
        
        return json_response['translatedText']
    else:
        cloudPrint(context, f'[-] Translation server error. Status code: {response.status_code}. Content: {response.text}')
        raise Exception('Translation server error.')
        
    
