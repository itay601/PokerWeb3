from pydantic import BaseModel


# Request Models
class CreateGameRequest(BaseModel):
    buy_in_ether: float

class JoinGameRequest(BaseModel):
    game_id: int
    buy_in_ether: float
    player_account: str

class BetRequest(BaseModel):
    game_id: int
    amount: int
    player_account: str

class GameActionRequest(BaseModel):
    game_id: int
    player_account: str