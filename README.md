# Project PCA

![projPca](./readme_imgs/main.gif)

This project **was developed and tested for Ubuntu 16.04 and 18.04.**

## Requirements

This section is a guide to the instalations of a python enviroment with the requirements of this repository.

First install [Anaconda](https://www.anaconda.com/distribution/) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html), both of them give you similar results but the latter requires less disk space.

Now create a python virtual environment and install the required packages following the commands. Substitute **<environment_name>** with a name for your environment

```console
user@computer:~$ conda create -n <enviroment_name> anaconda python=3
user@computer:~$ conda activate <enviroment_name>
(<enviroment_name>) user@computer:~$ conda install -c loopbio -c conda-forge -c pkgw-forge ffmpeg gtk2 opencv numpy 
```

## Using the script

To use the provided scripts make sure to activate your python enviroment, that can be acomplished by:

```console
user@computer:~$ conda activate <enviroment_name>
```

### [PCA Analyser](./pcaAnalyser.py)

This script aims to track and detect the gaze direction of mice in neuroscience experiments, a window contaning the results will be displayed. Usage:

```console
(<enviroment_name>) user@computer:~/proj-pca$ python pcaAnalyser.py [-h] [--color-mask] [--both-axis] [--show-mask] [--save-video] video bg_image
```

Optional arguments:

* *-h*, *--help*: Show a help message and exit
* *--color-mask*: Draw a colored mask over the detection.
* *--both-axis*: Draw both PCA axis.
* *--show-mask*: Displays a windows with the segmented mask.
* *--save-video*: Create a video file with the analysis result.

Positional arguments:

* *video*: Path to the file file to be processed.
* *bg_image*: Path to the background image of the scene.

### [Tracker](./tracker.py)

This script aims to track mice throughout a neuroscience experiment detecting when the mice is present in a previously selected region. Usage:

```console
(<enviroment_name>) user@computer:~/proj-pca$ python tracker.py [-h] [--draw-axis] [--save-video] [--color-mask] video bg_image
```

Optional arguments:

* *-h*, *--help*: Show a help message and exit
* *--draw-axis*: Draw both PCA axis.
* *--color-mask*: Draw a colored mask over the detection.
* *--save-video*: Create a video file with the analysis result.

Positional arguments:

* *video*: Path to the file file to be processed.
* *bg_image*: Path to the background image of the scene.

![tracker_GIF](./readme_imgs/tracker.gif)
