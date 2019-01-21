import speech_recognition as sr
import cloudconvert
import urllib.request
import requests
import time

# 2fd35efed90bc11ff20542d3d42164e75e454a83
# imv4.vk.com\/im3491
# 1841778296
def get_vk_token():
    return open('vk_api_token.txt').read()

def convert_ogg_to_wav(ogg_audio):
    api_key_file = 'api_key.txt'
    api_key = open(api_key_file).read()
    api = cloudconvert.Api(api_key)

    process = api.convert({
        "inputformat": "ogg",
        "outputformat": "wav",
        "input": "upload",
        "file": open(ogg_audio, 'rb')
    })

    process.wait()
    process.download()
 

def download_audio(url, wav_audio):
    audio_msg = urllib.request.urlopen(url).read()
    f = open(wav_audio, "wb")
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
    # convert_ogg_to_wav(ogg_voice)
    # print(recognize(wav_voice))

    long_poll_server = requests.get('https://api.vk.com/method/messages.getLongPollServer',
                        params={'access_token': get_vk_token(), 'v': 5.92}).json()['response']

    while True:
        response = requests.get('https://{server}?act=a_check&key={key}&ts={ts}&wait=20&mode=2&version=2'.format(
                server=long_poll_server['server'], key=long_poll_server['key'], ts=long_poll_server['ts'])).json()  # отправление запроса на Long Poll сервер со временем ожидания 20 и опциями ответа 2
        try:
            updates = response['updates']
        except KeyError:  # если в этом месте возбуждается исключение KeyError, значит параметр key устарел, и нужно получить новый
            long_poll_server = requests.get('https://api.vk.com/method/messages.getLongPollServer',
                                            params={'access_token': get_vk_token()}).json()['response']  # получение ответа от сервера
            continue  # переходим на следующую итерацию цикла, чтобы сделать повторный запрос
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
                        if element[3] - 2000000000 > 0:
                            user_id = element[6]['from']  # id отправителя
                            chat_id = element[3] - 2000000000  # id беседы
                            chat = requests.get('https://api.vk.com/method/messages.getChat',
                                                params={'chat_id': chat_id, 'access_token': get_vk_token()}).json()['response']['title']  # получение названия беседы
                            # user = requests.get('https://api.vk.com/method/users.get',
                            #                     params={'user_ids': user_id, 'name_case': 'gen'}).json()['response'][0]  # получение имени и фамилии пользователя, отправившего сообщение
                            time_ = element[4]  # время отправления сообщения
                            text = element[5]  # текст сообщения
                            if text:  # проверяем, что сообщение содержит текст
                                print(time.ctime(time_).split()[3], ':', 'Сообщение от', user_id, 'в беседе "{}"'.format(chat) + ':', text)
                        else:
                            user_id = element[3]  # id собеседника
                            # user = requests.get('https://api.vk.com/method/users.get',
                            #                     params={'user_ids': user_id, 'name_case': 'gen'}).json()['response'][0]  # получение имени и фамилии пользователя, отправившего сообщение
                            time_ = element[4]  # время отправления сообщения
                            text = element[5]  # текст сообщения
                            if text:  # проверяем, что сообщение содержит текст
                                print(time.ctime(time_).split()[3], ':', 'Сообщение от', user_id, ':', text)


                        index = 1
                        photos = []  # массив для хранения id фотографий
                        docs = []  # массив для хранения id документов
                        media_type = 'attach1_type'
                        while media_type in element[6].keys():  # проверка, существует ли медиа-вложение с таким индексом
                            media_type = element[6]['attach{}_type'.format(index)]  # если существует, сохраняем его тип
                            if media_type == 'photo':  # является ли вложение фотографией
                                photos.append(element[6]['attach{}'.format(index)])  # добавляем id фотографии в массив
                            elif media_type == 'doc':  # является ли вложение документом
                                docs.append(element[6]['attach{}'.format(index)])  # добавляем id документа в массив
                            index += 1  # увеличиваем индекс
                            media_type = 'attach{}_type'.format(index)
                        change = lambda ids, type_: requests.get(
                            'https://api.vk.com/method/{}.getById'.format(type_),
                            params={type_: ids, 'access_token': get_vk_token(), 'v': 5.92}
                        ).json()  # функция, возвращающаяся ссылки на объекты
                        if photos:  # проверка, были ли во вложениях фотографии
                            photos = change(', '.join(photos), 'photos')  # если были, то перезаписываем переменную photos на словарь
                            if 'response' in photos.keys():
                                photos = [attachment['src_xbig'] for attachment in photos['response']]  # перезаписываем на ссылки
                                print('сообщение содержит следующие фотографии:', ', '.join(photos))
                            else:
                                pass  # скорее всего, возникла ошибка доступа
                        if docs:  # проверка, были ли во вложениях документы
                            docs = change(', '.join(docs), 'docs')  # если были, то перезаписываем переменную docs на словарь
                            if 'response' in docs.keys():
                                docs = [attachment['url'] for attachment in docs['response']]  # перезаписываем на ссылки
                                print('сообщение содержит следующие документы:', ', '.join(docs))
                            else:
                                pass  # скорее всего, возникла ошибка доступа

        long_poll_server['ts'] = response['ts']