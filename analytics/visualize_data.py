import extract_data
import matplotlib.pyplot as plt
import seaborn as sns
import os.path

# directory has to exist, else it will throw an error. Path is relative
IMAGE_FILE_DIR = "images"


def bar_plot_string_data(data: dict, xlabel: str = "", ylabel: str = "", title: str = "",
                         output_filename: str = None) -> None:
    data = dict(sorted(data.items(), key=lambda item: item[1], reverse=True))
    values = list(data.values())
    keys = list(data.keys())
    no_evt_msg = "KEINE DATEN\nEntweder ein Fehler\nist passiert,\noder diesen Monat\ngab es keine Ereignisse\ndieses events"
    if not keys:  # no data to display
        keys = [no_evt_msg]
        values = [1]

    size_limit = 15
    for i in range(len(keys)):
        if keys[0] == no_evt_msg:
            break
        # rudimentary splitting of too long keys
        if len(keys[i]) > size_limit:
            k = keys.pop(i)
            new_key = [k[j:j+size_limit] + "-\n" for j in range(0, len(k), size_limit)]
            new_key[-1] = new_key[-1][:-2]
            new_key = "".join(new_key)
            keys.insert(i, new_key)

    plt.close()  # "reset" plt to avoid side effects with other plotting
    sns.barplot(x=values, y=keys)

    if xlabel:
        plt.xlabel(xlabel)
    if ylabel:
        plt.ylabel(ylabel)
    plt.suptitle(title, fontweight="bold", size="x-large")

    if output_filename:
        # change ratio here (e.g. w: 8, h: 6 for 4 to 3 or w: 8, h: 4.5 for 16 to 9)
        plt.gcf().set_size_inches(8, 4.5)
        # move plot to the right to make space for keys
        max_len = max([len(k) for k in keys])
        move_plot = max_len * 0.018
        move_plot = min(move_plot, size_limit * 0.018)
        plt.subplots_adjust(left=move_plot)

        plt.tight_layout()
        plt.savefig(output_filename + ".png", format="png", dpi=240)
    else:
        plt.show()


def hist_plot_data(data: list[int | float], bins: int = 30, xlabel: str = "", ylabel: str = "", title: str = "",
                   output_filename: str = None) -> None:
    no_data = ""
    if not data:
        no_data = "KEINE DATEN, Entweder ein Fehler ist passiert\noder diesen Monat gab es keine Ereignisse dieses events"
        data = [1]
    plt.close()  # "reset" plt to avoid side effects with other plotting
    plt.hist(data, bins=bins)
    average = sum(data) // len(data)

    if xlabel:
        plt.xlabel(xlabel)
    if ylabel:
        plt.ylabel(ylabel)
    plt.suptitle(title, fontweight="bold", size="x-large")
    plt.title(f"Durchschnitt: {average} {no_data}")

    if output_filename:
        plt.gcf().set_size_inches(8, 4.5)
        plt.tight_layout()
        plt.savefig(output_filename + ".png", format="png", dpi=240)
    else:
        plt.show()


def get_output_file_information(file_location: str) -> str:
    """
    Returns the common part of the output files
    remove "campusapp" and ".csv"; leave the year and month
    """
    filename = file_location
    if "/" in file_location:
        filename = file_location.split("/")[-1]
    if "\\" in file_location:
        filename = file_location.split("\\")[-1]
    return filename[9:-4]


def visualize_mensa_usage(csv_file_location: str, save_png: bool = True) -> None:
    if not os.path.isfile(csv_file_location):
        print("Could not find file:", csv_file_location)
        return
    selected_mensa_props = extract_data.extract_all_values_of_event(csv_file_location, "selected_a_mensa")
    mensa_names_dict = extract_data.string_values_of_string_props_to_dict(selected_mensa_props, "name")

    output_filename = None
    if save_png:
        output_filename = os.path.join(IMAGE_FILE_DIR, "MensaUsage" + get_output_file_information(csv_file_location))

    bar_plot_string_data(mensa_names_dict, "Anzahl", "Name", "Mensapläne angetippt", output_filename)


def visualize_saved_events(csv_file_location: str, save_png: bool = True) -> None:
    if not os.path.isfile(csv_file_location):
        print("Could not find file:", csv_file_location)
        return
    saved_events_props = extract_data.extract_all_values_of_event(csv_file_location, "saved_event")
    saved_events_dict = extract_data.string_values_of_string_props_to_dict(saved_events_props, "name")

    output_filename = None
    if save_png:
        output_filename = os.path.join(IMAGE_FILE_DIR, "SavedEvents" + get_output_file_information(csv_file_location))

    bar_plot_string_data(saved_events_dict, "Anzahl", "Name", "Gespeicherte Events", output_filename)


def visualize_usage_time(csv_file_location: str, save_png: bool = True) -> None:
    if not os.path.isfile(csv_file_location):
        print("Could not find file:", csv_file_location)
        return
    usage_time_props = extract_data.extract_all_values_of_event(csv_file_location, "usage_time")
    usage_times = extract_data.extract_integer_values_of_string_props(usage_time_props, "seconds")

    output_filename = None
    if save_png:
        output_filename = os.path.join(IMAGE_FILE_DIR, "UsageTime" + get_output_file_information(csv_file_location))

    hist_plot_data(usage_times, 30, "Nutzungszeit in Sekunden", "Anzahl", "Zeit am Stück in App", output_filename)


def save_all_as_png(csv_location: str) -> None:
    visualize_mensa_usage(csv_location, save_png=True)
    visualize_usage_time(csv_location, save_png=True)
    visualize_saved_events(csv_location, save_png=True)


if __name__ == '__main__':
    _year, _month, _build_mode = "2024", "05", "debug"
    _filename = f"campusapp-{_build_mode}-{_year}-{_month}.csv"

    # for separate testing of adjustments:

    # save_all_as_png(_filename)
    # visualize_mensa_usage(_filename, save_png=True)
    # visualize_mensa_usage(_filename, save_png=False)
    # visualize_saved_events(_filename, save_png=True)
    # visualize_saved_events(_filename, save_png=False)
    # visualize_usage_time(_filename, save_png=True)
    # visualize_usage_time(_filename, save_png=False)
