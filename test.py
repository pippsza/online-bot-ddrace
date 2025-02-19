import asyncio
from ddapi import DDnetApi

# Массив имен игроков для поиска (это же и список друзей)
players_to_find = ["nameless tee", "pippsza"]  # Пример списка игроков

# Словари для хранения состояний игроков
previous_online_players = set()
previous_afk_players = set()
previous_offline_players = set()

async def fetch_server_info():
    api = DDnetApi()
    while True:
        try:
            print('Запуск цикла...')
            server_info = await api.master()

            online_players = set()
            afk_players = set()
            offline_players = set()

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

                        # Проверяем, является ли игрок в списке для поиска
                        if player_name in players_to_find:
                            if afk_status:
                                afk_players.add((player_name, game_type, server_name, map_name))
                            else:
                                online_players.add((player_name, game_type, server_name, map_name))

            # Проверяем, были ли изменения в состояниях
            if online_players != previous_online_players:
                print("Игроки онлайн:")
                for player, game_type, server, map_name in online_players:
                    print(f"{player} - {game_type}, {server}, {map_name}")
                previous_online_players.clear()
                previous_online_players.update(online_players)

            if afk_players != previous_afk_players:
                print("\nИгроки в AFK:")
                for player, game_type, server, map_name in afk_players:
                    print(f"{player} - {game_type}, {server}, {map_name}")
                previous_afk_players.clear()
                previous_afk_players.update(afk_players)

            # Для оффлайн игроков из списка, которых нет на серверах
            if offline_players != previous_offline_players:
                print("\nИгроки оффлайн:")
                for player in players_to_find:
                    if player not in [p[0] for p in online_players + afk_players]:
                        print(player)
                previous_offline_players.clear()
                previous_offline_players.update(offline_players)

        except Exception as e:
            print(f"Ошибка при получении данных: {e}")
        
        await asyncio.sleep(10)  # Пауза между запросами

# Запуск асинхронного процесса
asyncio.run(fetch_server_info())
