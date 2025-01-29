<div align="center">
  <img src="./resources/icon.png" alt="PDA Logo" width="200"/>
  <h1>Particle Distortion Analysis (PDA)</h1>
</div>

## Overview
Particle Distortion Analysis (PDA) is software for the analysis of microaspiration (or ion pipette aspiration) data.
The source code, along with instructions, documentation and a Windows executable, is available on Github at [github.com/HaigBishop/particle-distortion-analysis](https://github.com/HaigBishop/particle-distortion-analysis)

## Dependencies
#### Python 3.13.1
#### Packages (Conda)
- kivy (2.3.1)
- opencv (4.10.0)
- numpy (2.2.2)
- scipy (1.15.1)
- moviepy (1.0.3)
- plyer (2.1.0)
- pywin32 (307)
- pandas (2.2.3)
#### Packages (Pip)
- nptdms (1.9.0)

## Installation
1. Run using python in a conda environment
```
conda create -n pda_env python=3.13 -y
conda activate pda_env
conda install -c conda-forge kivy opencv numpy scipy moviepy plyer pywin32 pandas -y
pip install nptdms
git clone https://github.com/HaigBishop/particle-distortion-analysis.git
cd particle-distortion-analysis
python particle-distortion-analysis.py
```
2. Run using the Windows executable
(Look for the .exe file in the lastest release on the [Github page](https://github.com/HaigBishop/particle-distortion-analysis/releases))

## Background/Theory
The purpose of this software is to select events from a microaspiration experiment and track the distortions. 

An experiment is a video of a microaspiration experiment which may be several minutes long and may contain any number of events. Electrical data is also often recorded during an experiment. This electrical signal (likely as a .tdms files) can be imported and synced with the video.

Events are when a particle is aspirated into the pipette tip, therefore the selection of events is simply selecting the range of frames in an experiment where the particle is aspirated. The first frame of an event is assumed to have 0 distortion, meaning the particle is a perfect circle.

Distortions are when the particle is deformed by the pipette tip as they are aspirated (see figure below). In the first frame of an event, the particle is a perfect circle, so dL (see figure) is 0. As the particle is aspirated, it is deformed by the pipette tip, and dL increases. 

After tracking the distortion, the software allows for the export of the data for all events as CSV files. Most importantly, the CSV file contains a dL column (in units of pixels). This data can be automatically stored in a  JSON file for each experiment, which holds both the electrical signal and distortion data.

<div align="left">
  <img src="./resources/masp_diagram.png" alt="microaspiration theory diagram" width="300"/>
</div>

## Usage

### Keyboard and Mouse Controls

#### Event Selection Keyboard Controls and Mouse Controls

##### Keyboard Controls
- **S**: 
  - *Add Start*: If ready for start.
  - *Add Stop*: If not ready for start.
- **R**: Remove the current event if the slider is on an event.
- **Left Arrow / A**: Scroll left or adjust ion data to the left.
- **Right Arrow / D**: Scroll right or adjust ion data to the right.
- **+ / =**: Zoom in or adjust ion data to zoom in.
- **-**: Zoom out or adjust ion data to zoom out.
- **0**: Reset zoom or reset ion data alignment.

##### Mouse Controls
- **Left Click**: Set the current frame based on the click position on the thumbnail bar.
- **Scroll Up**:
  - *Zoom Out*: If not adjusting ion data.
  - *Adjust Ion Data In*: If adjusting ion data.
- **Scroll Down**:
  - *Zoom In*: If not adjusting ion data.
  - *Adjust Ion Data Out*: If adjusting ion data.
- **Scroll Left**: Scroll the view to the left.
- **Scroll Right**: Scroll the view to the right.

#### Distortion Detection Keyboard Controls and Mouse Controls

##### Keyboard Controls
- **Z**: Zoom into the particle.
- **X**: Hide lines and circles.
- **Up Arrow / W**: 
  - *Shift + Up*: Move pipette tip up.
  - *Up*: Move circle up.
- **Down Arrow / S**:
  - *Shift + Down*: Move pipette tip down.
  - *Down*: Move circle down.
- **Left Arrow / A**:
  - *Shift + Left*: Tilt pipette tip left.
  - *Left*: Move circle left.
- **Right Arrow / D**:
  - *Shift + Right*: Tilt pipette tip right.
  - *Right*: Move circle right.

##### Mouse Controls
- **Left Click**: Move the particle to the clicked position within the image.
- **Scroll Up**: Increase the particle radius.
- **Scroll Down**: Decrease the particle radius.

#### Distortion Tracking Keyboard Controls and Mouse Controls

##### Keyboard Controls
- **Z**: Zoom into the distortion area.
- **X**: Hide distortion overlays.
- **S**: 
  - *Add Start*: If ready for start.
  - *Add Stop*: If not ready for start.
- **R**: Remove the current distortion event if the slider is on an event.
- **Left Arrow / A**: Scroll left or adjust ion data to the left.
- **Right Arrow / D**: Scroll right or adjust ion data to the right.
- **Up Arrow / W**: 
  - *Shift + Up*: Move distortion tip up while maintaining non-decreasing condition.
  - *Up*: Move distortion up.
- **Down Arrow / S**:
  - *Shift + Down*: Move distortion tip down while maintaining non-decreasing condition.
  - *Down*: Move distortion down.
- **+ / =**: Zoom in or adjust ion data to zoom in.
- **-**: Zoom out or adjust ion data to zoom out.
- **0**: Reset zoom or reset ion data alignment.

##### Mouse Controls
- **Left Click**: Set the current frame based on the click position on the thumbnail bar.
- **Scroll Up**:
  - *Zoom Out*: If not adjusting ion data.
  - *Adjust Ion Data In*: If adjusting ion data.
- **Scroll Down**:
  - *Zoom In*: If not adjusting ion data.
  - *Adjust Ion Data Out*: If adjusting ion data.
- **Scroll Left**: Scroll the view to the left.
- **Scroll Right**: Scroll the view to the right.

## Files and Development Descriptions
There are several Python files which make this program, which are each described.
There are also some images, fonts, a .kv file and a .txt file.
#### Main:
  -  particle-distortion-analysis.py  -  the main file for this application
#### Tracking functions:
  -  tracking.py  -  detects and tracks the pipette, particle and distortion
#### Graphic User Interface (using Kivy)
  -  pda.kv  -  contains the GUI styling for the entire application
  -  ie1.py  -  contains the functionality for the Importing Experiments screen
  -  ie3.py  -  contains the functionality for the Selecting Events screen
  -  td1.py  -  contains the functionality for the Importing Events screen
  -  td2.py  -  contains the functionality for the Detecting Distortions screen
  -  td3.py  -  contains the functionality for the Tracking Distortions screen
  -  popup_elements  -  contains popup GUI elements
#### Other:
  -  file_management  -  contains code for dealing with files



## License

MIT License
(see LICENSE.txt)

## How to Site PCT

The only way to site PCT is to cite this Github repository:

Bishop, H. (2025). Particle Distortion Analysis (Version 0.2.10) [Computer software]. https://github.com/HaigBishop/particle-distortion-analysis

## Author and Acknowledgments

Please feel free to contact me if you have any questions, feedback, or requests
  -  Author:         Haig Bishop
  -  Email:          haig.bishop@pg.canterbury.ac.nz
  -  Organisation:   University of Canterbury, New Zealand

A big thank you to Ashley Garrill, Volker Nock, and Ayelen Tayagui at UC for supporting this project!
