import sys

import numpy as np
import soundfile as sf
import os
import matplotlib.pyplot as plt
from matplotlib.pyplot import stem

debug = 1

class SoundFile:
    name = ""   #filename with path
    filename = "" #filename without path
    number = -1
    sex = None
    predicted_sex = None
    sound_data = []
    sound_fft = []
    samplerate = 0

    def process_filename(self, filename, directory = None, labeled = True):
        if directory != None:
            self.name = directory + "\\"
        self.name = self.name + filename
        self.filename = filename.split("\\")[-1]
        if labeled:
            self.sex = self.filename[4:5]
            self.number = int(self.filename[0:3])

    def load_sound(self):
        data, samplerate = sf.read(self.name)
        if type(data[0]) in (tuple, list, np.ndarray):
            self.sound_data = [x[0] for x in data[:]] #wez tylko pierwszy kanal
            self.sound_data = self.sound_data[::100]
        print(self.filename + " załadowano.")

    def fft_with_cut(self, display=False, lower_bound=70, upper_bound=250):
        self.sound_fft = abs(np.fft.fft(self.sound_data))[lower_bound:upper_bound]

        if display:
            display_stem(self, abs_sig=False, lower_bound=lower_bound)

def get_fig(fig_size = (15,6)):
    return plt.figure(figsize=fig_size, dpi = 80)

def display_plot(x_data, y_data, size = -1):
    if type(size) == tuple:
        fig = get_fig(size)
    elif size == -1:
        fig = get_fig()
    else:
        fig = get_fig((size, size))
    ax = fig.add_subplot(111)
    ax.set_ylim([min(y_data)*1.2, max(y_data)*1.2])
    ax.plot(x_data, y_data, linestyle='-', color='red')

def display_stem(sound_object, size = -1, abs_sig = True, lower_bound = 70):
    if type(size) == tuple:
        fig = get_fig(size)
    elif size == -1:
        fig = get_fig()
    else:
        fig = get_fig((size, size))
    if abs_sig:
        y_data = abs(sound_object.sound_fft)
    x_data = np.arange(70, 70 + len(sound_object.sound_fft), 1)
    stem(x_data, sound_object.sound_fft, '-*')
    plt.show()



def try_to_predict_sex(sound_object):
    if type(sound_object) is not SoundFile:
        print("not a sound file")
        return None

    #print("min_freq {min_f}, max_freq = {max_f}".format(min_f = min(fft), max_f = max(fft)))
    print("File {file}, predicted sex is {predicted_sex}".format(file = sound_object.filename, predicted_sex = sound_object.predicted_sex))
    return 'M'

if __name__ == "__main__":
    directory = "dataset\\"

    if debug:
        data = []
        for file in os.listdir(directory):
            object = SoundFile()
            object.process_filename(file, directory)
            object.load_sound()
            object.fft_with_cut(True)
            #data.append(object)
            break

    else:
        if len(sys.argv) != 2:
            print("Błędna liczba parametrów!")
            exit(0)
        filename = sys.argv[1]
        sound_object = SoundFile()
        sound_object.process_filename(filename = filename, labeled = False)
        sound_object.load_sound()
        sound_object.fft_with_cut(True)






