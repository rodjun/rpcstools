import requests
import os
from sfo import SfoFile
import platform


DEFAULT_RPCS3_SUBDIRS = ["shaderlog",
                         "GuiConfigs",
                         "dev_usb000",
                         "dev_hdd1",
                         "dev_hdd0"]


def is_rpcs3_dir(base_dir):
    return all(os.path.isdir(os.path.join(base_dir, subdir)) for subdir in DEFAULT_RPCS3_SUBDIRS)


def get_rpcs3_dir():
    cur_folder = os.getcwd()

    if is_rpcs3_dir(cur_folder):
        return cur_folder

    if platform.system() == "Linux":
        home_path = os.path.expanduser("~")
        possible_base_dir = os.path.join(home_path, ".config", "rpcs3")
        if is_rpcs3_dir(possible_base_dir):
            return possible_base_dir

    return None


def update_games():
    base_dir = get_rpcs3_dir()

    if base_dir is None:
        raise FileNotFoundError("Couldn't find RPCS3 folder")

    games_dir = os.path.join(base_dir, "dev_hdd0", "game")
    game_ids = []

    for game_dir in os.listdir(games_dir):
        try:
            with open(os.path.join(games_dir, game_dir, "PARAM.SFO"), "rb") as f:
                the_sfo = SfoFile.from_reader(f)
                game_ids.append(the_sfo["TITLE_ID"])
        except FileNotFoundError as e:
            print(e)



if __name__ == "__main__":
    update_games()