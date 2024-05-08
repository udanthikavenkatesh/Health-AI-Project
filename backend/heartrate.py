# Import necessary libraries
from logging import exception
import cv2
import os
from scipy.signal import butter, filtfilt
import heartpy as hp
import numpy as np
import matplotlib.pyplot as plt
import shutil
import time

# Function to compute signal-to-noise ratio
def signaltonoise(a, axis=0, ddof=0):
    a = np.asanyarray(a)
    m = a.mean(axis)
    sd = a.std(axis=axis, ddof=ddof)
    return m / sd

# Function to extract frames from video and calculate sampling rate
def extract_frames_and_sampling_rate(video_filename, output_directory):
    # Clear output directory if it exists
    if os.path.exists(output_directory):
        shutil.rmtree(output_directory)

    # Create output directory
    os.makedirs(output_directory)
    print(video_filename)

    # Open video file
    cap = cv2.VideoCapture(video_filename)

    # Get total number of frames and frames per second (FPS)
    frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    fps = cap.get(cv2.CAP_PROP_FPS)
    print("FPS :", frames)

    # Calculate duration of video
    dur = round(frames / fps)
    frame_count = 0

    # Loop through video frames
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        # Save frame as image
        frame_filename = os.path.join(output_directory, f'frame_{frame_count}.jpg')
        cv2.imwrite(frame_filename, frame)
        frame_count += 1
    cap.release()
    return dur

# Function to read an image and convert it to grayscale
def get_image(image_path):
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    return image

# Function to compute mean intensity of an image
def get_mean_intensity(image_path):
    image = get_image(image_path)
    return np.mean(image)

# Function to plot data
def plot(x, title, xaxis, yaxis, filename):
    fig = plt.figure(figsize=(13, 6))
    ax = plt.axes()
    ax.plot(list(range(len(x))), x)
    plt.title(title)
    plt.xlabel(xaxis)
    plt.ylabel(yaxis)
    plt.legend()
    plt.grid(True)
    plt.savefig(filename)
    plt.show()

# Function to get signal from frames directory
def get_signal_from(frames_dir):
    length = len(os.listdir(frames_dir))
    x = []
    for j in range(length):
        image_path = os.path.join(frames_dir, f'frame_{j}.jpg')
        x.append(get_mean_intensity(image_path))
    return x

# Butterworth bandpass filter design
def butter_bandpass(lowcut, highcut, fs, order=5):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return b, a

# Function to apply bandpass filter
def butter_bandpass_filter(data, lowcut, highcut, fs, order=5):
    b, a = butter_bandpass(lowcut, highcut, fs, order=order)
    y = filtfilt(b, a, data)
    return y

# Function to process video
def process_video(filename):
    try:
        print("Processing :",filename)
        f = filename
        start_time = time.time()
        output_directory = 'frames/' + filename + "/"
        dur = extract_frames_and_sampling_rate(f, output_directory)
        x = get_signal_from(output_directory)

        lowcut = 0.5
        highcut = 10.0
        order = 4

        filtered_ppg_signal = butter_bandpass_filter(x, lowcut, highcut, len(x) / dur, order)
        wd_filtered, m_filtered = hp.process(filtered_ppg_signal, sample_rate=len(x) / dur)
        snr = signaltonoise(filtered_ppg_signal)
        end_time = time.time()

        # Create JSON object with vital sign information
        v_json = {
            "bpm" : m_filtered['bpm'],
            "SNR": snr,
            "processing_time" : abs(start_time-end_time)
        }
        print(v_json)
        return m_filtered['bpm'], snr
    
    except Exception as e:
        # Print error message if processing fails
        print(e)

# Main section
if __name__ == "__main__":
    # Process each video file and print vital sign information
    print(process_video("S001_H.MOV"))
  