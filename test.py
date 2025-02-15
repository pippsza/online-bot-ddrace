import asyncio
from ddapi import DDnetApi

# Массив имен игроков для поиска
players_to_find = ["nameless tee", "pippsza"]  # Пример списка игроков


async def fetch_server_info():
    api = DDnetApi()
    server_info = await api.master()

    if server_info and hasattr(server_info, 'servers'):
        for player_name_to_find in players_to_find:  # Перебираем всех игроков из списка
            found = False  # Флаг для проверки наличия игрока
            for server in server_info.servers:
                for client in server.info.clients:
                    if client.name.lower() == player_name_to_find.lower():  # Сравниваем с именем игрока
                        found = True
                        print(
                            f"Игрок {client.name} найден на сервере: {server.info.name}")
                        print(f"Карта: {server.info.map.name}")
                        print(f"Статус: {'AFK' if client.afk else 'Active'}")
                        break  # Выход из цикла, так как игрок найден

                if found:
                    break  # Если игрок найден, выходим из внешнего цикла

            if not found:
                print(f"Игрок {player_name_to_find} не найден на сервере.")

    else:
        print("Не удалось получить информацию о серверах.")

    await api.close()  # Закрываем соединение

if __name__ == "__main__":
    asyncio.run(fetch_server_info())
