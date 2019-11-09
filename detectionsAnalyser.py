from time import sleep
import numpy as np
import cv2 as cv
import argparse

def parser_args():
    parser = argparse.ArgumentParser(
        description='Visualise and enables corrections on log files.'
    )

    parser.add_argument(
        'video', type=str,
        help='Path to the file file to be processed.'
    )

    parser.add_argument(
        'log_file', type=str,
        help='Path to the log file.'
    )

    return parser.parse_args()

def fileGenerator(filePath):
    with open(filePath, 'r')  as file:
        file.readline()
        for lineNum, line in enumerate(file):
            yield lineNum + 1, line.rstrip().split(',')

def editFrame(frame, lineNum, changes):
    print('\n>>> Drag the mouse to select, the disired centre should be in the crosshair.')
    x, y, w, h = cv.selectROI('Edition Window', frame, True)

    cv.destroyWindow('Edition Window')

    # Store the changes made into the changes list
    changes.append({
        'line': lineNum,
        'content': f'{x + w//2},{y + h//2}'
    })
    
    
if __name__ == '__main__':
    args = parser_args()

    # Gerenator for the log file
    file = fileGenerator(args.log_file)

    if(not file):
        print('Unable to open the log file.')
        exit()

    cap = cv.VideoCapture(args.video)

    if (not cap.isOpened()):
        print('Error opening video stream.')
        exit()

    # List to store the changes made in the log file
    changes = []

    # Delay on each frame
    delay = 0.5

    main_win = 'Video'
    cv.namedWindow(main_win, cv.WINDOW_KEEPRATIO)
    cv.resizeWindow(main_win, 640, 528)
    cv.moveWindow(main_win, 10, 10)

    while(cap.isOpened()):
        global frame
        ret, frame = cap.read()

        if(not ret):
            print('Error reading video stream')
            break

        # Read detected objects from file
        lineNum, cntr = next(file)
        
        # Draws detections
        annotatedFrame = frame.copy()
        if(cntr[0] != '0' and cntr[1] != '0'):
            cv.circle(
                annotatedFrame, 
                (int(cntr[0]), int(cntr[1])), 
                5, (42, 89, 247), -1
            )

        cv.imshow(main_win, annotatedFrame)

        key = cv.waitKey(5)
        # Exit the program
        if(key == 27 or key == 113):
            cv.destroyAllWindows()
            cap.release()
            break

        # Increases the delay between each video frame
        if(key == 115):
            delay += 0.25

        # Decreases the delay between each video frame
        if(key == 102 and delay > 0):
            delay -= 0.25

        # Pauses the video stream
        if(key == 32):
            while True:

                cv.imshow(main_win, annotatedFrame)

                key2 = cv.waitKey(5)
                if(key2 == 32):
                    break
                elif(key2 == 27 or key2 == 113):
                    cv.destroyAllWindows()
                    cap.release()
                    break
                elif(key2 == 100):
                    editFrame(frame.copy(), lineNum, changes)

        sleep(delay)

    # Write changes to the log file
    lines = open(args.log_file, 'r').read().splitlines()

    for change in changes:
        lines[change['line']] = change['content']

    open(args.log_file, 'w').write('\n'.join(lines))