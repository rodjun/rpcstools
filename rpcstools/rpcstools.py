import requests
import os
import platform
import yaml
import urllib3
import tqdm
import hashlib
import xml.etree.ElementTree as ET
from .sfo import SfoFile

BUFFER_SIZE = 1024 * 1024 * 3

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


def get_title_id(game_folder):
    try:
        with open(os.path.join(game_folder, "PARAM.SFO"), "rb") as f:
            the_sfo = SfoFile.from_reader(f)
            return the_sfo["TITLE_ID"]
    except FileNotFoundError:
        try:
            with open(os.path.join(game_folder, "PS3_GAME", "PARAM.SFO"), "rb") as f:
                the_sfo = SfoFile.from_reader(f)
                return the_sfo["TITLE_ID"]
        except FileNotFoundError:
            return None


def local_pkg_valid(file_path, file_name, expected_file_size, expected_hash, check_hash=False):
    if not os.path.isfile(file_path):
        return False

    file_size = os.path.getsize(file_path)

    if file_size != expected_file_size:
        return False

    if check_hash:
        # This ***should*** not fail because we already tested if the file exists, but who knows.
        try:
            with open(file_path, "rb") as f:
                sha1_hash = hashlib.sha1()

                pbar = tqdm.tqdm(
                            total=file_size,
                            unit='B',
                            unit_scale=True,
                            desc="Checking hash of package {}".format(file_name)
                        )

                bytes_left = file_size

                while True:
                    buf = f.read(BUFFER_SIZE)
                    bytes_left -= len(buf)
                    pbar.update(len(buf))

                    if bytes_left < 0x20:
                        sha1_hash.update(buf[:-(0x20 - bytes_left)])
                        pbar.update(bytes_left)  # Get that sweet 100%
                        break
                    else:
                        sha1_hash.update(buf)

                if sha1_hash.hexdigest() != expected_hash:
                    return False

        except FileNotFoundError:
            return False

    return True


def download_updates(tid, base_dir, cert_path):
    print("Downloading updates for title_id {}".format(tid))

    content_folder = os.path.join(base_dir, 'game_updates', str(tid))

    if not os.path.isdir(content_folder):
        os.mkdir(content_folder)

    r = requests.get(url="https://a0.ww.np.dl.playstation.net/tpl/np/{tid}/{tid}-ver.xml".format(tid=tid),
                     verify=cert_path)
    try:
        xml_tree = ET.fromstring(r.text)
    except ET.ParseError:
        print("Failed to parse xml for {} (Game might not have any updates)\n".format(tid))  # Extra \n is intentional
        return

    for node in xml_tree.iter('package'):
        disk_filename = node.attrib['url'].split(os.path.sep)[-1]
        disk_filepath = os.path.join(content_folder, disk_filename)

        if not local_pkg_valid(disk_filepath,
                               disk_filename,
                               int(node.attrib['size']),
                               node.attrib['sha1sum'],
                               check_hash=True):

            r = requests.get(node.attrib['url'],
                             verify=cert_path,
                             stream=True)

            total_size = int(r.headers.get('content-length', 0))

            with open(disk_filepath, "wb") as f:
                pbar = tqdm.tqdm(
                    total=total_size,
                    unit='B',
                    unit_scale=True,
                    desc="Downloading {}".format(disk_filename)
                )

                for data in r.iter_content(1024):
                    f.write(data)
                    pbar.update(1024)
                pbar.close()
    print()


# TODO: Argument for the rpcs3 folder
# TODO: Handle more exceptions/possible error cases
# TODO: Variable naming is hard
# TODO: Verify SHA-1
def update_games():
    # Silence warnings caused by HIGH QUALITY Sony certs
    urllib3.disable_warnings(urllib3.exceptions.SubjectAltNameWarning)

    base_dir = get_rpcs3_dir()

    if base_dir is None:
        raise FileNotFoundError("Couldn't find RPCS3 folder, make sure you call "
                                "update-rpcs3-games from the rpcs3 folder if you're not on Linux.")

    games_dirs = (os.path.join(base_dir, "dev_hdd0", "game"),
                  os.path.join(base_dir, "dev_hdd0", "disc"))

    game_ids = []

    for games_dir in games_dirs:
        for game_dir in os.listdir(games_dir):
            tid = get_title_id(os.path.join(games_dir, game_dir))
            if tid is not None:
                game_ids.append(tid)
            else:
                print("warning: Couldn't find PARAM.SFO on  \"{}\" ".format(os.path.join(games_dir, game_dir)))

    try:
        with open(os.path.join(base_dir, 'games.yml'), "r") as f:
            games_yml = yaml.load(f)
    except FileNotFoundError:
        games_yml = {}

    for key in games_yml.keys():
        tid = get_title_id(games_yml[key])
        if tid is not None:
            game_ids.append(tid)
        else:
            print("warning: Couldn't find PARAM.SFO on  \"{}\" ".format(games_yml[key]))

    print("Found game ids: {}".format(game_ids))
    print("Starting downloads...")

    downloads_path = os.path.join(base_dir, "game_updates")

    if not os.path.isdir(downloads_path):
        os.mkdir(downloads_path)

    cert_path = os.path.join(base_dir, "dev_flash", "data", "cert", "CA05.cer")

    if not os.path.isfile(cert_path):
        cert_path = False
        print("Couldn't find certificates on RPCS3 folder, going to ignore SSL."
              "To fix this just follow the rpcs3 quickstart guide")

    for title_dir in game_ids:
        download_updates(title_dir, base_dir, cert_path)
