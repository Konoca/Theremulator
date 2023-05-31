#!./venv/bin/python3

import numpy as np
import sounddevice as sd


class Synthesizer:
    def __init__(self, minimum_octave: int = 0, maximum_octave: int = 8, device: int = 0):
        self.calculate_note_frequencies(minimum_octave=minimum_octave, maximum_octave=maximum_octave)

        self.samples_per_second = 44100
        self.duration_in_seconds = 100
        self.volume = 0.1
        self.note = self.notes['C3']
        self.start_idx = 0

        self.stream = sd.OutputStream(channels=1, callback=self.callback, samplerate=self.samples_per_second)
        self.waveform = 'sine'

        self.perfect_pitch = True


    def calculate_note_frequencies(self,
        A4_frequency: float = 440,
        minimum_octave: int = 0,
        maximum_octave: int = 8,
        note_names: list[str] = ['C', 'C#/Db', 'D', 'D#/Eb', 'E', 'F', 'F#/Gb', 'G', 'G#/Ab', 'A', 'A#/Bb', 'B']
    ):
        # Math can be found here: https://pages.mtu.edu/~suits/NoteFreqCalcs.html
        # distance in half-steps
        A_index = note_names.index('A')
        length = len(note_names)

        lowest_note_distance = (A_index + (length * abs(4 - minimum_octave))) * (-1 if minimum_octave < 4 else 1)
        highest_note_distance = ((length - A_index) + (length * abs(4 - maximum_octave))) * (-1 if maximum_octave < 4 else 1)

        self.notes: dict[str, float] = {}
        self.frequencies: list[float] = []
        for i in range(lowest_note_distance, highest_note_distance):
            freq = A4_frequency * (2**(1/length))**i

            note_index = (i + A_index) % length
            note_name = note_names[note_index]

            octave = 4 + int(((i + A_index) - note_index) / length)

            self.notes[f'{note_name}{octave}'] = freq
            self.frequencies.append(freq)


    def get_waveform(self, t: np.ndarray):
        match self.waveform.lower():
            case 'sine': # https://en.wikipedia.org/wiki/Sine_wave
                return np.sin(2 * np.pi * self.note * t) * self.volume
            case 'square': # https://en.wikipedia.org/wiki/Square_wave
                return np.sign(np.sin(2 * np.pi * self.note * t)) * self.volume * 0.5
            case 'triangle': # https://www.youtube.com/watch?v=OSCzKOqtgcA
                return (np.arcsin(np.sin(2 * np.pi * self.note * t)) * (2 / np.pi)) * self.volume
            case 'sawtooth': # https://www.youtube.com/watch?v=OSCzKOqtgcA
                return ((2 * np.pi) * (self.note * np.pi * (t % (1 / self.note)) - (np.pi / 2))) * self.volume * 0.05
            case _:
                self.change_waveform('sine')
                return self.get_waveform(t)

    def get_waveforms(self):
        return ['sine', 'square', 'triangle', 'sawtooth']


    def callback(self, outdata, frames, _, status):
        if status:
            print(status)

        t = (self.start_idx + np.arange(frames)) / self.samples_per_second
        t = t.reshape(-1, 1)

        outdata[:] = self.get_waveform(t)
        self.start_idx += frames


    def start(self):
        self.stream.start()

    def stop(self):
        self.stream.abort()

    def change_note(self, note_display_name: str = 'A4'):
        try:
            self.note = self.notes[note_display_name]
        except KeyError:
            print('Not a valid note!')

    def change_volume(self, volume: float = 0.3):
        self.volume = volume

    def change_waveform(self, waveform: str = 'sine'):
        self.waveform = waveform

    def change_frequency(self, frequency: float):
        self.note = frequency

    def toggle_perfect_pitch(self):
        self.perfect_pitch = not self.perfect_pitch

    def change_values(self, pitch: float, volume: float):
        """To be used by HandTracking obj, parameters are percentages of available values
        pitch: percentage from 0 to 1, needs to be mapped to list of frequencies
        volume: percentage from 0 to 1, needs to be inverted"""

        inverted_volume = 1 - volume
        transformed_pitch = self.frequencies[int(pitch * len(self.frequencies)) - 1] if self.perfect_pitch else (pitch * self.frequencies[-1])

        self.change_volume(inverted_volume)
        self.change_frequency(transformed_pitch)

    def get_values(self):
        return self.volume, list(self.notes.keys())[list(self.notes.values()).index(self.note)] if self.perfect_pitch else f'{self.note:.2f}'


    def debug(self):
        print('### Note format: [Letter][Octave]. Examples: A4, C2, G#/Ab7 ###')
        print('### Commands: ###')
        print('###     Change note: N <note> (Example: N A4, note MUST be capatalized) ###')
        print('###     Change volume: V <volume> (Example: V 0.5) ###')
        print('###     Change waveform: W <waveform> (Example: W sine, available: sine, square, triangle, sawtooth) ###')

        while(True):
            inp = input('> ').split(' ')
            match inp[0].lower():
                case 'n':
                    self.change_note(inp[1])
                case 'v':
                    self.change_volume(float(inp[1]))
                case 'w':
                    self.change_waveform(inp[1])
                case 'q':
                    quit()
                case _:
                    continue


def main():
    synth = Synthesizer()

    note = input('Enter starting note: ')
    synth.change_note(note)
    synth.start()

    synth.debug()


if __name__ == '__main__':
    main()
