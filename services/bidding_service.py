from typing import Optional
from fastapi import HTTPException

from models import TEAM_SIZE_BY_ROLE, Offer, Team, User
from repositories.offer_repository import OfferRepository
from repositories.player_repository import PlayerRepository
from repositories.team_repository import TeamRepository
from repositories.user_repository import UserRepository


class BiddingService:
    def __init__(
        self,
        user_repo: UserRepository,
        offer_repo: OfferRepository,
        player_repo: PlayerRepository,
        team_repo: TeamRepository,
    ):
        self.user_repo = user_repo
        self.offer_repo = offer_repo
        self.player_repo = player_repo
        self.team_repo = team_repo

    def is_valid_bid(self, offer: Offer) -> Optional[bool]:
        # 1. Fetch full objects (User and Player) to validate
        # We assume the incoming 'offer' object has user_id and player_id
        user = self.user_repo.get_user_by_id(offer.user_id)
        player = self.player_repo.get_player_by_id(offer.player_id)

        if not user or not player:
            raise HTTPException(status_code=404, detail="User or Player not found")

        # 2. Check if player is already owned (purchase_cost is set).
        if player.purchase_cost is not None:
            raise HTTPException(status_code=400, detail="Player already has an owner!")
        # 3. Validate Budget
        # Logic: User must have enough money AND enough left for empty slots
        # Assuming user.team is a list of players. If it's a relation, ensure it's loaded.
        current_team_size = len(user.team.players) if user.team else 0
        slots_needed = TEAM_SIZE_BY_ROLE["ALL"] - current_team_size - 1

        if (user.budget - offer.amount) - slots_needed < 0:
            raise HTTPException(status_code=400, detail="You don't have enough budget!")

        # 4. Validate Roles
        # Logic: Check if the specific role slot is full
        if user.team:
            role_count = sum(1 for p in user.team.players if p.role == player.role)
            if role_count >= TEAM_SIZE_BY_ROLE.get(player.role, 0):
                raise HTTPException(
                    status_code=400, detail="You are already full for this role!"
                )

            return True

    # --- New Logic: Placing a Bid ---
    def place_bid(self, offer: Offer) -> Optional[Offer]:
        if self.is_valid_bid(offer):
            # 5. Save
            return self.offer_repo.save_offer(offer)

    def is_best_bid(self, offer: Offer) -> bool:
        """Check if the offer is the best bid for the player."""
        best_offers = self.offer_repo.get_best_offers_for_player(offer.player_id)
        if not best_offers:
            return True
        return offer.amount > best_offers[0].amount

    def get_best_offers(self, player_id: int):
        return self.offer_repo.get_best_offers_for_player(player_id)

    # --- Existing Logic: Resolving Auction ---
    def resolve_auction(self, user_id: int, player_id: int) -> dict:
        """
        Resolves the auction and returns details about the winner.
        """
        best_offers = self.offer_repo.get_best_offers_for_player(player_id)
        player = self.player_repo.get_player_by_id(player_id)
        
        if not best_offers:
            player = self.player_repo.set_player_purchase_cost(0, player)
            return {"isPurchaser": False, "purchaserName": None, "auctionClosed": True}
        elif len(best_offers) == 1:
            winner_offer = best_offers[0]
            winner = winner_offer.user
            if winner.id == user_id:
            # Execute the transaction logic we wrote previously
                self.user_repo.update_user_budget(winner_offer)
                self.team_repo.add_player_from_offer(winner_offer)
                self.player_repo.set_player_purchase_cost(winner_offer.amount, player)
            user = self.user_repo.get_user_by_id(user_id)
            return {
            "isPurchaser": winner.id == user_id,
            "purchaserName": winner.email,
            "userBudget": user.budget,
            "bestOffer": winner_offer.amount,
            "auctionClosed": True,
            }
        else:
            best_offer = best_offers[0]
            highest_bidders = []
            if best_offers:
                for offer in best_offers:
                    highest_bidders.append(offer.user.id)
            if user_id in highest_bidders:
                # Execute the transaction logic we wrote previously
                self.user_repo.update_user_budget(best_offers[0])
            user = self.user_repo.get_user_by_id(user_id)
            return {
                "isPurchaser": user_id in highest_bidders,
                "purchaserName": None,
                "userBudget": user.budget,
                "bestOffer": best_offer.amount,
                "auctionClosed": False,
            }

    def get_all_players(self):
        return self.player_repo.get_all_players()

    def get_player(self, player_id: int):
        player = self.player_repo.get_player_by_id(player_id)
        if not player:
            # Service layer handles the "Not Found" logic
            raise HTTPException(status_code=404, detail=f"Player {player_id} not found")
        return player

    def get_team_players(self, team_id: int):
        """
        Returns all players belonging to a specific team.
        """
        # We delegate to the player_repo which we already injected
        return self.player_repo.get_players_by_team(team_id)

    def get_team_by_user(self, user_id: int):
        return self.team_repo.get_team_by_user_id(user_id)

    def add_team(self, team: Team):
        return self.team_repo.add_team(team)

    def register_user(self, user: User) -> User:
        try:
            return self.user_repo.add_user(user)
        except Exception:
            # In a real app, catch the specific UserAlreadyExistsError we defined in the repo
            raise HTTPException(
                status_code=409, detail="User with this email already exists."
            )

    def get_user_by_auth_id(self, auth_id: int) -> User:
        user = self.user_repo.get_user_by_auth_id(auth_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    def get_user(self, user_id: int) -> User:
        user = self.user_repo.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    def delete_user(self, user_id: int) -> dict:
        success = self.user_repo.delete_user(user_id)
        if not success:
            raise HTTPException(status_code=404, detail="User not found")
        return {"message": "User deleted successfully"}
