# -*- coding: utf-8 -*-

#
#   Functions
#

def humanizeMenuLineNames(menuLineName: str) -> str:
    """
    Match AKAFÖ internal menu names to human readable / well-known
    menu names. 

    Args:
        menuLineName (str): internal name

    Returns:
        str: readable name
    """    
    if menuLineName == 'Komponente 1 RUB':
        return 'Komponentenessen'
    elif menuLineName == 'Vegetarische Menükomponente RUB':
        return 'Vegetarische Menükomponente'
    elif menuLineName == 'Vegetarischer Sprinter RUB':
        return 'Sprinter'
    elif menuLineName == 'Beilagen RUB':
        return 'Beilagen'
    elif menuLineName == 'Aktionsgericht RUB':
        return 'Aktion'
    elif menuLineName == 'Pfannengericht Außerhaus':
        return 'Henkelmann'
    elif menuLineName == 'KITAG 1':
        return 'AKAFÖ Kita'  # KiTag = Kindertagesbetreuung
    elif menuLineName == 'Kitag UniKids':
        return 'UniKids / Unizwerge'
    elif menuLineName == 'Dessert portioniert RUB':
        return 'Dessert'
    elif menuLineName == 'Grill Cube 1':
        return 'Grill Cube'
    else:
        return menuLineName.strip()
    
def mapAdditivesToShortcuts(additiveName: str) -> str:
    """
    Return one or two letter shortcut for additive name.

    Args:
        additiveName (str): Name of additive to shortcut.

    Returns:
        str: Shortcut of the given additive.
    """    
    if 'Gluten' in additiveName:
        return 'a'
    elif 'Weizen' in additiveName:
        return 'a1'
    elif 'Roggen' in additiveName:
        return 'a2'
    elif 'Gerste' in additiveName:
        return 'a3'
    elif 'Hafer' in additiveName:
        return 'a4'
    elif 'Dinkel' in additiveName:
        return 'a5'
    elif 'Kamut' in additiveName:
        return 'a6'
    elif 'Krebstiere' in additiveName:
        return 'b'
    elif 'Eier' in additiveName:
        return 'c'
    elif 'Fisch' in additiveName:
        return 'd'
    elif 'Erdnüsse' in additiveName:
        return 'e'
    elif 'Sojabohnen' in additiveName:
        return 'f'
    elif 'Milch' in additiveName or 'Lactose' in additiveName:
        return 'g'
    elif 'Schalenfrucht(e)' in additiveName:
        return 'h'
    elif 'Spuren von Schalenfrüchte' in additiveName:
        return 'u'
    elif 'Mandel' in additiveName:
        return 'h1'
    elif 'Haselnuss' in additiveName:
        return 'h2'
    elif 'Walnuss' in additiveName:
        return 'h3'
    elif 'Cashewnuss' in additiveName:
        return 'h4'
    elif 'Pecanuss' in additiveName:
        return 'h5'
    elif 'Paranuss' in additiveName:
        return 'h6'
    elif 'Pistazie' in additiveName:
        return 'h7'
    elif 'Macadamia' in additiveName or 'Quennslandnuss' in additiveName:
        return 'h8'
    elif 'Sellerie' in additiveName:
        return 'i'
    elif 'Senf' in additiveName:
        return 'j'
    elif 'Sesamsamen' in additiveName:
        return 'k'
    elif 'Schwefeldioxis' in additiveName:
        return 'l'
    elif 'Lupine' in additiveName:
        return 'm'
    elif 'Weichtiere' in additiveName:
        return 'n'
    elif 'Halal' in additiveName:
        return 'H'
    elif 'Geflügel' in additiveName:
        return 'G'
    elif 'Schwein' in additiveName:
        return 'S'
    elif 'Rind' in additiveName:
        return 'R'
    elif 'Lamm' in additiveName:
        return 'L'
    elif 'Wild' in additiveName:
        return 'W'
    elif 'Alkohol' in additiveName:
        return 'A'
    elif 'Farbstoff' in additiveName:
        return '1'
    elif 'Konservierungsstoff' in additiveName:
        return '2'
    elif 'Antioxidationsmittel' in additiveName:
        return '3'
    elif 'geschwefelt' in additiveName:
        return '5'
    elif 'geschwärzt' in additiveName:
        return '6'
    elif 'Phosphat' in additiveName:
        return '8'
    elif 'Süßungsmittel' in additiveName:
        return '9'
    elif 'Phenylalaninquelle' in additiveName:
        return '10'
    elif 'Schwefeldioxid' in additiveName:
        return 'E220'
    elif 'koffeinhaltig' in additiveName:
        return '12'
    elif 'Gelatine' in additiveName:
        return 'EG' # not displayed on AKAFÖ site or app 
    elif 'Geschmacksverstärker' in additiveName:
        return '4'
    else:
        return additiveName.strip()
    
def prettifyDishName(dishName: str) -> str:
    """
    Create pretty dish names by removing unessacary strings.

    Args:
        dishName (str): The ugly dish name.

    Returns:
        str: The pretty dish name.
    """    
    tmp = ( dishName
        .replace('NEU', '')
        .replace('(RUB)', '')
        .replace('RUB', '')
        .replace('(VG)', '')
        .replace('(V)', '')
        .replace('(H)', '')
        .replace('(G)', '')
        .replace('(S)', '')
        #.replace(' S', '') -> somethimes AKAFÖ just set "S" instead of "(S)"
        .replace('SF', '') # Study & Fit
        .replace('(QW)', '')
        .replace('QW', '')
        .replace('(Cube)', '')
        .replace('Topping:', '')
        .strip()
    )
    
    if tmp == 'Salattheke':
        return 'Diverse frei zusammenstellbare Auswahl (auch vegetarisch und vegan)'
    else:
        return tmp

def checkImplicitAddtives(*argv) -> list[str]:
    """
    Some Additives are not in the correct XML field, but the information
    exists implicitly in other string, e.g. names. This function extracts
    this information as good as possible.

    Returns:
        list[str]: List of additives. 
    """    
    additives = []
    for string in argv:
        # check if some weird argument was given
        if type(string) != str:
            continue
        # append some additives manually because this information is not in XML data
        if '(VG)' in string or 'vegan' in string.lower():
            additives.append('VG')
        if '(V)' in string or 'vegetarisch' in string.lower():
            additives.append('V')
        if '(G)' in string:
            additives.append('G')
        if '(S)' in string:
            additives.append('S')
        if '(F)' in string:
            additives.append('F')
        if '(A)' in string:
            additives.append('A')
        if '(H)' in string or 'halal' in string.lower():
            additives.append('S')

    return additives