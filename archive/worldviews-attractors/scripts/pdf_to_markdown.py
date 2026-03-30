#!/usr/bin/env python3
"""Convert a PDF to Markdown and extract images using PyMuPDF."""
from __future__ import annotations

import argparse
from pathlib import Path

import fitz  # PyMuPDF


def _write_image(doc: fitz.Document, xref: int, out_dir: Path, name: str) -> Path:
    img = doc.extract_image(xref)
    ext = img.get("ext", "png")
    out_path = out_dir / f"{name}.{ext}"
    out_path.write_bytes(img["image"])
    return out_path


def _block_text(block: dict) -> str:
    lines = []
    for line in block.get("lines", []):
        spans = line.get("spans", [])
        line_text = "".join(span.get("text", "") for span in spans).rstrip()
        lines.append(line_text)
    text = "\n".join(lines).strip()
    return text


def pdf_to_markdown(pdf_path: Path, md_path: Path, images_dir: Path) -> None:
    doc = fitz.open(pdf_path)
    images_dir.mkdir(parents=True, exist_ok=True)

    md_lines: list[str] = []
    image_cache: dict[int, str] = {}

    for page_index, page in enumerate(doc, start=1):
        md_lines.append(f"\n\n## Page {page_index}\n")
        blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_IMAGES).get("blocks", [])
        img_index = 0

        for block in blocks:
            btype = block.get("type")
            if btype == 0:
                text = _block_text(block)
                if text:
                    md_lines.append(text)
                    md_lines.append("")
            elif btype == 1:
                xref = block.get("xref")
                if not xref:
                    continue
                if xref in image_cache:
                    filename = image_cache[xref]
                else:
                    img_index += 1
                    filename = f"page_{page_index}_img_{img_index}"
                    _write_image(doc, xref, images_dir, filename)
                    image_cache[xref] = f"{filename}"
                # Use provided filename without duplicating extension
                existing = Path(filename).name
                # Find actual file path (may have extension from extraction)
                matches = list(images_dir.glob(f"{existing}.*"))
                if matches:
                    rel_path = f"{images_dir.name}/{matches[0].name}"
                else:
                    rel_path = f"{images_dir.name}/{existing}"
                md_lines.append(f"![Page {page_index} image]({rel_path})")
                md_lines.append("")

        # Fallback: ensure any remaining images are extracted even if not in text blocks.
        for img in page.get_images(full=True):
            xref = img[0]
            if xref in image_cache:
                continue
            img_index += 1
            filename = f"page_{page_index}_img_{img_index}"
            _write_image(doc, xref, images_dir, filename)
            image_cache[xref] = filename
            matches = list(images_dir.glob(f"{filename}.*"))
            if matches:
                rel_path = f"{images_dir.name}/{matches[0].name}"
            else:
                rel_path = f"{images_dir.name}/{filename}"
            md_lines.append(f"![Page {page_index} image]({rel_path})")
            md_lines.append("")

    md_path.write_text("\n".join(md_lines).strip() + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert PDF to Markdown and extract images.")
    parser.add_argument("pdf", type=Path, help="Path to PDF")
    parser.add_argument("--out", type=Path, help="Output markdown path")
    parser.add_argument("--images-dir", type=Path, help="Directory to store images")
    args = parser.parse_args()

    pdf_path = args.pdf
    md_path = args.out or pdf_path.with_suffix(".md")
    images_dir = args.images_dir or pdf_path.with_suffix("").with_name(f"{pdf_path.stem}_images")

    pdf_to_markdown(pdf_path, md_path, images_dir)


if __name__ == "__main__":
    main()
