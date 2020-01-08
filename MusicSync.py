import argparse
import os
import shutil
import eyed3

def sync(src, dest, filter):
    if not (os.path.isdir(src)):
        raise Exception("The source directory doesn't exist.")
    if not (os.path.isdir(dest)):
        os.makedirs(dest)
    addedSongsCount = 0
    for root, subdirs, files in os.walk(src):
        for file in files:
            if (file.lower().endswith((".mp3", ".aac", ".ogg", ".flac", ".wav"))):
                songPathDest = os.path.join(dest, os.path.relpath(os.path.join(root, file), src))
                dirPathDest = os.path.dirname(songPathDest)
                if not (filter(os.path.join(root, file))):
                    continue
                if (os.path.isfile(songPathDest)):
                    print(songPathDest + " already exists.")
                    continue
                if not (os.path.isdir(dirPathDest)):
                    os.makedirs(dirPathDest)
                shutil.copy2(os.path.join(root, file), dirPathDest)
                print(songPathDest + " copied.")
                addedSongsCount += 1
    print("Added", addedSongsCount, "songs.")

def ratingFilter(file, minimumRating):
    loadedFile = eyed3.load(file)
    if not (loadedFile):
        print(file, "rating not loaded.")
        return False
    for popm in loadedFile.tag.popularities:
        if popm.rating >= minimumRating:
            return True
    return False

def main():
    parser = argparse.ArgumentParser(description="Sync music automatically. You can use a filter to select the songs to copy.")
    parser.add_argument("src", metavar="SOURCE", type=str, help="the music source directory")
    parser.add_argument("dest", metavar="DESTINATION", type=str, help="the music destination directory")
    rating = parser.add_mutually_exclusive_group(required=False)
    rating.add_argument("-r", metavar="MINIMUM_RATING", action="store", dest="minimumRating", type=int, help="set up minimum rating of the songs (1-255)")
    rating.add_argument("-s", metavar="MINIMUM_STARS_RATING", action="store", dest="minimumStarsRating", type=int, help="set up minimum stars rating of the songs (1-5)")
    args = parser.parse_args()
    try:
        if (args.minimumRating):
            eyed3.log.setLevel("ERROR")
            sync(args.src, args.dest, lambda file : ratingFilter(file, args.minimumRating))
        elif (args.minimumStarsRating):
            eyed3.log.setLevel("ERROR")
            if (args.minimumStarsRating < 1 or args.minimumStarsRating > 5):
                parser.error("The minimum stars rating value must be between 1 and 5.")
            starsToRating = [1, 32, 96, 160, 224] #Windows Explorer standards (https://en.wikipedia.org/wiki/ID3#ID3v2_rating_tag_issue)
            sync(args.src, args.dest, lambda file : ratingFilter(file, starsToRating[args.minimumStarsRating - 1]))
        else:
            sync(args.src, args.dest, lambda file : True)
    except Exception as exc:
        print(exc.args)

if (__name__ == "__main__"):
    main()
