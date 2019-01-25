import speech_recognition as sr
import cloudconvert
import urllib.request
import requests
import random
import logging

# scope = friends,photos,audio,video,status,messages,wall,docs,groups,offline
logging.basicConfig(format=u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s %(message)s', level=logging.INFO,
                    filename=u'speech.log', filemode='w')

def get_vk_token():
    return open('vk_api_token.txt').read()


def convert_ogg_to_wav(ogg_audio_file):
    api_key_file = 'api_key.txt'
    api_key = open(api_key_file).read()
    api = cloudconvert.Api(api_key)

    process = api.convert({
        "inputformat": "ogg",
        "outputformat": "wav",
        "input": "upload",
        "file": open(ogg_audio_file, 'rb')
    })

    process.wait()
    process.download()


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
    vk_token = get_vk_token()
    long_poll_server = requests.get('https://api.vk.com/method/messages.getLongPollServer',
                                    params={'access_token': vk_token, 'v': 5.92}).json()['response']
    print(long_poll_server)
    while True:
        # отправление запроса на Long Poll сервер со временем ожидания 20 и опциями ответа 2
        response = requests.get('https://{server}?act=a_check&key={key}&ts={ts}&wait=20&mode=2&version=2'.format(
            server=long_poll_server['server'], key=long_poll_server['key'], ts=long_poll_server['ts'])).json()
        try:
            updates = response['updates']
        # если в этом месте возбуждается исключение KeyError, значит параметр key устарел, и нужно получить новый
        except KeyError:
            # получение ответа от сервера
            long_poll_server = requests.get('https://api.vk.com/method/messages.getLongPollServer',
                                            params={'access_token': vk_token}).json()['response']
            continue
        if updates:
            for element in updates:
                logging.info(u'Событие %s' % (element))
                summands = []  # массив, где мы будем хранить слагаемые
                flag = element[2]  # флаг сообщения
                for number in [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 65536]:  # проходим циклом по возможным слагаемым
                    if flag & number:  # проверяем, является ли число слагаемым с помощью побитового И
                        summands.append(number)  # если является, добавляем его в массив
                logging.info(u'Флаги события %s' % (flag))
                if 2 not in summands:
                    if element[0] == 4:
                        index = 1
                        media_type = 'attach1_type'
                        msg_id = None
                        while media_type in element[6].keys():  # проверка, существует ли медиа-вложение с таким индексом
                            media_type = element[6]['attach{}_type'.format(index)]
                            attach_kind = 'attach{}_kind'.format(index)
                            if media_type == 'doc' and attach_kind in element[6].keys():  # является ли вложение документом
                                if element[6][attach_kind] == 'audiomsg':  # является ли вложение аудио-сообщением
                                    msg_id = element[1]
                                    break
                            index += 1
                            media_type = 'attach{}_type'.format(index)

                        logging.info(u'Входящее сообщение с номером %s' % (msg_id))
                        if msg_id != None:
                            message = requests.get('https://api.vk.com/method/messages.getById',
                                                   params={'access_token': vk_token, 'message_ids': [msg_id], 'v': 5.92}).json()

                            if 'response' in message.keys():
                                ogg_link = message['response']['items'][0]['attachments'][0]['audio_message']['link_ogg']
                                logging.info(u'Ссылка на аудио сообщение %s' % (ogg_link))
                                from_id = message['response']['items'][0]['from_id']
                                download_audio(ogg_link, ogg_voice)
                                convert_ogg_to_wav(ogg_voice)
                                audio_text = recognize(wav_voice)
                                print('Расшифровка голосового сообщения:', audio_text)

                                send_msg = requests.get('https://api.vk.com/method/messages.send',
                                                        params={'access_token': vk_token,
                                                                'message': audio_text,
                                                                'random_id': random.randint(0, 10e9),
                                                                'user_id': from_id,
                                                                'reply_to': msg_id, 'v': 5.92}).json()

        long_poll_server['ts'] = response['ts']
