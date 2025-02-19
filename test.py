import asyncio
from ddapi import DDnetApi

# Массив имен игроков для поиска
players_to_find = ["nameless tee", "pippsza"]  # Пример списка игроков

# Словарь для хранения состояния игроков
current_status = {player: None for player in players_to_find}
previous_groups = {'online': [], 'afk': [], 'offline': []}


async def fetch_server_info():
    api = DDnetApi()
    while True:
        print('cycle')
        server_info = await api.master()

        online_players = []
        afk_players = []
        offline_players = []

        if server_info and hasattr(server_info, 'servers'):
            # Перебираем всех игроков из списка
            for player_name_to_find in players_to_find:
                found = False
                player_status = None  # Переменная для текущего статуса игрока
                for server in server_info.servers:
                    for client in server.info.clients:
                        if client.name == player_name_to_find:  # Сравниваем с именем игрока
                            found = True
                            player_status = 'AFK' if client.afk else 'Active'
                            # Добавляем игрока в соответствующую категорию
                            if client.afk:
                                afk_players.append(client.name)
                            else:
                                online_players.append(client.name)
                            break

                    if found:
                        break

                if not found:
                    offline_players.append(player_name_to_find)

                # Проверка, изменился ли статус игрока
                if current_status[player_name_to_find] != player_status:
                    # Если статус изменился, выводим данные
                    if player_status:
                        print(
                            f"Игрок {player_name_to_find} изменил статус на {player_status}.")
                    current_status[player_name_to_find] = player_status

        else:
            print("Не удалось получить информацию о серверах.")

        # Проверка изменений в группах игроков
        if (sorted(online_players) != sorted(previous_groups['online']) or
            sorted(afk_players) != sorted(previous_groups['afk']) or
                sorted(offline_players) != sorted(previous_groups['offline'])):
            if online_players:
                print(f"\nОнлайн игроки: {', '.join(online_players)}")
            if afk_players:
                print(f"Игроки онлайн, но AFK: {', '.join(afk_players)}")
            if offline_players:
                print(f"Оффлайн игроки: {', '.join(offline_players)}")

            # Обновляем предыдущие группы
            previous_groups['online'] = sorted(online_players)
            previous_groups['afk'] = sorted(afk_players)
            previous_groups['offline'] = sorted(offline_players)

        # Задержка 1 минута
        await asyncio.sleep(6)

    await api.close()  # Закрываем соединение

if __name__ == "__main__":
    asyncio.run(fetch_server_info())
