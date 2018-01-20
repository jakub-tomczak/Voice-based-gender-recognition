import sys
import numpy as np
import soundfile as sf
import os
import matplotlib.pyplot as plt
from matplotlib.pyplot import stem

debug = 1
true_positive = 0

#klasa przechowujaca dane nt. pliku oraz tablice z wczytanym plikiem
class SoundFile:
    beta = 14
    cut_lower_bound = 50
    cut_upper_bound = 800
    male_voice_interval = (50, 165)
    female_voice_interval = (166, 300)

    def __init__(self):
        self.name = ""   #filename with path
        self.filename = "" #filename without path
        self.number = -1
        self.sex = None
        self.predicted_sex = None
        self.sound_data = np.empty([])
        self.sound_fft = []
        self.samplerate = 0
        self.peak = 0

    def process_filename(self, filename, directory = None, labeled = True):
        if directory != None:
            self.name = directory
        self.name = self.name + filename
        self.filename = filename.split("\\")[-1]
        if labeled:
            self.sex = self.filename[4:5]
            self.number = int(self.filename[0:3])

    def apply_window_function(self):
        self.sound_data = self.sound_data * np.kaiser(len(self.sound_data), 50)

    def load_sound(self, apply_window_function = True):
        data, samplerate = sf.read(self.name)
        self.samplerate = float(samplerate)
        if type(data[0]) in (tuple, list, np.ndarray):
            self.sound_data = data[:,0] + data[0:,1] #[x[0] for x in data[:]] #data[0] + data[1] #[x[0] for x in data[:]] #wez tylko pierwszy kanal
            self.sound_data = self.sound_data
        elif type(data[0]) is np.float64:
            self.sound_data = data
        if len(self.sound_data) == 0:
            raise Exception("Nie udało się pobrać próbek")

        if(apply_window_function):
            self.apply_window_function()

        print(self.filename + " załadowano. {len}".format(len = len(self.sound_data)) )

def display_stem(sound_object, abs_sig = False, lower_bound = SoundFile.cut_lower_bound):
    if abs_sig:
        y_data = abs(sound_object.sound_fft)
    plt.figure(figsize=(20, 10), dpi=80)
    plt.title(sound_object.filename)
    x_data = np.arange(lower_bound, lower_bound + len(sound_object.sound_fft), 1)
    stem(x_data, sound_object.sound_fft, '-*')
    plt.show()

def try_to_predict_sex(sound_object, male_frequencies = SoundFile.male_voice_interval, female_frequencies = SoundFile.female_voice_interval):
    global true_positive

    if type(sound_object) is not SoundFile:
        raise Exception("Not a sound file")

    #liczba próbek dla fft
    Nfft = 262144   #dobrane w testach
    divider = 5
    values, frequencies = hps(sound_object, divider, Nfft)

    #oblicz najczesciej wystepujaca czestotliwosc - peak
    maxVal = 0
    top_freq = 0
    for freq, val in zip(frequencies, values):
        if val > maxVal:
            maxVal = val
            top_freq = freq

    if top_freq < male_frequencies[0] or top_freq > female_frequencies[1]:
        # peak jest poza zakresem meskich i zenskich czestotliwosci, oblicz sume dla meskich i zenskich,

        male_freq_sum = 0.0
        female_freq_sum = 0.0
        for freq, val in zip(frequencies, values):
            if freq > male_frequencies[0] and freq < male_frequencies[1]:
                #czestotliwosc nalezy do przedzialu dla mezczyzn
                male_freq_sum += val
            if freq > female_frequencies[0] and freq < female_frequencies[1]:
                # czestotliwosc nalezy do przedzialu dla kobiet
                female_freq_sum += val

        # stwierdz których sumarycznie jest wiecej
        if male_freq_sum > female_freq_sum:
            sound_object.predicted_sex = 'M'
        else:
            sound_object.predicted_sex = 'K'

        if sound_object.predicted_sex == sound_object.sex:
            true_positive += 1
        else:
            print("Zle dopasowanie dla pliku: " + sound_object.filename)

        sound_object.peak = 0
    else:
        #peak jest wykryty w zakresie ludzkiego glosu
        sound_object.peak = top_freq

        if top_freq < male_frequencies[1] and sound_object.sex == 'M' or top_freq >= female_frequencies[0] and sound_object.sex == 'K':
            #peak jest w dobrym przedziale
            true_positive += 1
        else:
            print("Zle dopasowanie dla pliku: " + sound_object.filename)

        if top_freq <  male_frequencies[1]:
            sound_object.predicted_sex = 'M'
        elif top_freq >=  female_frequencies[0]:
            sound_object.predicted_sex = 'K'


def hps(sound_object, divider, Nfft=None):
    x = sound_object.sound_data
    fs = sound_object.samplerate

    f = np.arange(Nfft) / Nfft
    #Nfft - dlugosc transformowanej osi, podawana jako potega 2 dla lepszej wydajnosci
    xf = np.fft.fft(x, Nfft)
    #wez pierwsza polowe probek, ich wartości bezwzględne
    xf = np.abs(xf[:int(len(xf) / 2)])
    #utnij tablice o polowe
    f = f[:int(len(f) / 2)]
    N = f.size

    newLength = int(np.ceil(N / divider))#wez piata czesc probek
    y = xf[:newLength].copy()
    # i wskazuje co która próbkę skaczemy
    # od N/2 do N/divider
    for i in range(2, divider + 1):
        y *= xf[::i][:newLength]

    #przelicz czestotliwosci
    f = f[:newLength] * fs
    return (y, f)

def logarithmic_amplify20(value):
    return np.log10(np.abs(value)) * 20

def print_results(file_handle, sound_object):
    file_results.write("{file};{sex};{predicted};{top_freq};{sample_rate}\n".
                       format(file=sound_object.filename, sex=sound_object.sex, predicted=sound_object.predicted_sex,
                              top_freq=sound_object.peak, sample_rate=sound_object.samplerate))

if __name__ == "__main__":
    directory = "dataset\\"
    test_items_count = 0

    file_results = open("results.csv", "w")

    if len(sys.argv) == 1:
        data = []
        for file in os.listdir(directory):
            try:
                object = SoundFile()
                object.process_filename(file, directory)
                object.load_sound()
                try_to_predict_sex(object)#(70,170), (171,255)
                test_items_count += 1   #licznik wszystkich elementow
            except Exception as e:
                if(len(e.args) >= 1):
                    print("Plik {file}, blad: {err}".format(file = file, err = e.args[0]))
                else:
                    print("Plik {file}, nieznany blad.".format(file=file))
                #print(e.__traceback__)
    elif len(sys.argv) == 2:
        try:
            filename = sys.argv[1]
            sound_object = SoundFile()
            sound_object.process_filename(filename = filename, labeled = False)
            sound_object.load_sound()
        except Exception as e:
            if (len(e.args) >= 1):
                print("Plik {file}, blad: {err}".format(file=filename, err=e.args[0]))
            else:
                print("Plik {file}, nieznany blad.".format(file=filename))
    else:
        print("Błędna liczba parametrów!")
        exit(0)

    file_results.close()
    print("{tr}/{all} : {res}%".format(tr = true_positive, all = test_items_count, res = np.floor(true_positive / test_items_count * 100) ))



