from typing import Optional
from sqlmodel import Session, select
from models import Team, Offer

class TeamRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_team_by_id(self, team_id: int) -> Optional[Team]:
        """
        Retrieves a team by its primary key.
        """
        return self.session.get(Team, team_id)
    
    def add_team(self, team: Team):
        query = select(Team).where(Team.user_id == team.user_id) 
        team_to_update = self.session.exec(query).first()
        if team_to_update is not None:
            team_to_update.name = team.name
            team = team_to_update
        else:
            self.session.add(team)
        self.session.commit()
        self.session.refresh(team) 
        return team

    def get_team_by_user_id(self, user_id: int) -> Optional[Team]:
        """
        Finds the team owned by a specific user.
        Note: Checks the Foreign Key directly for performance.
        """
        # Assuming your Team model has a foreign key field like 'owner_id' or 'user_id'
        # This is more efficient than joining tables via 'Team.owner'.
        query = select(Team).where(Team.user_id == user_id) 
        team = self.session.exec(query).first()
        return team

    def add_player_from_offer(self, accepted_offer: Offer) -> None:
        """
        Moves the player in the offer to the team of the user who made the offer.
        """
        # 1. Resolve the buyer's team
        # We assume relations (offer.user -> user.team) are set up in your models
        buyer_team = accepted_offer.user.team

        if not buyer_team:
            raise ValueError(f"User {accepted_offer.user_id} does not have a team.")

        # 2. Add the player to the team (SQLAlchemy handles the relationship table update)
        buyer_team.players.append(accepted_offer.player)
        
        # 3. Explicitly mark the team as modified (good practice) and commit
        self.session.add(buyer_team)
        self.session.commit()
        # Optional: Refresh if you need to read updated state immediately
        self.session.refresh(buyer_team)