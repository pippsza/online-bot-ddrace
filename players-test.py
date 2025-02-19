import asyncio
from ddapi import DDnetApi, DDPlayer


async def main():
    obj = DDnetApi()
    nickname = "Cor"
    user: DDPlayer = await obj.player(nickname)
    if user is None:
        return "Player not found"

    print(f"{user.player}: {user.points.points}")
    # Cor: 31473 
    await obj.close()  # Closing client Not necessary
    assert isinstance(user, DDPlayer)


asyncio.run(main())