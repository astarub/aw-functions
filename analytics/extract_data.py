import csv


def get_lines_of_csv(filename: str) -> list[str]:
    """
    Return the lines of the csv file as python list object or an empty list on error
    """
    try:
        with open(filename) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=",")
            all_lines = []
            for line in csv_reader:
                all_lines.append(line)
            return all_lines
    except Exception as exc:
        print("Could not open file:", filename, exc)
        return []


def string_to_dict(string: str) -> dict:
    """
    Returns a dict from strings of the form "{"key1":"value1", "key2":"value"}"
    """
    as_dict = {}
    parts = string.split("\"")
    for i in range(1, len(parts), 4):
        as_dict[parts[i]] = parts[i+2]
    return as_dict


def extract_all_values_of_event(filename: str, event_name: str) -> list[dict]:
    """
    Returns a list which contains dicts with the different values of a certain event. e.g., for event selected_a_mensa:\n
    [{'name': 'Mensa der RUB'}, {'name': 'Mensa der RUB'}, {'name': 'Q-West'},...]\n
    Depending on the size of the CSV file this might take some time
    """
    csv_lines: list = get_lines_of_csv(filename)
    if not csv_lines:
        return
    parameter_name = "event_name"
    parameter_list = csv_lines[0]
    if parameter_name not in parameter_list:
        print(f"Could not find parameter {parameter_name}")
        print(f"Possible parameters are {csv_lines[0]}")
        return
    if "event_name" not in parameter_list or "string_props" not in parameter_list:
        print("Parameter list has unexpected content")
        return
    event_name_index = parameter_list.index("event_name")
    string_props_index = parameter_list.index("string_props")
    # list of strings of the form: '{"name1":"value", "name2":"value"}' e.g. ['{"seconds":"157"}', '{"seconds":"195"}']
    all_string_props = []
    for line in csv_lines:
        # found a line with the event we are looking for
        if line[event_name_index] == event_name:
            # filter out empty string props (older entries)
            if line[string_props_index] == "{}":
                continue
            all_string_props.append(string_to_dict(line[string_props_index]))
    return all_string_props


def extract_integer_values_of_string_props(all_string_props: list[dict], value_name: str) -> list[int]:
    """
    Returns a list with integers extracted from the props. i.e. from [{"seconds": "27", "seconds": "35"}] to [27, 35]
    for value_name = "seconds"
    """
    if len(all_string_props) == 0:
        return
    if value_name not in all_string_props[0]:
        print(f"Did not find values with name: {value_name}")
        return
    all_values = []
    for entry in all_string_props:
        if value_name not in entry:
            continue
        try:
            all_values.append(int(entry[value_name]))
        except Exception as exc:
            print("Value is no integer:", exc)
    return all_values


def get_event_names(filename: str) -> list[str]:
    """
    Returns a list of possible events; the events which are tracked by the app and can be visualized
    """
    csv_lines: list = get_lines_of_csv(filename)
    event_names = []
    event_name_index: int = csv_lines[0].index("event_name")
    for line in csv_lines:
        name = line[event_name_index]
        if name not in event_names:
            event_names.append(name)
    return event_names


def string_values_of_string_props_to_dict(all_string_props: list[dict], value_name: str) -> dict:
    """
    Returns a dict of the form {string value: count}, e.g. for the value_name 'name' of event 'selected_a_mensa':
    {'Mensa der RUB': 15, 'Q-West': 7, 'Rote Bete': 8, 'KulturCafe': 9}
    """
    string_values = {}
    for dictionary in all_string_props:
        for key, value in dictionary.items():
            if not key == value_name:
                continue
            if value in string_values:
                string_values[value] += 1
            else:
                string_values[value] = 0
    return string_values


if __name__ == '__main__':
    pass
