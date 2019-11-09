# Mice Tracking and Detection of Head Direction Using Principal Component Analysis (PCA)

![projPca](./readme_imgs/pca.png)

This project **was developed and tested for Ubuntu 16.04 and 18.04.**

To use the provided tools, the first step is to clone this repository, which can be can be accomplished by:

```console
user@computer:~$ git clone https://github.com/vanluwin/proj-pca.git
```

## Requirements

### Python enviroment

This section is a guide to the installations of a python environment with the requirements of this repository.

First, install [Anaconda](https://www.anaconda.com/distribution/) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html), both of them give you similar results, but the latter requires less disk space.

Now, create a python virtual environment and install the required packages following the commands. Substitute **<environment_name>** with a name for your environment

#### On Linux Distributions

Open your terminal and execute the following commands:

```console
user@computer:~$ conda create -n <enviroment_name> anaconda python=3
user@computer:~$ conda activate <enviroment_name> || source activate <enviroment_name>
(<enviroment_name>) user@computer:~$ conda install -c loopbio -c conda-forge -c pkgw-forge ffmpeg gtk2 numpy==1.16.3 opencv==3.4.3 matplotlib scipy pyserial
```

#### On Windows

Open your anaconda command prompt and execute the following commands:  

```console
C:\Users\your-user> conda create -n <enviroment_name> anaconda python=3
C:\Users\your-user> conda activate <enviroment_name> || source activate <enviroment_name>
(<enviroment_name>) C:\Users\your-user> conda install -c loopbio -c conda-forge -c pkgw-forge ffmpeg numpy==1.16.3 opencv==3.4.3 matplotlib scipy pyserial
```

## The scripts

To use the provided scripts, first make sure to activate your python environment:

### On Linux Distributions

On your terminal, execute the following command:

```console
user@computer:~$ conda activate <enviroment_name>
```

### On Windows

On your anaconda command prompt, execute the following command:  

```console
C:\Users\your-user> conda activate <enviroment_name>
```

### [PCA Analyser](./pcaAnalyser.py)

![pcaGif](./readme_imgs/pca.gif)

This script aims to track the mice and detect the head direction during behavioral neuroscience experiments. For testing, use the following suggested commands:

```console
(<enviroment_name>) user@computer:~/proj-pca$ python pcaAnalyser.py [-h] [--color-mask] [--both-axis] [--show-mask] [--save-video] video
```

**Required arguments**:

* *video*: Path to the video file to be processed.

**Optional arguments**:

* *-h*, *--help*: Show a help message and exit.
* *--color-mask*: Draw a colored mask over the detection.
* *--both-axis*: Draw both PCA axis.
* *--show-mask*: Displays a window with the segmented mask.
* *--save-video*: Create a video file with the analysis result.

### [Tracker](./tracker.py)

![tracker_GIF](./readme_imgs/tracker.gif)

This script aims to track mice throughout a neuroscience experiment detecting when the mice is present in a previously selected region. Usage:

```console
(<enviroment_name>) user@computer:~/proj-pca$ python tracker.py [-h] [--draw-axis] [--save-video] [--color-mask] video
```

**Required arguments**:

* *video*: Path to the video file to be processed.

**Optional arguments**:

* *-h*, *--help*: Show a help message and exit.
* *--draw-axis*: Draw both PCA axis.
* *--color-mask*: Draw a colored mask over the detection.
* *--save-video*: Create a video file with the analysis results.
* *--log-position*: Creates a text file with the (x, y) position of the tracked mice.

### [Tracker with Arduino integration](./trackerArduino.py)

![trackerArduino](./readme_imgs/trackerArduino.gif)

This script is an integration of the tracking system with Arduino-based development boards, enabling experiments with real-time decisions like the control of a laser simulated by the blue led in the gif above.

To utilize the script first, upload the [Arduino file](./trackerArduinoFile.ino) to your microcontroller and make sure that the serial communication is working. Then, in your terminal, run the following command:

```console
(<enviroment_name>) user@computer:~/proj-pca$ python trackerArduino.py [-h] [--draw-axis] [--save-video] [--color-mask] [--log-position] video
```

**Required arguments**:

* *video*: Path to the video file to be processed.

**Optional arguments**:

* *-h*, *--help*: Show a help message and exit.
* *--draw-axis*: Draw both PCA axis.
* *--color-mask*: Draw a colored mask over the detection.
* *--save-video*: Create a video file with the analysis results.
* *--log-position*: Creates a text file with the (x, y) position of the tracked mice.

### [Detections Analyser](./detectionsAnalyser.py)

![detectionsAnalyser](./readme_imgs/detectionsAnalyser.png)

This script is intended to manually correct errors in detections that have already been made and can be edited, a window containing the instructions will be displayed. Pause and press *d* to edit the detections of the current frame. Usage:

```console
(<enviroment_name>) user@computer:~/proj-pca$ python detectionsAnalyser.py video log_file
```

Avalible commands:

* *space* - Pause the video stream
* *q*, *esc* - Finish the execution
* *s* - Increases the delay between each video frame
* *f* - Decreases the delay between each video frame
* *d* - Opens a new window where the user is able to select a new point by drawing a rectangle with the disered point in its cente, to finish the selection press *enter*, press *c* to clean the selection.

### [Heatmap Plot](./heatmapPlot.py)

![heatmapPlot](./readme_imgs/heatmap.png)

This scripts takes as input a detection log file and procuces a heatmap plot, a window containg the plot will be displayed. Usage:

```console
(<enviroment_name>) user@computer:~/proj-pca$ python heatmapPlot.py log_file frameWidth frameHeight
```

**Required arguments**:

* *log_file*: Path to the log file file to be processed.
* *frameWidth*: Frame width of the processed video.
* *frameHeight*: Frame height of the processed video.

## Any questions?

Feel free to contact me at richardsonsantiago@ufrn.edu.br
