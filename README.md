# MusicSync
**MusicSync** is a cross-platform tool that **synchronizes your music library** between devices and drives with **advanced settings**.

You can use it through **CLI**, that makes easy to sync you library with only a click using a script, or through **GUI**, that is more user-friendly. Here there are two examples:

```shell
python musicsync D:/Music sdcard/Music --adb --min-rating 4.5 --output-format opus --output-bitrate 128k
python musicsync D:/Music sdcard/Music --adb --min-rating 3 --min-year 2020 --output-format opus --output-bitrate 128k
```

![MusicSync GUI Preview](https://user-images.githubusercontent.com/49209517/120080459-85fe3400-c0a8-11eb-8771-a260f6ccc351.png)

## Transfer protocols
MusicSync supports two transfer protocols:
* **Mass Storage Class (MSC)**, that is the standard protocol used by flash drives, hard drives, SD cards, etc.;
* **Android Debug Bridge (ADB)**, that is used by Android devices.

More practically, select ADB only if you want to sync your library with an Android device, otherwise select MSC.
If you want to know more about the reason why Android devices don’t support MSC, check out [this article](https://www.howtogeek.com/192732/android-usb-connections-explained-mtp-ptp-and-usb-mass-storage).

## Format conversion
Although currently MusicSync can use filters only with MP3 and FLAC input files, you can specify **every output format and bitrate supported by ffmpeg**. You can see che format supported by ffmpeg [here](http://www.ffmpeg.org/general.html#File-Formats).

## Filters
Using the following filters, you can select very precisely which songs to sync and which not. Remember that, like in the CLI example above, you can run the program multiple times to have more control. The filters are based on:
* **Artists**;
* **Genres**;
* **Minimum rating**;
* **Maximum rating**;
* **Minimum year**;
* **Maximum year**.

## Requirements
- [**Python**](https://www.python.org/downloads);
- [**ADB**](https://www.xda-developers.com/install-adb-windows-macos-linux) correctly [added to the PATH system variable](https://www.xda-developers.com/adb-fastboot-any-directory-windows-linux);
- [**ffmpeg**](https://ffmpeg.org/download.html) correctly [added to the PATH system variable](hhttps://www.thewindowsclub.com/how-to-install-ffmpeg-on-windows-10);
- **mutagen, pydub and PySide2** (Python libreries), installable running the following command in MusicSync main folder:
	```shell
	pip install -r requirements.txt
	```
