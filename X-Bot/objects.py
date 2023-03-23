import helper
import asyncio


class Account:
    def __init__(self, email: str, password: str) -> None:
        self.email, self.password = email, password


class Token:
    def __init__(self, token: str, uhs: str, user_token: str, xuid: str) -> None:
        self.token, self.uhs, self.user_token, self.xuid = token, uhs, user_token, xuid


class Stats:
    def __init__(self, gamertag: str, user_id: int) -> None:
        self.combinations = helper.generate_combinations(gamertag)

        self.running, self.reserved = True, False

        self.attempts, self.rl, self.rs = 0, 0, 0

        self.user_id = user_id

        self.index = -1


    def current_combination(self) -> any:
        self.index += 1
        if self.index >= len(self.combinations):
            self.index = 0

        return self.combinations[self.index]
        

    async def calculate_rs(self) -> None:
        while self.running:
            before = self.attempts
            await asyncio.sleep(1)
            self.rs = self.attempts - before
