import speech_recognition as sr
import cloudconvert
from urllib.request import urlopen

url = 'https://psv4.userapi.com/c852428//u143857006/audiomsg/d15/0b95a179cd.ogg'
ogg_voice = 'voice.ogg'
wav_voice = 'voice.wav'

audio_msg = urlopen(url).read()
f = open(ogg_voice, "wb")
f.write(audio_msg)
f.close()

api_key_file = 'api_key.txt'
api_key = open(api_key_file).read()
api = cloudconvert.Api(api_key)

process = api.convert({
    "inputformat": "ogg",
    "outputformat": "wav",
    "input": "upload",
    "file": open(ogg_voice, 'rb')
})

process.wait()
process.download()

recog = sr.Recognizer()

audio_to_recognize = sr.AudioFile(wav_voice)
with audio_to_recognize as source:
    audio = recog.record(source)
    text = recog.recognize_google(audio, language='ru-RU')
    print(text)
