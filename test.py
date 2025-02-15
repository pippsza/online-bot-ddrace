import asyncio
from ddapi import DDnetApi, DDPlayer


async def check_player_on_server(nickname: str):
    # Создаем объект для работы с API
    obj = DDnetApi()

    # Получаем список всех игроков на сервере
    server_info = await obj.query()

    # Перебираем всех игроков на сервере
    player_found = False
    for player in server_info['data']:
        if player.name.lower() == nickname.lower():  # Сравниваем имена игроков (регистр не важен)
            player_found = True
            print(f"Player {nickname} found with {player.points} points")
            break

    # Если игрок не найден
    if not player_found:
        print(f"Player {nickname} not found on the server.")

    # Закрываем соединение
    await obj.close()

# Вводим имя игрока, которого ищем
nickname_to_check = "Cor"  # Замените на нужный ник игрока

# Запуск асинхронной функции
asyncio.run(check_player_on_server(nickname_to_check))
