import mediapipe as mp
import cv2
import time
from google.protobuf.json_format import MessageToDict
import threading

from synthesizer import Synthesizer

class HandTracking:
    def __init__(self, synth: Synthesizer, webcam_id: int = 0, event: threading.Event = threading.Event()):
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.webcam = cv2.VideoCapture(webcam_id)  # int parameter decides which webcam to use
        self.resolution = (int(self.webcam.get(cv2.CAP_PROP_FRAME_WIDTH)), int(self.webcam.get(cv2.CAP_PROP_FRAME_HEIGHT)))
        self.topLeft = (0,0)
        self.botRight = (0,0)

        self.isCalibrated = False

        self.volume = 0.0
        self.pitch = 0.0
        self.synth = synth

        self.img = []
        self.event = event

    def main(self):
        with self.mp_hands.Hands(
            model_complexity=0,
            min_detection_confidence = 0.5,
            min_tracking_confidence = 0.5
        ) as hands:
            startTime = time.time()
            prevTime = time.time()
            while self.webcam.isOpened():
                success, img = self.webcam.read()
                img = cv2.flip(img, 1)
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

                img.flags.writeable = False
                results = hands.process(img)

                img.flags.writeable = True
                #img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

                tempTopLeft = list((self.resolution[0], self.resolution[1]))
                tempBotRight = list((0,0))
                closestPitch = self.topLeft[0]
                closestVol = self.botRight[1]
                if results.multi_hand_landmarks:
                    # only works is multiple hands in frame
                    if (len(results.multi_hand_landmarks) > 1):
                        left = 0
                        right = 1
                        if MessageToDict(results.multi_handedness[0])['classification'][0]['label'] == 'Right':
                            left = 1
                            right = 0
                        # Calibration logic
                        if self.isCalibrated == False:
                            for hand_landmarks in results.multi_hand_landmarks:
                                self.mp_drawing.draw_landmarks(img, hand_landmarks, connections = self.mp_hands.HAND_CONNECTIONS)
                                for point in hand_landmarks.landmark:
                                    x = int(point.x * self.resolution[0])
                                    y = int(point.y * self.resolution[1])

                                    if x < tempTopLeft[0]:
                                        tempTopLeft[0] = x
                                    if x > tempBotRight[0]:
                                        tempBotRight[0] = x
                                    if y < tempTopLeft[1]:
                                        tempTopLeft[1] = y
                                    if y > tempBotRight[1]:
                                        tempBotRight[1] = y

                                self.topLeft = tuple(tempTopLeft)
                                self.botRight = tuple(tempBotRight)
                        # Pitch and Volume finding
                        else:
                            self.mp_drawing.draw_landmarks(img, results.multi_hand_landmarks[0], connections = self.mp_hands.HAND_CONNECTIONS)
                            self.mp_drawing.draw_landmarks(img, results.multi_hand_landmarks[1], connections = self.mp_hands.HAND_CONNECTIONS)
                            for point in results.multi_hand_landmarks[left].landmark:
                                y = int(point.y * self.resolution[1])
                                if y < closestVol:
                                    closestVol = y
                            for point in results.multi_hand_landmarks[right].landmark:
                                x = int(point.x * self.resolution[0])
                                if x > closestPitch:
                                    closestPitch = x
                        if self.isCalibrated == True:
                            self.pitch = (closestPitch - self.topLeft[0]) / (self.botRight[0] - self.topLeft[0])
                            self.volume = ((closestVol - self.topLeft[1]) / (self.botRight[1] - self.topLeft[1]))
                            if self.pitch < 0:
                                self.pitch = 0
                            elif self.pitch > 1:
                                self.pitch = 1
                            if self.volume < 0:
                                self.volume = 0
                            elif self.volume > 1:
                                self.volume = 1

                currTime = time.time()
                if (currTime - startTime) > 5.0:
                    self.isCalibrated = True
                    self.synth.start()
                fps = 1 / (currTime - prevTime)
                prevTime = currTime
                #cv2.putText(img, f'FPS: {int(fps)} PITCH: {int(self.pitch*100)} VOL: {int(self.volume*100)}', (28,70), cv2.FONT_HERSHEY_PLAIN, 2, (255,0,0), 2)

                self.synth.change_values(self.pitch, self.volume)
                v,p = self.synth.get_values()
                cv2.putText(img, f'V: {int(v * 100)}%, P: {p}', (28,70), cv2.FONT_HERSHEY_PLAIN, 2, (255,0,0), 2)

                # Draw box around calibrated area
                color = (0,0,255)
                if self.isCalibrated:
                    color = (0,255,0)
                cv2.line(img, (self.topLeft[0],self.topLeft[1]), (self.botRight[0],self.topLeft[1]), color, thickness=2)
                cv2.line(img, (self.botRight[0],self.topLeft[1]), (self.botRight[0],self.botRight[1]), color, thickness=2)
                cv2.line(img, (self.botRight[0],self.botRight[1]), (self.topLeft[0],self.botRight[1]), color, thickness=2)
                cv2.line(img, (self.topLeft[0],self.botRight[1]), (self.topLeft[0],self.topLeft[1]), color, thickness=2)

                #cv2.imshow('Test', img)
                self.img = img
                if cv2.waitKey(5) & 0xFF == 27:
                    break

                if self.event.is_set():
                    break

        self.webcam.release()
        cv2.destroyAllWindows()
