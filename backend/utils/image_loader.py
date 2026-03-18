import os
import logging
import asyncio
from pathlib import Path
from functools import partial
from tqdm import tqdm
from sqlalchemy.ext.asyncio import AsyncSession

from backend.ocr import openai_vision
from backend.rag import embeddings
from backend.db import crud
from backend.utils import field_extractor

logger = logging.getLogger(__name__)


async def run_pipeline(app) -> dict:
    """
    Main indexing pipeline: load images, run OCR via OpenAI Vision (returns JSON),
    extract and validate fields, generate embeddings via OpenAI, and insert with
    vectors to PostgreSQL + pgvector.

    Supports MAX_CARDS environment variable for testing with limited card count.
    Returns dict with status and card count.
    """
    assets_dir = os.getenv("ASSETS_DIR", "assets")
    # If ASSETS_DIR is not absolute, resolve it relative to project root
    assets_path = Path(assets_dir) if Path(assets_dir).is_absolute() else Path(assets_dir).resolve()

    if not assets_path.exists():
        logger.error(f"Assets directory not found: {assets_path}")
        return {"status": "error", "message": f"Assets directory not found: {assets_path}"}

    # Get all PNG files
    png_files = sorted(assets_path.glob("*.png"))
    if not png_files:
        logger.warning(f"No PNG files found in {assets_path}")
        return {"status": "ok", "cards_indexed": 0}

    # Check MAX_CARDS limit (for testing with subset of cards)
    max_cards = os.getenv("MAX_CARDS")
    if max_cards:
        try:
            max_cards = int(max_cards)
            if max_cards > 0:
                png_files = png_files[:max_cards]
                logger.info(f"MAX_CARDS={max_cards} limit applied - processing {len(png_files)} cards")
        except ValueError:
            logger.warning(f"Invalid MAX_CARDS value: {max_cards}, ignoring")

    # Set total cards upfront
    app.state.total_cards = len(png_files)
    logger.info(f"Found {len(png_files)} PNG files in {assets_path}")

    # Get database session
    from backend.db.session import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        # Clear existing data for re-indexing
        await crud.delete_all_cards(db)

        cards_indexed = 0

        # Process each image
        for idx, image_path in enumerate(png_files, 1):
            relative_path = f"assets/{image_path.name}"

            try:
                # Check if already indexed (shouldn't happen after delete_all, but for safety)
                if await crud.card_exists(db, relative_path):
                    logger.info(f"Card already indexed: {relative_path}")
                    continue

                # Run OpenAI Vision OCR in executor to avoid blocking event loop
                # Returns JSON dict with extracted fields and confidence scores
                loop = asyncio.get_event_loop()
                ocr_json = await loop.run_in_executor(None, partial(openai_vision.extract, str(image_path)))

                if not ocr_json:
                    logger.warning(f"No OCR data extracted from {image_path.name}")
                    continue

                # Extract and validate structured fields from OCR JSON
                fields = field_extractor.extract(ocr_json)

                # Build full_text from extracted fields for embedding
                # Use non-"Not Available" fields to create meaningful text
                full_text_parts = []
                for key in ['name', 'designation', 'company', 'country', 'phone', 'email', 'address']:
                    if fields[key] != 'Not Available':
                        full_text_parts.append(fields[key])

                full_text = ' '.join(full_text_parts)

                if not full_text.strip():
                    logger.warning(f"No valid text extracted from {image_path.name} after field extraction")
                    continue

                # Log extracted fields with confidence
                confidence = ocr_json.get('confidence', {})
                logger.info(
                    f"[{idx}/{len(png_files)}] {image_path.name}: "
                    f"name={fields['name'][:30]} (conf={confidence.get('name', 0)}), "
                    f"company={fields['company'][:30]} (conf={confidence.get('company', 0)}), "
                    f"designation={fields['designation'][:30]} (conf={confidence.get('designation', 0)}), "
                    f"country={fields['country']} (conf={confidence.get('country', 0)})"
                )

                # Generate embedding using OpenAI text-embedding-3-large
                vector = embeddings.encode(app.state.embedder, full_text)

                # Convert numpy array to bytes for storage in BYTEA column
                embedding_bytes = vector.astype('float32').tobytes()

                # Prepare card data with embedding
                card_data = {
                    **fields,
                    'full_text': full_text,
                    'image_path': relative_path,
                    'embedding': embedding_bytes,  # Store as binary in DB
                }

                # Insert into database (with embedding)
                postgres_id = await crud.insert_card(db, card_data)
                cards_indexed += 1

                # Update progress state
                app.state.cards_indexed = cards_indexed
                app.state.total_cards = len(png_files)

            except Exception as e:
                logger.error(f"Error processing {image_path.name}: {e}", exc_info=True)
                continue

        # Summary
        if cards_indexed > 0:
            logger.info(f"Successfully indexed {cards_indexed} cards into PostgreSQL with pgvector")
            return {"status": "ok", "cards_indexed": cards_indexed}
        else:
            logger.warning("No cards indexed")
            return {"status": "ok", "cards_indexed": 0}
