#%% setup

import genshinstats as gs
import os
import re


#%% login into genshin

GAME_UID = int(os.environ.get("GAME_UID"))
gs.set_cookie(os.environ.get("COOKIE"))

#%% check in and get exp on hoyolab

try:
    gs.hoyolab_check_in()
    print("Claimed exp for hoyolab.")
except gs.SignInException as e:
    print("Exp for hoyolab was already claimed.")


#%% get data

user_info = gs.get_user_stats(GAME_UID)
characters = gs.get_characters(GAME_UID)
spiral_abys = gs.get_spiral_abyss(GAME_UID)
(daily_reward_info_is_sign, daily_reward_info_total_sign_day) = gs.get_daily_reward_info()


#%% create readme from template

import pathlib

root = pathlib.Path(__file__).parent.resolve()
readme_template = root / "README_template_v3.md"
data = readme_template.open().read()


import datetime
data = data.replace("replace_this_with_check_time", datetime.datetime.utcnow().strftime("%d.%m.%Y %H:%M:%S UTC"))

# stats filling
data = data.replace(f"replace_this_with_reward_info_total_sign_day", str(daily_reward_info_total_sign_day))
data = data.replace(f"replace_this_with_reward_info_is_sign", str(daily_reward_info_is_sign))

# exploration filling
offset = 0
while True:
    try:
        template_start_str = "replace_this_with_explorations_template_string$$$"
        start_index = data.index(template_start_str, offset)
    except ValueError as e:
        break

    try:
        end_index = data.index("$$$", start_index + len(template_start_str))
    except ValueError as e:
        print("You forgot to enclose explorations template string!")
        raise

    template_string = data[start_index + len(template_start_str): end_index]

    filled_templates = ""

    for location in user_info["explorations"]:
        filled_template = template_string
        for key, value in location.items():
            filled_template = filled_template.replace(f"replace_this_with_exploration_{key}", str(value))
        filled_templates += filled_template

    data = data.replace(template_start_str + template_string + "$$$", filled_templates)

    offset = start_index


# abys stats filling
for key, value in spiral_abys["stats"].items():
    data = data.replace(f"replace_this_with_abys_{key}", str(value))

# done any abys this seasson?
if spiral_abys["stats"]["total_battles"] != 0:
    # abys strongest hit
    for key, value in spiral_abys["character_ranks"].get("strongest_hit")[0].items():
        data = data.replace(f"replace_this_with_abys_strongest_hit_{key}", str(value))

    # abys most damage taken
    for i, character in enumerate(spiral_abys["character_ranks"].get("most_damage_taken")):
        for key, value in character.items():
            data = data.replace(f"replace_this_with_abys_most_damage_taken_nth-{i}_{key}", str(value))

    # abys most skills used
    for i, character in enumerate(spiral_abys["character_ranks"].get("most_skills_used")):
        for key, value in character.items():
            data = data.replace(f"replace_this_with_abys_most_skills_used_nth-{i}_{key}", str(value))
else:
    # replace with some data
    data = re.sub(r"replace_this_with_abys_strongest_hit_[a-z]+", "no strongest hit this seasson", data)
    data = re.sub(r"replace_this_with_abys_most_damage_taken_nth-\d_[a-z]+", "no most damage taken this seasson", data)
    data = re.sub(r"replace_this_with_abys_most_skills_used_nth-\d_[a-z]+", "no most skills used this seasson", data)


# characters
offset = 0
while True:
    try:
        template_start_str = "replace_this_with_characters_template_string$$$"
        start_index = data.index(template_start_str, offset)
    except ValueError as e:
        break

    try:
        end_index = data.index("$$$", start_index + len(template_start_str))
    except ValueError as e:
        print("You forgot to enclose characters template string!")
        raise

    template_string = data[start_index + len(template_start_str): end_index]

    filled_templates = ""

    characters.sort(key=lambda x: (int(x["rarity"]), int(x["level"]), int(x["ascension"]), int(x["constellation"]) ,int(x["friendship"])), reverse=True)

    for character in characters:
        filled_template = template_string
        for key, value in character.items():
            if key == "icon":
                filled_template = filled_template.replace(f"replace_this_with_character_image", str(value))
                filled_template = filled_template.replace(f"replace_this_with_character_icon", str(value).replace("@2x", "").replace("character_image", "character_icon"))
            elif key == "weapon":
                for key, value in value.items():
                    filled_template = filled_template.replace(f"replace_this_with_character_weapon_{key}", str(value))
            elif key == "artifacts":
                sets = [set_piece.get("set").get("name") for set_piece in value]
                sets = [f"{sets.count(x)} x {x}" for x in set(sets)]
                sets.sort(reverse=True)
                sets = "<br>".join(sets)
                filled_template = filled_template.replace("replace_this_with_character_artifact_sets", sets)
            elif key == "constellations":
                continue
            else:
                filled_template = filled_template.replace(f"replace_this_with_character_{key}", str(value))
        filled_templates += filled_template

    data = data.replace(template_start_str + template_string + "$$$", filled_templates)

    offset = start_index

# stats filling
for key, value in user_info["stats"].items():
    data = data.replace(f"replace_this_with_{key}", str(value))

readme = root / "README.md"
readme.open("w").write(data)


#%% Check for new codes

import requests
from bs4 import BeautifulSoup

res = requests.get("https://www.pockettactics.com/genshin-impact/codes")
soup = BeautifulSoup(res.text, 'html.parser')

active_codes = [code.text.strip() for code in soup.find("div", {"class":"entry-content"}).find("ul").findAll("strong")]

codes_file = root / "codes.txt"
used_codes = codes_file.open().read().split("\n")
new_codes = list(filter(lambda x: x not in used_codes, active_codes))


#%% Redeem new codes

import time

failed_codes = []
for code in new_codes[:-1]:
    try:
        gs.redeem_code(code, GAME_UID)
    except Exception as e:
        failed_codes.append(code)
    time.sleep(5.2)
if len(new_codes) != 0:
    try:
        gs.redeem_code(new_codes[-1], GAME_UID)
    except Exception as e:
        failed_codes.append(new_codes[-1])

redeemed_codes = list(filter(lambda x: x not in failed_codes, new_codes))
if len(redeemed_codes) != 0:
    print("Redeemed " + str(len(redeemed_codes)) + " new codes: " + ", ".join(redeemed_codes))


#%% Add new codes to used codes

used_codes.extend(new_codes)
codes_file.open("w").write("\n".join(used_codes))

#%%
