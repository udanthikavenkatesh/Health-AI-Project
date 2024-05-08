import cv2
import os
from scipy.signal import butter, filtfilt
import heartpy as hp
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
import shutil
import threading

# Function to extract frames from the video and find the sampling rate
def extract_frames_and_sampling_rate(video_filename, output_directory):
    if os.path.exists(output_directory):
        shutil.rmtree(output_directory)

    os.makedirs(output_directory)

    # Open the video file
    cap = cv2.VideoCapture(video_filename)

    frames = cap.get(cv2.CAP_PROP_FRAME_COUNT) 
    fps = cap.get(cv2.CAP_PROP_FPS) 
  
    # calculate duration of the video 
    dur = round(frames / fps)
    
    # Initialize frame count
    frame_count = 0

    # Read until video is completed
    while cap.isOpened():
        # Capture frame-by-frame
        ret, frame = cap.read()
        if not ret:
            break

        # Save the frame
        frame_filename = os.path.join(output_directory, f'frame_{frame_count}.jpg')
        cv2.imwrite(frame_filename, frame)

        # Increment frame count
        frame_count += 1

    # Release the video capture object
    cap.release()

    return dur


def get_image(image_path):
    '''
    Return a numpy array of red image values so that we can access values[x][y]
    '''
    image = Image.open(image_path)
    width, height = image.size
    red, _, _ = image.split()  # Ignore green and blue channels
    red_values = list(red.getdata())
    return np.array(red_values).reshape((width, height))

def get_mean_intensity(image_path):
    '''
    Return mean intensity of an image values
    '''
    image = get_image(image_path)
    return np.mean(image)

def process_frames(start, end, output):
    '''
    Process a range of frames and store the mean intensities in a shared list.
    '''
    dir = 'frames/'
    for j in range(start, end):
        image_path = os.path.join(dir, f'frame_{j}.jpg')
        output[j] = get_mean_intensity(image_path)

def get_signal_from(num_threads=4):
    '''
    Return PPG signal as a sequence of mean intensities from the sequence of
    images that were captured by a device (NoIR camera or iphone camera)
    '''
    dir = 'frames/'
    length = len(os.listdir(dir))
    x = [0] * length
    threads = []
    chunk_size = length // num_threads

    for i in range(num_threads):
        start = i * chunk_size
        end = (i + 1) * chunk_size if i < num_threads - 1 else length
        thread = threading.Thread(target=process_frames, args=(start, end, x))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

    return x


def butter_bandpass(lowcut, highcut, fs, order=5):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return b, a

def butter_bandpass_filter(data, lowcut, highcut, fs, order=5):
    b, a = butter_bandpass(lowcut, highcut, fs, order=order)
    y = filtfilt(b, a, data)
    return y

def getHR(filename):
    try:
        output_directory = 'frames/'
        dur = extract_frames_and_sampling_rate(filename, output_directory)
        x = get_signal_from()
        # Define the cutoff frequencies and order of the filter
        lowcut = 0.5  # Lower cutoff frequency in Hz
        highcut = 10.0  # Upper cutoff frequency in Hz
        order = 4  # Filter order
            # Apply the bandpass filter to the PPG signal
        filtered_ppg_signal = butter_bandpass_filter(x, lowcut, highcut, len(x) / dur, order)
            # Process the filtered PPG signal with HeartPy
        wd_filtered, m_filtered = hp.process(filtered_ppg_signal, sample_rate=len(x) / dur)
        return m_filtered
    except:
        print("Bad Signal Error: Retake the video")


if __name__ == "__main__":
    print(getHR("902578060.mp4"))
