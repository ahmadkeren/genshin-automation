#%% Check for new codes

import requests
from bs4 import BeautifulSoup

res = requests.get("https://www.pockettactics.com/genshin-impact/codes")
soup = BeautifulSoup(res.text, 'html.parser')

active_codes = [code.text.strip() for code in soup.find("div", {"class":"entry-content"}).find("ul").findAll("strong")]

codes_file = root / "codes.txt"
used_codes = codes_file.open().read().split("\n")
new_codes = list(filter(lambda x: x not in used_codes and x != "", active_codes))

#%% Add new codes to used codes

used_codes.extend(new_codes)
io.open(codes_file, "w", newline="\n").write("\n".join(used_codes))