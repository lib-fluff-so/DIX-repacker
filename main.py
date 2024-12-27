import glob
import math
from operator import itemgetter
import PIL.Image
import xmltodict
import json
import shutil
import os
from colorama import init as colorama_init
from colorama import Back
from colorama import Style
from colorama import Fore
import PIL
import time
import art

start_time = time.time()

PIL.Image.MAX_IMAGE_PIXELS = None

settings = {"folder": "images", "newFolder": "imagesNew",
            "charactersFolder": "characters", "newCharactersFolder": "charactersNew", "spriteSheetWidth": 10}
folder = settings["folder"]
newFolder = settings["newFolder"]
charactersFolder = settings["charactersFolder"]
newCharactersFolder = settings["newCharactersFolder"]
spriteSheetWidth = settings["spriteSheetWidth"]


def print_info(text: str, new_line_after: bool = False):
    for i in text.splitlines():
        print(Back.GREEN + " " + Style.RESET_ALL + " " + i)
    if new_line_after:
        print("")


def print_warn(text: str, new_line_after: bool = False):
    for i in text.splitlines():
        print(Back.YELLOW + " " + Style.RESET_ALL + " " + i)
    if new_line_after:
        print("")


colorama_init()
# print_info(f"{Style.BRIGHT}Settings:")
# print_info(json.dumps(settings, indent=4))
art.tprint("DIX-repacker", font="tarty3")
print("")
print_info("Starting", True)

print_info("Copying...")
if os.path.isdir(newFolder):
    print_warn("Q: The new folder is already exists! What to do with this?\n"
               "1: Remove, 2: Override")
    answer = input()
    if answer == "1":
        print_warn("Removing old folder!")
    shutil.rmtree(newFolder)
shutil.copytree(folder, newFolder)
print_info("Copied!")

print_info("Copying...")
if os.path.isdir(newCharactersFolder):
    print_warn("Q: The new characters folder is already exists! What to do with this?\n"
               "1: Remove, 2: Override")
    answer = input()
    if answer == "1":
        print_warn("Removing old folder!")
    shutil.rmtree(newCharactersFolder)
shutil.copytree(charactersFolder, newCharactersFolder)
print_info("Copied!")

print("\033c", end="")

for addresso, dirs, files in os.walk(newCharactersFolder):
    for name in files:
        splitext = os.path.splitext(name)
        if splitext[1] == ".json":
            print_info(f"Using {splitext[0]}")
            print_info(f"Doing to array")

            file2 = open(os.path.join(addresso, name), "r")
            content2 = file2.readlines()
            dicto = json.loads("".join(content2))
            splitext = (dicto["image"], ".xml")
            address = newFolder
            scale = dicto["scale"]

            if os.path.isfile(os.path.join(address, splitext[0]) + "-texture.json"):
                print("\033c", end="")
                print_warn("Looks like file was already processed before. Skipping.")
                time.sleep(0.1)
                print("")
                print("\033c", end="")
                continue

            file = open(os.path.join(newFolder, dicto["image"]) + ".xml", "r")
            print_info("Found corresponding image")
            print_info("Doing to array")
            content = file.readlines()
            dicti = xmltodict.parse("".join(content))

            print_info("Making sprite sheet image and making JSON.")
            mostWidth = max(dicti["TextureAtlas"]["SubTexture"], key=itemgetter("@width"))
            mostWidthNumber = int(mostWidth["@width"])
            mostHeight = max(dicti["TextureAtlas"]["SubTexture"], key=itemgetter("@height"))
            mostHeightNumber = int(mostHeight["@height"])
            blocks = dicti["TextureAtlas"]["SubTexture"]
            temp = set()
            result = []
            for d in blocks:
                if "@frameX" in d:
                    xy = (d["@x"] + d["@frameX"], d["@y"] + d["@frameY"])
                else:
                    xy = (d["@x"], d["@y"])
                if xy not in temp:
                    temp.add(xy)
                    result.append(d)
            blocksOld = blocks
            blocks = result
            blocksLen = len(blocks)
            width = int(mostWidthNumber * (spriteSheetWidth - 1) * scale)
            height = int(mostHeightNumber * math.ceil(blocksLen / spriteSheetWidth + 1) * scale)
            image = PIL.Image.new("RGBA", (width, height), "#ffffff00")
            oldSpriteSheet = PIL.Image.open(os.path.join(address, splitext[0] + ".png"))
            cw = 1
            ch = 0
            num = 1
            dic = {}
            for i in blocks:
                cw += 1
                num += 1
                if cw >= spriteSheetWidth:
                    cw = 1
                    ch += 1
                cropped = oldSpriteSheet.crop((int(i["@x"]), int(i["@y"]),
                                               int(i["@x"]) + int(i["@width"]), int(i["@y"]) + int(i["@height"])))
                cropped = cropped.resize((int(int(i["@width"]) * scale), int(int(i["@height"]) * scale)),
                                         PIL.Image.Resampling.NEAREST)
                image.paste(cropped, (int((cw - 1) * mostWidthNumber * scale),
                                      int(ch * mostHeightNumber * scale)))
                if "@rotated" not in i: i["@rotated"] = False
                if i["@rotated"] == "true": i["@rotated"] = True
                if i["@rotated"] == "false": i["@rotated"] = False
                blocks[blocks.index(i)]["rotated"] = i["@rotated"]
                rotated = blocks[blocks.index(i)]["rotated"]
                if i["@name"].split("0", 1)[0] in dic:
                    dic[i["@name"].split("0", 1)[0]][int(i["@name"].split("0", 1)[1])] = \
                        {"name": int(i["@name"].split("0", 1)[1]), "x": cw, "y": ch, "num": num, "rotated": rotated}
                else:
                    dic[i["@name"].split("0", 1)[0]] = {}
                    dic[i["@name"].split("0", 1)[0]][int(i["@name"].split("0", 1)[1])] = \
                        {"name": int(i["@name"].split("0", 1)[1]), "x": cw, "y": ch, "num": num, "rotated": rotated}
                blocks[blocks.index(i)]["cw"] = cw
                blocks[blocks.index(i)]["ch"] = ch
                blocks[blocks.index(i)]["num"] = num
            image.save(os.path.join(address, splitext[0]) + ".png")
            for i in blocksOld:
                if i not in blocks:
                    for j in blocks:
                        if j["@x"] == i["@x"] and j["@y"] == i["@y"]:
                            for k, v in dic.items():
                                if k == j["@name"].split("0", 1)[0]:
                                    if i["@name"].split("0", 1)[0] in dic:
                                        cw, ch = blocks[blocks.index(j)]["cw"], blocks[blocks.index(j)]["ch"]
                                        num = blocks[blocks.index(j)]["num"]
                                        rotated = blocks[blocks.index(j)]["rotated"]
                                        dic[i["@name"].split("0", 1)[0]][int(i["@name"].split("0", 1)[1])] = \
                                            {"name": int(i["@name"].split("0", 1)[1]), "x": cw, "y": ch, "num": num,
                                             "rotated": rotated}
                                    else:
                                        dic[i["@name"].split("0", 1)[0]] = {}
                                        cw, ch = blocks[blocks.index(j)]["cw"], blocks[blocks.index(j)]["ch"]
                                        num = blocks[blocks.index(j)]["num"]
                                        rotated = blocks[blocks.index(j)]["rotated"]
                                        dic[i["@name"].split("0", 1)[0]][int(i["@name"].split("0", 1)[1])] = \
                                            {"name": int(i["@name"].split("0", 1)[1]), "x": cw, "y": ch, "num": num,
                                             "rotated": rotated}
                                    break

            for k, v in dic.items():
                dic[k]["countOfFrames"] = max(v.keys())
            animationList = {"width": mostWidthNumber, "height": mostHeightNumber, "animations": dic, "countOfFrames":
                             round(image.width / (mostWidthNumber * scale)) * round(image.height /
                                  (mostHeightNumber * scale))}
            dumps = json.dumps(animationList, indent=4)
            jsonify = open(os.path.join(address, splitext[0]) + "-texture.json", "w+")
            jsonify.write(dumps)

            print_info("Done!")
            jsonify.close()
            file.close()
            print("")
            print("\033c", end="")

for address, dirs, files in os.walk(newFolder):
    for name in files:
        splitext = os.path.splitext(name)
        if splitext[1] == ".xml":
            if os.path.isfile(os.path.join(address, splitext[0] + "-texture.json")):
                print("\033c", end="")
                print_warn("Looks like file was already processed before. Skipping.")
                time.sleep(0.1)
                print("")
                print("\033c", end="")
                continue

            print_info(f"Using {splitext[0]}")
            print_info(f"Doing to array")
            file = open(os.path.join(address, name), "r")
            content = file.readlines()
            dicti = xmltodict.parse("".join(content))

            print_info("Making sprite sheet image and making JSON.")
            mostWidth = max(dicti["TextureAtlas"]["SubTexture"], key=itemgetter("@width"))
            mostWidthNumber = int(mostWidth["@width"])
            mostHeight = max(dicti["TextureAtlas"]["SubTexture"], key=itemgetter("@height"))
            mostHeightNumber = int(mostHeight["@height"])
            blocks = dicti["TextureAtlas"]["SubTexture"]
            temp = set()
            result = []
            for d in blocks:
                if "@frameX" in d:
                    xy = (d["@x"] + d["@frameX"], d["@y"] + d["@frameY"])
                else:
                    xy = (d["@x"], d["@y"])
                if xy not in temp:
                    temp.add(xy)
                    result.append(d)
            blocksOld = blocks
            blocks = result
            blocksLen = len(blocks)
            width = int(mostWidthNumber * (spriteSheetWidth - 1))
            height = int(mostHeightNumber * math.ceil(blocksLen / spriteSheetWidth + 1))
            image = PIL.Image.new("RGBA", (width, height), "#ffffff00")
            oldSpriteSheet = PIL.Image.open(os.path.join(address, splitext[0] + ".png"))
            cw = 1
            ch = 1
            num = 1
            dic = {}
            for i in blocks:
                cw += 1
                num += 1
                if cw >= spriteSheetWidth:
                    cw = 1
                    ch += 1
                cropped = oldSpriteSheet.crop((int(i["@x"]), int(i["@y"]),
                                               int(i["@x"]) + int(i["@width"]), int(i["@y"]) + int(i["@height"])))
                cropped = cropped.resize((int(int(i["@width"])), int(int(i["@height"]))),
                                         PIL.Image.Resampling.NEAREST)
                image.paste(cropped, (int((cw - 1) * mostWidthNumber),
                                      int((ch - 1) * mostHeightNumber)))
                if "@rotated" not in i: i["@rotated"] = False
                if i["@rotated"] == "true": i["@rotated"] = True
                if i["@rotated"] == "false": i["@rotated"] = False
                blocks[blocks.index(i)]["rotated"] = i["@rotated"]
                rotated = blocks[blocks.index(i)]["rotated"]
                if i["@name"].split("0", 1)[0] in dic:
                    dic[i["@name"].split("0", 1)[0]][int(i["@name"].split("0", 1)[1])] = \
                        {"name": int(i["@name"].split("0", 1)[1]), "x": cw, "y": ch, "num": num, "rotated": rotated}
                else:
                    dic[i["@name"].split("0", 1)[0]] = {}
                    dic[i["@name"].split("0", 1)[0]][int(i["@name"].split("0", 1)[1])] = \
                        {"name": int(i["@name"].split("0", 1)[1]), "x": cw, "y": ch, "num": num, "rotated": rotated}
                blocks[blocks.index(i)]["cw"] = cw
                blocks[blocks.index(i)]["ch"] = ch
                blocks[blocks.index(i)]["num"] = num
                print(i)
            image.save(os.path.join(address, splitext[0]) + ".png")
            for i in blocksOld:
                if i not in blocks:
                    for j in blocks:
                        if j["@x"] == i["@x"] and j["@y"] == i["@y"]:
                            for k, v in dic.items():
                                if k == j["@name"].split("0", 1)[0]:
                                    if i["@name"].split("0", 1)[0] in dic:
                                        cw, ch = blocks[blocks.index(j)]["cw"], blocks[blocks.index(j)]["ch"]
                                        num = blocks[blocks.index(j)]["num"]
                                        rotated = blocks[blocks.index(j)]["rotated"]
                                        dic[i["@name"].split("0", 1)[0]][int(i["@name"].split("0", 1)[1])] = \
                                            {"name": int(i["@name"].split("0", 1)[1]), "x": cw, "y": ch, "num": num,
                                             "rotated": rotated}
                                    else:
                                        dic[i["@name"].split("0", 1)[0]] = {}
                                        cw, ch = blocks[blocks.index(j)]["cw"], blocks[blocks.index(j)]["ch"]
                                        num = blocks[blocks.index(j)]["num"]
                                        rotated = blocks[blocks.index(j)]["rotated"]
                                        dic[i["@name"].split("0", 1)[0]][int(i["@name"].split("0", 1)[1])] = \
                                            {"name": int(i["@name"].split("0", 1)[1]), "x": cw, "y": ch, "num": num,
                                             "rotated": rotated}
                                    break

            for k, v in dic.items():
                dic[k]["countOfFrames"] = max(v.keys())

            animationList = {"width": mostWidthNumber, "height": mostHeightNumber, "animations": dic, "countOfFrames":
                             round(image.width / mostWidthNumber) * round(image.height / mostHeightNumber)}
            dumps = json.dumps(animationList, indent=4)
            jsonify = open(os.path.join(address, splitext[0]) + "-texture.json", "w+")
            jsonify.write(dumps)

            print_info("Done!")
            jsonify.close()
            file.close()
            print("")
            print("\033c", end="")

print_info("Removing XMLs")
newFolderFiles = glob.glob(os.path.join(newFolder, "**/*.xml"), recursive=True)
for i in newFolderFiles:
    os.remove(i)

print_info("All done in %s seconds!" % (time.time() - start_time), True)
art.tprint("Done!", font="tarty3")
