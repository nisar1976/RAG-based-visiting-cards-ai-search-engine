'use client';

import { Card, getDownloadUrl } from '@/lib/api';

interface ActionButtonsProps {
  card: Card | null;
}

export default function ActionButtons({ card }: ActionButtonsProps) {
  if (!card) {
    return null;
  }

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="action-buttons">
      <a
        href={getDownloadUrl(card.id)}
        download={`card_${card.id}.png`}
        className="button button-download"
      >
        ↓ Download
      </a>
      <button onClick={handlePrint} className="button button-print">
        ⎙ Print
      </button>
    </div>
  );
}
