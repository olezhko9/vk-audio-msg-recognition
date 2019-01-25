import speech_recognition as sr
import urllib.request
import random
import logging
import subprocess
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType

# scope = friends,photos,audio,video,status,messages,wall,docs,groups,offline
logging.basicConfig(format=u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s %(message)s', level=logging.INFO,
                    filename=u'speech.log', filemode='w')

def get_vk_token():
    return open('vk_api_token.txt').read()


def convert_ogg_to_wav(ogg_audio_file, wav_audio_file):
    subprocess.run("ffmpeg -y -i {ogg} {wav}".format(ogg=ogg_audio_file, wav=wav_audio_file).split())


def download_audio(url, audio_name_ogg):
    audio_msg = urllib.request.urlopen(url).read()
    f = open(audio_name_ogg, "wb")
    f.write(audio_msg)
    f.close()


def recognize(wav_audio):
    r = sr.Recognizer()
    audio_to_recognize = sr.AudioFile(wav_audio)

    with audio_to_recognize as source:
        audio = r.record(source)
        text = ""
        try:
            text = r.recognize_google(audio, language='ru-RU')
        except sr.UnknownValueError:
            text = "Речь неразборчива. Не могу распознать."
        except sr.RequestError as reqE:
            text = "Распознавание завершилось неудачно."
            logging.error(u'%s %s' % (text, reqE))
    return text


if __name__ == "__main__":
    ogg_voice = 'voice.ogg'
    wav_voice = 'voice.wav'

    vk_session = vk_api.VkApi(token=get_vk_token())
    vk = vk_session.get_api()
    long_poll_server = VkLongPoll(vk_session)

    for event in long_poll_server.listen():
        if event.type == VkEventType.MESSAGE_NEW:
            # если входящее сообщение и содержит вложения
            if event.to_me and event.attachments:
                attachments = event.attachments
                logging.info(u'Входящее сообщение с вложениями: %s' % attachments)
                # на случай, если вложение не является аудио сообщением
                try:
                    if attachments['attach1_kind'] == 'audiomsg':
                        message = vk.messages.getById(message_ids=event.message_id, v=5.92)
                        ogg_link = message['items'][0]['attachments'][0]['audio_message']['link_ogg']
                        from_id = message['items'][0]['from_id']
                        logging.info(u'Аудио сообщение от %d: %s' % (from_id, ogg_link))

                        download_audio(ogg_link, ogg_voice)
                        convert_ogg_to_wav(ogg_voice, wav_voice)
                        audio_text = recognize(wav_voice)
                        logging.info(u'Текст сообщения: %s' % audio_text)

                        vk.messages.send(message=audio_text, peer_id=from_id, reply_to=event.message_id,
                                         random_id=random.randint(0, 10e9), v=5.92)
                except KeyError:
                    continue