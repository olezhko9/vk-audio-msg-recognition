import speech_recognition as sr
import cloudconvert
import urllib.request
import requests
import time
import random

# scope = friends,photos,audio,video,status,messages,wall,docs,groups,offline

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
        text = r.recognize_google(audio, language='ru-RU')

    return text


if __name__ == "__main__":
    url = 'https://psv4.userapi.com/c852428//u143857006/audiomsg/d15/0b95a179cd.ogg'
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
                summands = []  # массив, где мы будем хранить слагаемые
                flag = element[2]  # флаг сообщения
                for number in [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 65536]:  # проходим циклом по возможным слагаемым
                    if flag & number:  # проверяем, является ли число слагаемым с помощью побитового И
                        summands.append(number)  # если является, добавляем его в массив

                if 2 not in summands:
                    if element[0] == 4:
                        print(element)
                        index = 1
                        media_type = 'attach1_type'
                        msg_element = {}
                        while media_type in element[6].keys():  # проверка, существует ли медиа-вложение с таким индексом
                            media_type = element[6]['attach{}_type'.format(index)]
                            attach_kind = 'attach{}_kind'.format(index)
                            if media_type == 'doc' and attach_kind in element[6].keys():  # является ли вложение документом
                                if element[6][attach_kind] == 'audiomsg':
                                    msg_element = dict(msg_id=element[1], peer_id=element[3], doc=element[6]['attach{}'.format(index)])
                                    break
                            index += 1  # увеличиваем индекс
                            media_type = 'attach{}_type'.format(index)

                        if msg_element:
                            msg_element['doc'] = requests.get('https://api.vk.com/method/docs.getById',
                                                params={'docs': msg_element['doc'], 'access_token': vk_token, 'v': 5.92}).json()
                            if 'response' in msg_element['doc'].keys():
                                doc_url = msg_element['doc']['response'][0]['url']
                                download_audio(doc_url, ogg_voice)
                                convert_ogg_to_wav(ogg_voice)
                                audio_text = recognize(wav_voice)
                                print('Расшифровка голосового сообщения:', audio_text)

                                send_msg = requests.get('https://api.vk.com/method/messages.send',
                                             params={'access_token': vk_token, 'message': audio_text, 'random_id': random.randint(0, 10e9), 'user_id': msg_element['peer_id'], 'reply_to': msg_element['msg_id'], 'v': 5.92}).json()
                                print(send_msg)
                            else:
                                pass  # скорее всего, возникла ошибка доступа

        long_poll_server['ts'] = response['ts']