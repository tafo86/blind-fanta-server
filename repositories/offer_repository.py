from typing import Optional, Sequence
from sqlalchemy import func
from sqlmodel import Session, select
from models import Offer

class OfferRepository:
    def __init__(self, session: Session):
        self.session = session

    def save_offer(self, offer: Offer) -> Offer:
        """
        Updates an existing offer amount if the user has already made an offer 
        on this player, otherwise creates a new offer.
        """
        # 1. Check if an offer already exists for this User + Player combo
        query = select(Offer).where(
            Offer.player_id == offer.player_id,
            Offer.user_id == offer.user_id,
        )
        existing_offer = self.session.exec(query).first()

        if existing_offer:
            # 2. Update the existing record (Upsert logic)
            # Standardized on 'amount' to match the best_offer logic
            existing_offer.amount = offer.amount 
            final_offer = existing_offer
        else:
            # 3. Insert the new record
            final_offer = offer

        self.session.add(final_offer)
        self.session.commit()
        self.session.refresh(final_offer)

        return final_offer

    def get_best_offers_for_player(self, player_id: int) -> Optional[Sequence[Offer]]:
        # 1. Create a subquery to find the highest amount for this player
        max_value_subquery = (
            select(func.max(Offer.amount))
            .where(Offer.player_id == player_id)
            .scalar_subquery()
        )

        # 2. Select all offers for this player where the amount equals that max value
        statement = (
            select(Offer)
            .where(Offer.player_id == player_id)
            .where(Offer.amount == max_value_subquery)
        )

        return self.session.exec(statement).all()