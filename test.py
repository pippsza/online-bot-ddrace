import asyncio
from ddapi import DDnetApi

# Массив имен игроков для поиска
players_to_find = ["nameless tee", "pippsza"]  # Пример списка игроков

# Словарь для хранения состояния игроков
current_status = {player: None for player in players_to_find}
previous_groups = {'online': [], 'afk': [], 'offline': []}

# Пример списка друзей
friends_list = ["nameless tee", "pippsza"]  # Ваш список друзей

async def fetch_server_info():
    api = DDnetApi()
    while True:
        try:
            print('Запуск цикла...')
            server_info = await api.master()

            online_players = []
            afk_players = []
            offline_players = []

            if server_info and hasattr(server_info, 'servers'):
                # Перебираем все серверы
                for server in server_info.servers:
                    server_name = server.info.name
                    map_name = server.info.map.name
                    game_type = server.info.game_type

                    # Перебираем всех игроков на сервере
                    for client in server.info.clients:
                        player_name = client.name
                        afk_status = client.afk
                        player_details = f'{player_name} (AFK: {afk_status})'

                        # Проверяем, является ли игрок в списке друзей
                        if player_name in friends_list:
                            if player_name in players_to_find:
                                if afk_status:
                                    afk_players.append((player_name, game_type, server_name, map_name))
                                else:
                                    online_players.append((player_name, game_type, server_name, map_name))
                            else:
                                offline_players.append((player_name, game_type, server_name, map_name))

            # Создаем вывод с учетом всех игроков
            print("Игроки онлайн:")
            for player, game_type, server, map_name in online_players:
                print(f"{player} - {game_type}, {server}, {map_name}")

            print("\nИгроки в AFK:")
            for player, game_type, server, map_name in afk_players:
                print(f"{player} - {game_type}, {server}, {map_name}")

            # Для оффлайн игроков из списка друзей, которых нет на серверах
            print("\nИгроки оффлайн:")
            for player in players_to_find:
                if player not in [p[0] for p in online_players + afk_players]:
                    print(player)

        except Exception as e:
            print(f"Ошибка при получении данных: {e}")
        
        await asyncio.sleep(10)  # Пауза между запросами

# Запуск асинхронного процесса
asyncio.run(fetch_server_info())
