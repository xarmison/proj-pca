from matplotlib import pyplot as plt
from pandas import read_csv
import argparse

def parse_args():
    parser = argparse.ArgumentParser(
        description='Processes a log of speed detections and produces a plot.'
    )

    parser.add_argument(
        'log_file', type=str,
        help='Path to the speed log file'
    )

    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()

    data = read_csv(args.log_file)

    fig, axes = plt.subplots(ncols=1, nrows=1, figsize=(12, 5))
    
    axes.set(
        title='Speed of the animal during the video', 
        xlabel='Time (s)',
        ylabel='Speed ($Pixel * s^{-1}$)'
    )

    #axes.plot(data.time, data.speed)
    axes.plot(data.query('speed < 1000').time, data.query('speed < 1000').speed)

    mean = data.query("speed < 1000").speed.mean()
    median = data.query("speed < 1000").speed.median() 

    axes.text(
        0.87, 0.95, f'Mean: {mean:.3f}\nMedian: {median:.3f}', 
        transform = axes.transAxes, fontsize=10,
        verticalalignment='top', 
        bbox={
            'boxstyle': 'round', 
            'facecolor': 'wheat', 
            'alpha': 0.5
        }
    )
    
    plt.tight_layout()
    plt.show()
