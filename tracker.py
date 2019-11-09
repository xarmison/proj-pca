from math import atan2, cos, sin, sqrt, pi
import numpy as np
import cv2 as cv
import argparse

def parser_args():
    parser = argparse.ArgumentParser(
        description='Tracks mice.'
    )

    parser.add_argument(
        'video', type=str,
        help='Path to the file file to be processed.'
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

    return parser.parse_args()

def drawAxis(img, p_, q_, colour, scale):
    p = list(p_)
    q = list(q_)

    angle = atan2(p[1] - q[1], p[0] - q[0])  # angle in radians
    hypotenuse = sqrt((p[1] - q[1]) * (p[1] - q[1]) + (p[0] - q[0]) * (p[0] - q[0]))

    # Here we lengthen the arrow by a factor of scale
    q[0] = p[0] - scale * hypotenuse * cos(angle)
    q[1] = p[1] - scale * hypotenuse * sin(angle)
    cv.line(img, (int(p[0]), int(p[1])), (int(q[0]), int(q[1])), colour, 2, cv.LINE_AA)

    # create the arrow hooks
    p[0] = q[0] + 9 * cos(angle + pi / 4)
    p[1] = q[1] + 9 * sin(angle + pi / 4)
    cv.line(img, (int(p[0]), int(p[1])), (int(q[0]), int(q[1])), colour, 2, cv.LINE_AA)

    p[0] = q[0] + 9 * cos(angle - pi / 4)
    p[1] = q[1] + 9 * sin(angle - pi / 4)
    cv.line(img, (int(p[0]), int(p[1])), (int(q[0]), int(q[1])), colour, 2, cv.LINE_AA)

def getOrientation(pts, img, draw):
    # Construct a buffer used by the pca analysis
    sz = len(pts)
    data_pts = np.empty((sz, 2), dtype=np.float64)

    for i in range(data_pts.shape[0]):
        data_pts[i, 0] = pts[i, 0, 0]
        data_pts[i, 1] = pts[i, 0, 1]

    # Perform PCA analysis
    mean = np.empty((0))
    mean, eigenvectors, eigenvalues = cv.PCACompute2(data_pts, mean)

    # Store the center of the object
    cntr = (int(mean[0, 0]), int(mean[0, 1]))

    # Draw the principal components
    cv.circle(img, cntr, 3, (42, 89, 247), -1)
    p1 = (
        cntr[0] + 0.02 * eigenvectors[0, 0] * eigenvalues[0, 0],
        cntr[1] + 0.02 * eigenvectors[0, 1] * eigenvalues[0, 0]
    )
    p2 = (
        cntr[0] - 0.02 * eigenvectors[1,0] * eigenvalues[1,0],
        cntr[1] - 0.02 * eigenvectors[1,1] * eigenvalues[1,0]
    )

    if(draw):
        drawAxis(img, cntr, p1, (91, 249, 77), 2)
        drawAxis(img, cntr, p2, (190, 192, 91), 2)

    # orientation in radians
    angle = atan2(eigenvectors[0, 1], eigenvectors[0, 0])

    return cntr, angle

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

    # Color range of the mice un the subtracted image
    lower_white = np.array([100, 100, 100])
    upper_white = np.array([160, 160, 160])

    # Selection of the ROIs
    ret, frame = cap.read()

    if(not ret):
        print('Error readning video stream')
        exit()

    rois = cv.selectROIs('ROIs Selection', frame, False)
    cv.destroyWindow('ROIs Selection')

    # Counter for each selected region    
    roisCounter = [ 0 for _ in range(len(rois)) ]
    statsLogFile = args.video.split('/')[-1].split('.')[0] + '_stats.txt'

    result_win = 'Tracker'
    cv.namedWindow(result_win, cv.WINDOW_KEEPRATIO)
    cv.resizeWindow(result_win, 640, 528)

    if(args.save_video):
        resultFileName = args.video.split('/')[-1].split('.')[0] + '_result.avi'

        outWriter = cv.VideoWriter(
            resultFileName,
            cv.VideoWriter_fourcc('M', 'J', 'P', 'G'),
            30, (frameWidth, frameHeight)
        )
    
    # Create file for position loging 
    if(args.log_position):
        logFileName = args.video.split('/')[-1].split('.')[0] + '_log.csv'
        
        with open(logFileName, 'w') as logFile:
            logFile.write('x,y\n')

    while(cap.isOpened()):
        ret, frame = cap.read()

        if(not ret):
            print('Error readning video stream')
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

        mask_roi = cv.bitwise_and(sub_frame, sub_frame, mask=mask)

        # Find all the contours in the mask
        returns = cv.findContours(mask, cv.RETR_LIST, cv.CHAIN_APPROX_NONE)
        
        # Check what findContours returned
        contours = []
        if(len(returns) == 3):
            contours = returns[1]
        else:
            contours = returns[0]

        cntr = (0, 0)
        for i, c in enumerate(contours):
            # Calculate the area of each contour
            area = cv.contourArea(c)

            # Ignore contours that are too small or too large
            if area < 1e2 or 1e5 < area:
                continue

            # Draw each contour only for visualisation purposes
            cv.drawContours(frame, contours, i, (255, 0, 255), 2)

            # Find the orientation of each shape
            cntr, _ = getOrientation(c, frame, args.draw_axis)
        
        # Draw ROI and check if the mice is inside 
        if(rois is not None):
            if(args.log_position):
                with open(statsLogFile, 'w') as logFile:
                    logFile.write('Conuters for the regions\n')

            for index, roi in enumerate(rois):
                x, y, w, h = roi
                
                if(any(cntr)):
                    if(x <= cntr[0] <= x+w and y <= cntr[1] <= y+h):
                        cv.rectangle(
                            frame, (x, y),
                            (x + w, y + h),
                            (128, 244, 66), 2
                        )

                        roisCounter[index] += 1
                        cv.putText(
                            frame, f'{index}: {roisCounter[index]}', (x, y - 5),
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
                            frame, f'{index}: {roisCounter[index]}', (x, y - 5),
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
                        frame, f'{index}: {roisCounter[index]}', (x, y - 5),
                        cv.FONT_HERSHEY_COMPLEX,
                        0.5, (255, 255, 255)
                    )

                if(args.log_position):
                    # Saves the rois counter to file
                    with open(statsLogFile, 'a') as logFile:
                        logFile.write(f'Region {index}: {roisCounter[index]} frames\n')

        # Save position to file
        if(args.log_position):
            logFileName = args.video.split('/')[-1].split('.')[0] + '_log.csv'

            with open(logFileName, 'a') as logFile:
                if(cntr[0] > 50 and cntr[1] > 50):
                    # Changes the coordinates' center to the bottom left for later plotting
                    logFile.write(f'{cntr[0]},{frameHeight - cntr[1]}\n')

        if(args.color_mask):
            # Change the color of the mask
            colored_mask = cv.cvtColor(mask, cv.COLOR_GRAY2BGR)
            colored_mask[np.where((colored_mask == [255, 255, 255]).all(axis = 2))] = [222, 70, 222]

            # Apply the mask
            frame = cv.add(frame, colored_mask)

        cv.imshow(result_win, frame)

        if(args.save_video):
            outWriter.write(frame)

        key = cv.waitKey(10)
        if(key == 27 or key == 113):
            cv.destroyAllWindows()
            cap.release()

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

                    if(args.save_video):
                        outWriter.release()

                    exit()