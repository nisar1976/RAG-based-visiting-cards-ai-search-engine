from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from .models import Card


async def insert_card(db: AsyncSession, data: dict) -> int:
    """Insert a card and return its ID."""
    card = Card(**data)
    db.add(card)
    await db.commit()
    await db.refresh(card)
    return card.id


async def get_card_by_id(db: AsyncSession, card_id: int) -> Card | None:
    """Get a card by ID."""
    result = await db.execute(select(Card).where(Card.id == card_id))
    return result.scalar_one_or_none()


async def get_all_cards(db: AsyncSession) -> list[Card]:
    """Get all cards."""
    result = await db.execute(select(Card))
    return result.scalars().all()


async def delete_all_cards(db: AsyncSession) -> None:
    """Delete all cards."""
    await db.execute(delete(Card))
    await db.commit()


async def card_exists(db: AsyncSession, image_path: str) -> bool:
    """Check if a card with the given image_path already exists."""
    result = await db.execute(select(Card).where(Card.image_path == image_path))
    return result.scalar_one_or_none() is not None
