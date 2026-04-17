from typing import Optional
from fastapi import HTTPException
from pydantic import EmailStr
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select
from models import User, Offer


# Custom exception for cleaner error handling
class UserAlreadyExistsError(Exception):
    pass


class UserRepository:
    def __init__(self, session: Session):
        self.session = session

    def add_user(self, user: User) -> User:
        self.session.add(user)
        try:
            self.session.commit()
            self.session.refresh(user)  # Refresh to get the generated ID back
            return user
        except IntegrityError:
            self.session.rollback()  # Always rollback on error
            raise UserAlreadyExistsError("A user with this email already exists.")

    def get_user_by_email(self, email: EmailStr) -> Optional[User]:
        query = select(User).where(User.email == email)
        return self.session.exec(query).first()

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        # 'session.get' is the most efficient way to fetch by Primary Key
        user =  self.session.get(User, user_id)
        if user is None:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found") 
        else:
            return user

    def get_user_by_auth_id(self, auth_id: str) -> Optional[User]:
        # 'session.get' is the most efficient way to fetch by Primary Key
        query = select(User).where(User.auth0_id == auth_id)
        return self.session.exec(query).first()

    def delete_user(self, user_id: int) -> bool:
        user = self.get_user_by_id(user_id)
        if not user:
            return False  # User didn't exist

        self.session.delete(user)
        self.session.commit()
        return True

    def update_user_budget(self, best_offer: Offer) -> None:
        # Assuming best_offer.user is already loaded or attached to session
        # If not, you might need to fetch the user first via ID
        purchaser = best_offer.user
        if purchaser:
            purchaser.budget = purchaser.budget - best_offer.amount
            self.session.add(purchaser)  # Mark as modified
            self.session.commit()
            self.session.refresh(purchaser)
