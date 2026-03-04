from typing import List, Optional

from fastapi import HTTPException
from sqlmodel import Session, select

from models import Player


class PlayerRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_player_by_id(self, player_id: int) -> Optional[Player]:
        """
        Retrieves a player by ID. Returns None if not found.
        Uses session.get() for primary key optimization.
        """
        player = self.session.get(Player, player_id)
        if player is None:
             raise HTTPException(status_code=404, detail=f"Player {player_id} not found") 
        else:
            return player

    def get_all_players(self) -> List[Player]:
        """Retrieves all players in the database."""
        query = select(Player)
        return list(self.session.exec(query).all())

    def get_players_by_team(self, team_id: int) -> List[Player]:
        """Retrieves all players belonging to a specific team."""
        query = select(Player).where(Player.team_id == team_id)
        return list(self.session.exec(query).all())
    
    def set_player_purchase_cost(self, amount: int, player: Player):
        player.purchase_cost = amount
        self.session.add(player)
        self.session.commit()
        self.session.refresh(player)