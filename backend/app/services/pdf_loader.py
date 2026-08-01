from pathlib import Path

import fitz


class PDFLoader:
    @staticmethod
    def extract_text(pdf_path: Path):
        """
        Extract text from every page of a PDF.

        Returns:
            List[dict]:
            [
                {
                    "page": 1,
                    "text": "..."
                }
            ]
        """

        pages = []

        try:
            document = fitz.open(pdf_path)

            for page_number, page in enumerate(document):

                text = page.get_text("text").strip()

                pages.append(
                    {
                        "page": page_number + 1,
                        "text": text,
                    }
                )

            document.close()

        except Exception as e:
            raise ValueError(
                f"Failed to read PDF '{pdf_path.name}': {str(e)}"
            )

        return pages