from utils import getOrientation
from os import path, mkdir
from tqdm import tqdm
import numpy as np
import cv2 as cv
import argparse

def parser_args():
    parser = argparse.ArgumentParser(
        description='Tracks mice.'
    )

    parser.add_argument(
        'video', type=str,
        help='Path to the video file to be processed.'
    )

    parser.add_argument(
        'frame_rate', type=int,
        help='Frame rate of the video file to be processed.'
    )

    parser.add_argument(
        '--draw-axis', action='store_true',
        help='Draw both PCA axis.'
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
        '--log-speed', action='store_true',
        help='Logs the speed of the center of mass to file.'
    )

    return parser.parse_args()

if __name__ == '__main__':
    args = parser_args()

    cap = cv.VideoCapture(args.video)
    frameWidth = int(cap.get(3)) 
    frameHeight = int(cap.get(4))

    if (not cap.isOpened()):
        print('Error opening video stream')
        exit()

    # First frame as the background image
    ret, bg_img = cap.read()
    
    if(not ret):
        print('Error readning video stream')
        exit()

    # Selection of the ROIs
    ret, frame = cap.read()

    if(not ret):
        print('Error readning video stream')
        exit()

    roi_win = 'ROI Selection'
    cv.namedWindow(roi_win, cv.WINDOW_KEEPRATIO)
    cv.resizeWindow(roi_win, 1438, 896)

    rois = cv.selectROI(roi_win, frame, False)
    cv.destroyWindow(roi_win)

    # Counter for each selected region    
    rois_counter = [ 0 for _ in range(len(rois)) ]
    statsLogFile = f"./logs/{args.video.split('/')[-1].split('.')[0]}_stats.txt"

    if(args.save_video):
        resultFileName = f"{args.video.split('/')[-1].split('.')[0]}_result.avi"

        outWriter = cv.VideoWriter(
            resultFileName,
            cv.VideoWriter_fourcc('M', 'J', 'P', 'G'),
            args.frame_rate, (frameWidth, frameHeight)
        )

    # Check whether it's necessary to create a logs directory
    if(args.log_stats or args.log_position or args.log_speed):
        if(not path.exists('./logs')):
            mkdir('./logs')

    # Create file for stats loging
    statsLogFile = f"./logs/{args.video.split('/')[-1].split('.')[0]}_stats.txt"
    if(args.log_stats):
        with open(statsLogFile, 'w') as log_file:
            log_file.write('')

    # Create file for position loging
    posLogFile = f"./logs/{args.video.split('/')[-1].split('.')[0]}_pos.csv"
    if(args.log_position):        
        with open(posLogFile, 'w') as log_file:
            log_file.write('x,y\n')

    # Create file for speed loging 
    speedLogFile = f"./logs/{args.video.split('/')[-1].split('.')[0]}_speed.csv"
    if(args.log_speed):        
        with open(speedLogFile, 'w') as log_file:
            log_file.write('time,speed\n')

    result_win = 'Tracker'
    cv.namedWindow(result_win, cv.WINDOW_KEEPRATIO)
    cv.resizeWindow(result_win, 640, 528)

    # Color range of the mice un the subtracted image
    lower_white = np.array([100, 100, 100])
    upper_white = np.array([160, 160, 160])

    # Varibles fo tracking the mice's position
    previous_pos = (0, 0)
    current_pos = (0, 0)

    frameIndex = 0
    traveledDistance = 0

    num_frames = int(cap.get(cv.CAP_PROP_FRAME_COUNT))
    pbar = tqdm(total=num_frames)

    while(cap.isOpened()):
        ret, frame = cap.read()
        pbar.update(1)

        if(not ret):
            print('Error readning video stream')
            pbar.close()
            exit()

        sub_frame = cv.absdiff(frame, bg_img)
           
        filtered_frame = cv.inRange(sub_frame, lower_white, upper_white)
        
        # Kernel for morphological operation opening
        kernel3 = cv.getStructuringElement(
            cv.MORPH_ELLIPSE,
            (3, 3),
            (-1, -1)
        )

        kernel20 = cv.getStructuringElement(
            cv.MORPH_ELLIPSE,
            (20, 20),
            (-1, -1)
        )

        # Morphological opening
        mask = cv.dilate(cv.erode(filtered_frame, kernel3), kernel20)

        # Find all the contours in the mask
        returns = cv.findContours(mask, cv.RETR_LIST, cv.CHAIN_APPROX_NONE)
        
        # Check what findContours returned
        contours = []
        if(len(returns) == 3):
            contours = returns[1]
        else:
            contours = returns[0]

        if(len(contours) != 0):
            # find the biggest countour by the area
            contour = max(contours, key = cv.contourArea)
            cv.drawContours(frame, [contour], 0, (255, 0, 255), 2)

            # Find the orientation of each shape
            current_pos, _ = getOrientation(contour, frame, args.draw_axis)

        speed = np.sqrt(
            (previous_pos[0] - current_pos[0])**2 + 
            (previous_pos[1] - current_pos[1])**2
        )

        traveledDistance += speed
        previous_pos = current_pos

        if(args.log_speed):
            if(current_pos[0] > 50 and current_pos[1] > 50):        
                with open(speedLogFile, 'a') as logFile:
                    logFile.write(f'{frameIndex * (1/float(args.frame_rate)):.3f},{speed:.3f}\n')
        
        # Draw ROI and check if the mice is inside 
        if(rois is not None):

            for index, roi in enumerate(rois):
                x, y, w, h = roi
                
                if(any(current_pos)):
                    if(x <= current_pos[0] <= x+w and y <= current_pos[1] <= y+h):
                        cv.rectangle(
                            frame, (x, y),
                            (x + w, y + h),
                            (128, 244, 66), 2
                        )

                        rois_counter[index] += 1
                        cv.putText(
                            frame, f'{index}: {rois_counter[index]}', (x, y - 5),
                            cv.FONT_HERSHEY_COMPLEX,
                            0.5, (255, 255, 255)
                        )

                    else:
                        cv.rectangle(
                            frame, (x, y),
                            (x + w, y + h),
                            (80, 80, 80), 2
                        )

                        cv.putText(
                            frame, f'{index}: {rois_counter[index]}', (x, y - 5),
                            cv.FONT_HERSHEY_COMPLEX,
                            0.5, (255, 255, 255)
                        )
                else:
                    cv.rectangle(
                        frame, (x, y),
                        (x + w, y + h),
                        (80, 80, 80), 2
                    )

                    cv.putText(
                        frame, f'{index}: {rois_counter[index]}', (x, y - 5),
                        cv.FONT_HERSHEY_COMPLEX,
                        0.5, (255, 255, 255)
                    )

            if(args.log_stats):
                # Saves the rois counter to file
                with open(statsLogFile, 'w') as log_file:
                    
                    log_file.write(f'\tCounters for the regions considering {args.frame_rate}fps video\n')
                    log_file.write(f'\n- Traveled distance: {traveledDistance:.3f} pixels\n')

                    log_file.write('\n- Time in spent in each region:\n')
                    for idx, region in enumerate(rois_counter):
                        log_file.write(f'\tRegion {idx}:\t{rois_counter[idx]} frames')
                        log_file.write(f', {rois_counter[idx] * (1/float(args.frame_rate)):.3f}s\n')

        # Save position to file
        if(args.log_position):
            with open(posLogFile, 'a') as logFile:
                if(current_pos[0] > 50 and current_pos[1] > 50):
                    # Changes the coordinates' center to the bottom left for later plotting
                    logFile.write(f'{current_pos[0]},{frameHeight - current_pos[1]}\n')

        if(args.color_mask):
            # Change the color of the mask
            colored_mask = cv.cvtColor(mask, cv.COLOR_GRAY2BGR)
            colored_mask[np.where((colored_mask == [255, 255, 255]).all(axis = 2))] = [222, 70, 222]

            # Apply the mask
            frame = cv.add(frame, colored_mask)

        cv.imshow(result_win, frame)
        frameIndex += 1

        if(args.save_video):
            outWriter.write(frame)

        key = cv.waitKey(10)
        if(key == 27 or key == 113):
            cv.destroyAllWindows()
            cap.release()
            pbar.close()

            if(args.save_video):
                outWriter.release()

            exit()

        if(key == 32):
            while True:

                cv.imshow(result_win, frame)
                
                key2 = cv.waitKey(5)
                if(key2 == 32):
                    break
                elif(key2 == 27 or key == 113):
                    cv.destroyAllWindows()
                    cap.release()
                    pbar.close()

                    if(args.save_video):
                        outWriter.release()

                    exit()