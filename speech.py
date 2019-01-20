import speech_recognition as sr
import cloudconvert

ogg_voice = 'voice.ogg'
wav_voice = 'voice.wav'

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
