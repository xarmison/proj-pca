from matplotlib import pyplot as plt
from scipy.stats import kde
import numpy as np
import argparse

def parse_args():
    parser = argparse.ArgumentParser(
        description='Processes a log of detections and produces a heatmap plot.'
    )

    parser.add_argument(
        'log_file', type=str,
        help='Path to the log file'
    )

    return parser.parse_args()

def processFile(logFile):
    x, y = [], []

    with open(logFile, 'r') as file:
        for line in file:
            line = line.split(' ')

            x.append(int(line[0]))
            y.append(int(line[1]))

    return np.asarray(x), np.asarray(y), np.vstack((x, y)).T 

if __name__ == '__main__':
    args = parse_args()

    x, y, points = processFile(args.log_file)

    nbins = 20

    fig, axes = plt.subplots(ncols=2, nrows=1, figsize=(10, 5))

    axes[0].set_title('Trajectory')
    axes[0].plot(x, y, 'r')

    # Evaluate a gaussian the kernel density estimation on a regular grid of nbins x nbins
    k = kde.gaussian_kde(points.T)
    xi, yi = np.mgrid[x.min():x.max():nbins*1j, y.min():y.max():nbins*1j]
    zi = k(np.vstack([xi.flatten(), yi.flatten()]))

    # Plot density with shading
    axes[1].set_title('Heatmap')
    pc = axes[1].pcolormesh(xi, yi, zi.reshape(xi.shape), shading='gouraud', cmap=plt.cm.jet)

    fig.colorbar(pc, ticks=[])
    plt.tight_layout()
    plt.show()