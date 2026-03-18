import logging
from pathlib import Path
from fastapi import APIRouter, Depends, Query, HTTPException, Request
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from backend.db.session import get_db
from backend.db import crud
from backend.rag import embeddings
from backend.rag import vector_search
from backend.utils import image_loader

logger = logging.getLogger(__name__)

router = APIRouter()


class CardResponse(BaseModel):
    """Card response model."""
    id: int
    name: str
    designation: str
    company: str
    country: str
    phone: str
    email: str
    address: str
    full_text: str
    image_path: str

    class Config:
        from_attributes = True


@router.post("/process-assets")
async def process_assets(request: Request) -> dict:
    """
    POST /process-assets
    Trigger full indexing of all cards from assets directory.
    """
    try:
        result = await image_loader.run_pipeline(request.app)
        return result
    except Exception as e:
        logger.error(f"Error in process-assets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search-card")
async def search_card(
    request: Request,
    q: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db),
) -> CardResponse:
    """
    GET /search-card?q=<query>
    Semantic search for matching card using query string.

    Workflow:
    1. Validate embedder is initialized (auto-indexing may still be in progress)
    2. Encode query string to 3072-dim embedding using OpenAI text-embedding-3-large
    3. Search database for top-1 similar card using L2 distance
    4. Fetch and return card metadata as CardResponse (includes image_path)

    Returns:
        CardResponse with id, name, designation, company, country, phone, email, address, image_path
        404: No matching card found
        503: Embedder not ready (indexing in progress)
    """
    # Implementation: Check embedder state, encode query, vector search, fetch from DB
    pass


@router.get("/get-card/{card_id}")
async def get_card(
    card_id: int,
    db: AsyncSession = Depends(get_db),
) -> CardResponse:
    """
    GET /get-card/{id}
    Fetch card metadata by ID.
    """
    try:
        card = await crud.get_card_by_id(db, card_id)
        if not card:
            raise HTTPException(status_code=404, detail="Card not found")
        return CardResponse.model_validate(card)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get-card: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download-card/{card_id}")
async def download_card(
    card_id: int,
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    """
    GET /download-card/{id}
    Download card image (attachment).
    """
    try:
        card = await crud.get_card_by_id(db, card_id)
        if not card:
            raise HTTPException(status_code=404, detail="Card not found")

        image_path = Path(card.image_path).resolve()
        if not image_path.exists():
            raise HTTPException(status_code=404, detail="Image file not found")

        return FileResponse(
            path=image_path,
            media_type="image/png",
            filename=f"card_{card_id}.png"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in download-card: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/image/{card_id}")
async def get_image(
    card_id: int,
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    """
    GET /image/{id}
    Serve card image (inline).
    """
    try:
        card = await crud.get_card_by_id(db, card_id)
        if not card:
            raise HTTPException(status_code=404, detail="Card not found")

        image_path = Path(card.image_path).resolve()
        if not image_path.exists():
            raise HTTPException(status_code=404, detail="Image file not found")

        return FileResponse(
            path=image_path,
            media_type="image/png"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in image: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/all-cards")
async def list_all_cards(db: AsyncSession = Depends(get_db)) -> list[CardResponse]:
    """
    GET /all-cards
    Fetch all indexed cards.
    """
    try:
        cards = await crud.get_all_cards(db)
        return [CardResponse.model_validate(c) for c in cards]
    except Exception as e:
        logger.error(f"Error in all-cards: {e}")
        raise HTTPException(status_code=500, detail=str(e))
