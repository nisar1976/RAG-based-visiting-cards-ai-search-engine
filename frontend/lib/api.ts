const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface Card {
  id: number;
  name: string;
  designation: string;
  company: string;
  country: string;
  phone: string;
  email: string;
  address: string;
  full_text: string;
  image_path: string;
}

export interface HealthStatus {
  status: string;
  embedder_ready: boolean;
  indexing_status: 'idle' | 'running' | 'done' | 'error';
  cards_indexed: number;
  total_cards: number;
  indexing_error?: string | null;
}

export async function getHealth(): Promise<HealthStatus> {
  const response = await fetch(`${BASE_URL}/health`);
  if (!response.ok) throw new Error('Health check failed');
  return response.json();
}

export async function searchCard(q: string): Promise<Card> {
  /**
   * GET /search-card?q=<query>
   * Sends query to backend for semantic search.
   * Handles errors: 404 (no match), 503 (indexing not ready)
   */
  // Implementation: fetch with URL-encoded query parameter, parse JSON response
  // throw appropriate errors based on status codes
}

export async function getCard(id: number): Promise<Card> {
  /**
   * GET /get-card/{id}
   * Fetch single card metadata by ID
   */
  // Implementation: fetch card by ID, handle 404
}

export async function getAllCards(): Promise<Card[]> {
  /**
   * GET /all-cards
   * Fetch all indexed cards for table view
   */
  // Implementation: fetch all cards array from backend
}

export async function processAssets(): Promise<{ status: string; cards_indexed: number }> {
  /**
   * POST /process-assets
   * Trigger full indexing/re-indexing of all card images from assets directory
   * Runs OCR, field extraction, and embedding generation
   */
  // Implementation: POST request to trigger backend indexing pipeline
}

export function getImageUrl(cardId: number): string {
  return `${BASE_URL}/image/${cardId}`;
}

export function getDownloadUrl(cardId: number): string {
  return `${BASE_URL}/download-card/${cardId}`;
}
