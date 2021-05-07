#%% setup

import genshinstats as gs
import os

#%% login into genshin

GAME_UID = int(os.environ.get("GAME_UID"))
gs.set_cookie_header(os.environ.get("COOKIE"))

#%% check in and get exp on hoyolab

try:
    gs.check_in()
    print("Claimed exp for hoyolab.")
except gs.AlreadySignedIn as e:
    print("Exp for hoyolab was already claimed.")


#%% get data

user_info = gs.get_user_info(GAME_UID)
characters = gs.get_all_characters(GAME_UID)
spiral_abys = gs.get_spiral_abyss(GAME_UID)
daily_reward_info = gs.get_daily_reward_info()


#%% create readme from template

import pathlib

root = pathlib.Path(__file__).parent.resolve()
readme_template = root / "README_template.md"
data = readme_template.open().read()


import datetime
data = data.replace("replace_this_with_check_time", datetime.datetime.utcnow().strftime("%d.%m.%Y %H:%M:%S"))

# stats filling
for key, value in daily_reward_info.items():
    data = data.replace(f"replace_this_with_reward_info_{key}", str(value))

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

    offset = end_index + 3


# abys stats filling
for key, value in spiral_abys["stats"].items():
    data = data.replace(f"replace_this_with_abys_{key}", str(value))

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

    for character in characters:
        filled_template = template_string
        for key, value in character.items():
            if key == "weapon":
                for key, value in value.items():
                    filled_template = filled_template.replace(f"replace_this_with_character_weapon_{key}", str(value))
            elif key == "artifacts":
                sets = [set_piece.get("set").get("name") for set_piece in value]
                sets = ", ".join([f"{sets.count(x)} x {x}" for x in set(sets)])
                filled_template = filled_template.replace("replace_this_with_character_artifact_sets", sets)
            else:
                filled_template = filled_template.replace(f"replace_this_with_character_{key}", str(value))
        filled_templates += filled_template

    data = data.replace(template_start_str + template_string + "$$$", filled_templates)

    offset = end_index + 3

# stats filling
for key, value in user_info["stats"].items():
    data = data.replace(f"replace_this_with_{key}", str(value))

readme = root / "README.md"
readme.open("w").write(data)

#%%
