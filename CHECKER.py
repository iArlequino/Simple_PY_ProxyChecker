import os
import sys
from concurrent.futures import ThreadPoolExecutor, wait
from time import sleep, time
import json

import requests
from fake_headers import Headers

os.system("")


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


checked = {}
cancel_all = False



def load_proxy():
    proxies = []

    filename = input(bcolors.OKBLUE + 'Введите имя вашего файла с proxy: ' + bcolors.ENDC)

    if not os.path.isfile(filename) and filename[-4:] != '.txt':
        filename = f'{filename}.txt'

    try:
        with open(filename, encoding="utf-8") as fh:
            loaded = [x.strip() for x in fh if x.strip() != '']
    except Exception as e:
        print(bcolors.FAIL + str(e) + bcolors.ENDC)
        input('')
        sys.exit()

    for lines in loaded:
        if lines.count(':') == 3:
            split = lines.split(':')
            lines = f'{split[2]}:{split[-1]}@{split[0]}:{split[1]}'
        proxies.append(lines)

    return proxies


def test_speed(proxy_dict, headers):
    urls = [
        'https://www.google.com',
        'https://www.youtube.com',
        'https://www.facebook.com'
    ]
    speeds = []
    for url in urls:
        try:
            start_time = time()
            response = requests.get(url, headers=headers, proxies=proxy_dict, timeout=30, verify=True)
            if response.status_code == 200:
                speed = time() - start_time
                speeds.append(speed)
        except:
            continue
    return round(sum(speeds) / len(speeds), 2) if speeds else 999

def get_country(proxy_dict):
    try:
        response = requests.get('http://ip-api.com/json', proxies=proxy_dict, timeout=10)
        data = response.json()
        if data['status'] == 'success':
            return f"{data['country']} ({data['countryCode']})"
    except:
        pass
    return "Неизвестно"

def main_checker(proxy_type, proxy, position):
    if cancel_all:
        raise KeyboardInterrupt

    checked[position] = None

    try:
        proxy_dict = {
            "http": f"{proxy_type}://{proxy}",
            "https": f"{proxy_type}://{proxy}",
        }

        agent = Headers(headers=False).generate()['User-Agent']
        headers = {'User-Agent': f'{agent}'}

        # Получаем страну перед проверкой скорости
        country = get_country(proxy_dict)
        speed = test_speed(proxy_dict, headers)
        
        if speed == 999:
            raise Exception("Timeout")

        speed_rating = "🚀" if speed < 1 else "⚡" if speed < 3 else "🐌"
        
        print(bcolors.OKBLUE + f"Worker {position+1} | " + bcolors.OKGREEN +
              f'{proxy} | Рабочий | Тип: {proxy_type} | Страна: {country} | Скорость: {speed}s {speed_rating}' + bcolors.ENDC)

        with open('good_proxys.txt', 'a', encoding='utf-8') as f:
            f.write(f'{proxy}|{proxy_type}|{speed}s|{country}\n')

    except Exception as e:
        try:
            e = int(e.args[0])
        except Exception:
            e = ''
        print(bcolors.OKBLUE + f"Worker {position+1} | " + bcolors.FAIL + f'{proxy} | {proxy_type} | Плохой | {e}' + bcolors.ENDC)
        checked[position] = proxy_type


def proxy_check(position):
    sleep(2)
    proxy = proxy_list[position]

    if '|' in proxy:
        splitted = proxy.split('|')
        main_checker(splitted[-1], splitted[0], position)
    else:
        main_checker('http', proxy, position)
        if checked[position] == 'http':
            main_checker('socks4', proxy, position)
        if checked[position] == 'socks4':
            main_checker('socks5', proxy, position)


def main():
    global cancel_all

    cancel_all = False
    pool_number = [i for i in range(total_proxies)]

    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = [executor.submit(proxy_check, position)
                   for position in pool_number]
        done, not_done = wait(futures, timeout=0)
        try:
            while not_done:
                freshly_done, not_done = wait(not_done, timeout=5)
                done |= freshly_done
        except KeyboardInterrupt:
            print(bcolors.WARNING + 'Позвольте мне на минутку закончить запущенные потоки.' + bcolors.ENDC)
            cancel_all = True
            for future in not_done:
                _ = future.cancel()
            _ = wait(not_done, timeout=None)
            raise KeyboardInterrupt
        except IndexError:
            print(bcolors.WARNING + 'Количество прокси-серверов меньше, чем потоков. Предоставляйте больше прокси-серверов или меньше потоков. ' + bcolors.ENDC)

    # Сортируем результаты по скорости
    if os.path.exists('good_proxys.txt'):
        with open('good_proxys.txt', 'r', encoding='utf-8') as f:
            proxies = f.readlines()
        
        sorted_proxies = sorted(proxies, key=lambda x: float(x.split('|')[2].replace('s\n', '')))
        
        with open('good_proxys_sorted.txt', 'w', encoding='utf-8') as f:
            f.writelines(sorted_proxies)
        
        print(bcolors.OKGREEN + "\nТоп 5 самых быстрых прокси:" + bcolors.ENDC)
        for proxy in sorted_proxies[:5]:
            proxy_data = proxy.strip().split('|')
            print(bcolors.OKCYAN + f"Прокси: {proxy_data[0]} | Тип: {proxy_data[1]} | Скорость: {proxy_data[2]} | Страна: {proxy_data[3]}" + bcolors.ENDC)


if __name__ == '__main__':
    
    try:
        threads = int(input(bcolors.OKBLUE+'Введите количество потоков (рекомендуем = 1000): ' + bcolors.ENDC))
    except Exception:
        threads = 100

    proxy_list = load_proxy()
    proxy_list = list(set(filter(None, proxy_list)))

    total_proxies = len(proxy_list)
    print(bcolors.OKCYAN + f'Всего прокси : {total_proxies}' + bcolors.ENDC)

    try:
        main()
    except KeyboardInterrupt:
        sys.exit()