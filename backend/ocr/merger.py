def merge(lines: list[str]) -> str:
    """Join non-empty text lines into full_text string."""
    return '\n'.join(line.strip() for line in lines if line.strip())
