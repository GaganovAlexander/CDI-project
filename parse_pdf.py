import fitz

from preprocessing_text import lemmatize_text


def parse_pdf_to_paragraphs(file_path: str):
    with fitz.open(file_path) as pdf_document:
        result = []
        document_name = file_path.split('/')[-1]

        for page_number in range(pdf_document.page_count):
            page = pdf_document.load_page(page_number)
            page_data = page.get_text("dict")

            current_paragraph = []
            previous_indent = None
            paragraph_number = 1
            paragraph_bbox = None

            for block in page_data['blocks']:
                if 'lines' not in block:
                    continue

                current_indent = block['bbox'][0]
                text = ''
                for line in block['lines']:
                    text += line['spans'][0]['text'].lstrip()

                if previous_indent is None:
                    previous_indent = current_indent

                if current_indent > previous_indent and current_paragraph:
                    text_ = " ".join(current_paragraph)
                    result.append({
                        "document_name": document_name,
                        "page_number": page_number + 1,
                        "paragraph_number": paragraph_number,
                        "text": text_,
                        "lemmatized_text": lemmatize_text(text_),
                        "bbox": paragraph_bbox
                    })
                    paragraph_number += 1
                    current_paragraph = []
                    paragraph_bbox = block['bbox']

                if text:
                    current_paragraph.append(text)
                    if paragraph_bbox:  
                        paragraph_bbox = (
                            min(paragraph_bbox[0], block['bbox'][0]),
                            min(paragraph_bbox[1], block['bbox'][1]),
                            max(paragraph_bbox[2], block['bbox'][2]),
                            max(paragraph_bbox[3], block['bbox'][3])
                        )

                previous_indent = current_indent

            if current_paragraph:
                text_ = " ".join(current_paragraph)
                result.append({
                    "document_name": document_name,
                    "page_number": page_number + 1,
                    "paragraph_number": paragraph_number,
                    "text": text_,
                    "lemmatized_text": lemmatize_text(text_),
                    "bbox": paragraph_bbox  
                })
            yield int((page_number + 1) / pdf_document.page_count * 100)

    yield result
