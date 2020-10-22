from matplotlib.ticker import FuncFormatter
from matplotlib import pyplot as plt
from scipy.stats import kde
import pandas as pd
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

    parser.add_argument(
        'frameWidth', type=int,
        help='Frame width of the processed video'
    )

    parser.add_argument(
        'frameHeight', type=int,
        help='Frame height of the processed video'
    )

    return parser.parse_args()

def numberFormatter(x, pos):
    return f'{int(x * 10e5)}'

if __name__ == '__main__':
    args = parse_args()

    data = pd.read_csv(args.log_file)
    x, y = data.x.values, data.y.values
    points = np.vstack((x, y)).T 

    # x, y, points = processFile(args.log_file)

    nbins = 20

    fig, axes = plt.subplots(ncols=2, nrows=1, figsize=(12, 5))

    #axes[0].set_title('Trajectory')
    axes[0].set(
        title='Trajectory', 
        xlim=(0, args.frameWidth), 
        xticks=list(range(0, args.frameWidth, 60)),
        ylim=(0, args.frameHeight),
        yticks=list(range(0, args.frameHeight, 60))
    )

    axes[0].plot(x, y, 'k')

    # Evaluate a gaussian the kernel density estimation on a regular grid of nbins x nbins
    k = kde.gaussian_kde(points.T)
    xi, yi = np.mgrid[x.min():x.max():nbins*1j, y.min():y.max():nbins*1j]
    zi = k(np.vstack([xi.flatten(), yi.flatten()]))

    # Plot density with shading
    #axes[1].set_title('Heatmap')
    axes[1].set(
        title='Heatmap', 
        xticks=list(range(0, args.frameWidth, 60)),
        yticks=list(range(0, args.frameHeight, 60))
    )

    pc = axes[1].pcolormesh(xi, yi, zi.reshape(xi.shape), shading='gouraud', cmap=plt.cm.jet)

    fig.colorbar(pc, format=FuncFormatter(numberFormatter))
    plt.setp(axes[0].xaxis.get_majorticklabels(), rotation=70)
    plt.setp(axes[1].xaxis.get_majorticklabels(), rotation=70)
    plt.tight_layout()
    plt.show()