from argparse import Namespace
from typing import TextIO

import numpy as np
import cv2 as cv
import json

FONT_SCALE = 0.5


class Metadata:
    
    def new_pos(self, current_pos: tuple[int, int]) -> None:
        self.speed = np.sqrt(
            (self.previous_pos[0] - self.current_pos[0])**2 + 
            (self.previous_pos[1] - self.current_pos[1])**2
        )
        self.traveled_distance += self.speed
        self.previous_pos = current_pos


    def write_on_frame(self, frame: np.array) -> None:
        # Show the frames spent in each region
        cv.putText(
            frame,
            'Frames Counter',
            (500, 40), cv.FONT_HERSHEY_SIMPLEX,
            FONT_SCALE, (255, 255, 255), lineType=cv.LINE_AA
        )

        for idx, (region, counter) in enumerate(self.rois_counter.items()):
            cv.putText(
                frame,
                f'{region}: {counter}',
                (500, 40 * idx + 80), cv.FONT_HERSHEY_SIMPLEX,
                FONT_SCALE, (255, 255, 255), lineType=cv.LINE_AA
            )

        # Show the entries counters 
        cv.putText(
            frame,
            'Entries Counter',
            (40, 40), cv.FONT_HERSHEY_SIMPLEX,
            FONT_SCALE, (255, 255, 255), lineType=cv.LINE_AA
        )

        for idx, entry in enumerate(self.entires_counter):
            cv.putText(
                frame,
                f'{entry}: {self.entires_counter[entry]}',
                (40, 40 * idx + 80), cv.FONT_HERSHEY_SIMPLEX,
                FONT_SCALE, (255, 255, 255), lineType=cv.LINE_AA
            )

    
    def dump(self, file: TextIO, fps: float) -> None:
        stats = {
            'traveled_distance': self.traveled_distance,
            'time_in_regions': {
                region: self.rois_counter[region] * (1/float(fps)) 
                for region in self.rois_counter
            },
            'entries': {
                region: self.entires_counter[region] 
                for region in self.entires_counter
            }
        }

        json.dump(stats, file, indent=4)

class MetadataOF(Metadata):

    def __init__(self) -> None:
        # Counter for each selected region    
        self.rois_counter = { 'center': 0, 'borders': 0}
        self.entires_counter = self.rois_counter.copy()

        # Varibles fo tracking the mice's position
        self.previous_pos = (0, 0)
        self.current_pos = (0, 0)

        self.previous_zone = 'center'
        self.current_zone = 'center'

        self.traveled_distance = 0

    
    def define_rois(self, args: Namespace, frame: np.array) -> dict:
        # Manual definition of the ROIs
        rois_file = f'{args.video.split(".")[0]}.json'
        if args.draw_rois: 
            print('Draw the center ROI!')

            roi_win = 'ROI Selection'
            cv.namedWindow(roi_win, cv.WINDOW_KEEPRATIO)
            cv.resizeWindow(roi_win, 1438, 896)

            roi = cv.selectROI(roi_win, frame, False, True)
            cv.destroyWindow(roi_win)
            
            rois = { 'center': list(roi) }

            print(f'Selected ROI: {rois}\nSaved to file: {rois_file}')
            json.dump(rois, open(rois_file, 'w'), indent=2)
            
        else:
            print(f'Loading ROIs from file: {rois_file}')

            rois = json.load(open(rois_file, 'r'))

        self.rois = rois
    

    def increment_region(self, region: str) -> None:

        self.rois_counter[region] += 1
                
        # Conting the entires
        self.current_zone = region

        if self.previous_zone == 'borders' and self.speed > 1:
            self.entires_counter[region] += 1

        elif self.previous_zone == 'center' and self.speed > 1:
            self.entires_counter['borders'] += 1

        self.previous_zone = region


class MetadataEPM(Metadata):

    def __init__(self) -> None:
        # Counter for each selected region    
        self.rois_counter = {
            'top': 0,
            'bottom': 0,
            'right': 0,
            'left': 0,
            'center': 0      
        }
        self.entires_counter = self.rois_counter.copy()

        # Varibles fo tracking the mice's position
        self.previous_pos = (0, 0)
        self.current_pos = (0, 0)

        self.previous_zone = 'center'
        self.current_zone = 'center'

        self.traveled_distance = 0


    def define_rois(self, args: Namespace, frame: np.array) -> dict:
        # Manual definition of the ROIs
        rois_file = f'{args.video.split(".")[0]}.json'
        if args.draw_rois: 
            print('Draw the ROIs on the following order: top, bottom, right, left, center!')

            roi_win = 'ROI Selection'
            cv.namedWindow(roi_win, cv.WINDOW_KEEPRATIO)
            cv.resizeWindow(roi_win, 1438, 896)

            rois = cv.selectROIs(roi_win, frame, False)
            cv.destroyWindow(roi_win)

            rois = { 
                label: roi.tolist()
                for label, roi in zip(
                    ['top', 'bottom', 'right', 'left', 'center'], 
                    rois
                )
            }

            print(f'Selected ROIs: {rois}\nSaved to file: {rois_file}')
            json.dump(rois, open(rois_file, 'w'), indent=2)
            
        else:
            print(f'Loading ROIs from file: {rois_file}')

            rois = json.load(open(rois_file, 'r'))

        self.rois = rois


    def increment_region(self, region: str) -> None:
        
        self.rois_counter[region] += 1
                
        # Conting the entires in each arm of the maze
        self.current_zone = region
        if self.previous_zone == 'center' and self.current_zone != 'center' and self.speed > 1:
            self.entires_counter[region] += 1

        self.previous_zone = region
