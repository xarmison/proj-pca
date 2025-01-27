from argparse import ArgumentParser, Namespace
from ultralytics import YOLO
from typing import NoReturn
from os import path, sep
from tqdm import tqdm

import numpy as np
import cv2 as cv
import torch
import json

from metadata import MetadataOF, MetadataEPM

DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'
MODEL = 'assets/best.pt'

# Kernel for morphological operation opening
KERNEL3 = cv.getStructuringElement(
    cv.MORPH_ELLIPSE,
    (3, 3), (-1, -1)
)

KERNEL20 = cv.getStructuringElement(
    cv.MORPH_ELLIPSE,
    (5, 5), (-1, -1)
)


def parser_args() -> Namespace:

    parser = ArgumentParser(
        description='Tracks mice.'
    )

    parser.add_argument(
        'video', type=str,
        help='Path to the video file to be processed.'
    )

    parser.add_argument(
        'type', type=str, choices=['OF', 'EPM'],
        help='Type of the experiment being analyzed.'
    )

    parser.add_argument(
        '--draw-rois', action='store_true',
        help='User inputed Regions of interest.'
    )

    parser.add_argument(
        '--save-video', action='store_true',
        help='Create a video file with the analysis result.'
    )

    parser.add_argument(
        '--color-mask', action='store_true',
        help='Draw a colored mask over the detection.'
    )

    parser.add_argument(
        '--log-position', action='store_true',
        help='Logs the position of the center of mass to file.'
    )

    parser.add_argument(
        '--log-stats', action='store_true',
        help='Logs the statistics of the mice moviment.'
    )

    parser.add_argument(
        '--log-speed', action='store_true',
        help='Logs the speed of the center of mass to file.'
    )

    return parser.parse_args()


def find_mask_center(mask: np.array) -> tuple[int, int]:

    y_indices, x_indices = np.where(mask > 0.5)

    if not len(y_indices) or not len(x_indices):
        print('The mask does not contain relevant pixels!')

    return int(np.median(x_indices)), int(np.median(y_indices))


def cleanup_and_exit(cap: cv.VideoCapture, pbar: tqdm) -> NoReturn:

    print('Cleaning up and exiting...')

    cv.destroyAllWindows()
    cap.release()
    pbar.close()

    exit()


def setup(args: Namespace) -> tuple:

    out_writer = None
    if args.save_video:
        result_file_name = f'{args.video.split(sep)[-1].split(".")[0]}_result.mp4'

        out_writer = cv.VideoWriter(
            result_file_name,
            cv.VideoWriter_fourcc(*'mp4v'),
            frame_rate, (frame_width, frame_height)
        )

    # Create file for stats loging
    stats_log_file = None
    if args.log_stats:
        path, _, video_name = args.video.rpartition('/')
        stats_log_file = f'{path}/{video_name.split(".")[0]}_stats.json'

        with open(stats_log_file, 'w') as log_file:
            log_file.write('')

    # Create file for position loging
    pos_log_file = None
    if args.log_position:        
        pos_log_file = f'{path}/{video_name.split(".")[0]}_pos.csv'
        
        with open(pos_log_file, 'w') as log_file:
            log_file.write('region,x,y\n')

    # Create file for speed loging 
    speed_log_file = None
    if args.log_speed:        
        speed_log_file = f"{path}/{video_name.split('.')[0]}_speed.csv"
        
        with open(speed_log_file, 'w') as log_file:
            log_file.write('time,speed\n')

    return (
        out_writer,
        stats_log_file,
        pos_log_file,
        speed_log_file
    )


if __name__ == '__main__':

    args = parser_args()

    cap = cv.VideoCapture(args.video)

    if not cap.isOpened():
        print('Error opening video stream')
        exit()

    frame_width = int(cap.get(3)) 
    frame_height = int(cap.get(4))
    frame_rate = 30.0

    result_win = 'Tracker'
    cv.namedWindow(result_win, cv.WINDOW_KEEPRATIO)
    cv.resizeWindow(result_win, 640, 360)
    cv.moveWindow(result_win, 10, 10)

    out_writer, stats_log_file, pos_log_file, speed_log_file = setup(args)

    model = YOLO(MODEL)
    model.to(DEVICE)

    if args.type == 'OF':
        metadata = MetadataOF()    
    elif args.type == 'EPM':
        metadata = MetadataEPM()
    else:
        print(f'Invalid experiment type `{args.type}`!')
        exit()

    metadata.define_rois(args, cap.read()[1])

    frame_index = 0
    pbar = tqdm(
        total=int(cap.get(cv.CAP_PROP_FRAME_COUNT)), 
        desc='Processing frames', 
        unit='frame', leave=True
    )

    while cap.isOpened():
        ret, frame = cap.read()
        pbar.update(1)

        if not ret:
            pbar.close()
            exit()

        # Match frame dimensions to the model
        new_height = (frame_height // 32) * 32
        new_width = (frame_width // 32) * 32
        resized_frame = cv.resize(frame, (new_width, new_height))

        # Convert to tensor format BCHW
        tensor_frame = torch.from_numpy(resized_frame).permute(
            2, 0, 1
        ).unsqueeze(0).float().to(DEVICE) / 255.0

        # Perform inference
        result = model(tensor_frame, verbose=False)[0]

        # No detections found
        if not len(result.boxes.conf) or not result.masks:
            continue

        max_conf_idx = np.argmax(result.boxes.conf.cpu().numpy())
        mask = cv.resize(
            result.masks.data[max_conf_idx].cpu().numpy(), 
            (frame_width, frame_height)
        )

        mask = cv.dilate(cv.erode(mask, KERNEL3), KERNEL20)

        current_pos = find_mask_center(mask)
        metadata.new_pos(current_pos)

        for roi_label, roi_coords in metadata.rois.items():
            x, y, w, h = roi_coords

            if (x <= current_pos[0] <= x + w) and (y <= current_pos[1] <= y + h):

                if args.log_position:
                    with open(pos_log_file, 'a') as log_file:
                        log_file.write(f'{roi_label},{current_pos[0]},{frame_height - current_pos[1]}\n')
                
                cv.rectangle(
                    frame, (x, y),
                    (x + w, y + h),
                    (128, 244, 66), 2
                )

                metadata.increment_region(roi_label)

            else:
                cv.rectangle(
                    frame, (x, y),
                    (x + w, y + h),
                    (80, 80, 80), 2
                )

                if args.type == 'OF':
                    metadata.increment_region('borders')

                    if args.log_position:
                        with open(pos_log_file, 'a') as log_file:
                            log_file.write(f'borders,{current_pos[0]},{frame_height - current_pos[1]}\n')

            metadata.write_on_frame(frame)

            if args.log_stats:
                # Saves the rois counter to file
                metadata.dump(open(stats_log_file, 'w'), frame_rate)
                    
        masked_frame = np.zeros_like(frame)
        masked_frame[mask > 0.5] = [255, 0, 255]

        cv.circle(frame, current_pos, 3, (42, 89, 247), -1)
        frame = cv.addWeighted(masked_frame, 0.2, frame, 1, 0)

        frame_index += 1

        if args.save_video:
            out_writer.write(frame)

        if frame_index == 1000:
            break

        cv.imshow(result_win, frame)
        key = cv.waitKey(10)
        if key in [27, 113]:  # ESC or q
            cleanup_and_exit(cap, pbar)

        elif key == 32:  # Space
            while True:
                cv.imshow(result_win, frame)

                key2 = cv.waitKey(10)
                if key2 == 32:
                    break
                elif key2 in [27, 113]:
                    cleanup_and_exit(cap, pbar)
