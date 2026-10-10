import os
import re
import json
import hashlib
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from rag.models import DocumentMetadata, KnowledgeChunk

logger = logging.getLogger("isense_ingestion")

def compute_file_hash(filepath: str) -> str:
    """Computes SHA-256 digest of file content for tamper detection and deduplication."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

def clean_text(text: str) -> str:
    """
    Cleans extraction artifacts without altering legal and technical regulatory meanings:
    - Normalizes irregular linebreaks
    - Removes zero-width and non-printable control characters
    - Collapses excess spaces while preserving paragraph breaks
    """
    if not text:
        return ""
    # Normalize unicode spaces
    text = text.replace("\u00a0", " ").replace("\u200b", "").replace("\ufeff", "")
    # Normalize CRLF
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Remove control characters except standard whitespace
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    # Collapse multiple inline spaces while keeping newlines
    text = re.sub(r'[ \t]+', ' ', text)
    # Collapse 3+ newlines to double newline
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def parse_markdown_with_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
    """Extracts YAML frontmatter metadata and markdown body."""
    meta = {}
    body = content
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            raw_meta = parts[1]
            body = parts[2]
            for line in raw_meta.strip().split("\n"):
                if ":" in line:
                    key, val = line.split(":", 1)
                    meta[key.strip()] = val.strip().strip('"').strip("'")
    return meta, body

def extract_text_from_pdf(file_path: str) -> Tuple[str, List[Tuple[int, str]]]:
    """
    Extracts text from PDF preserving page numbers using pdfminer.high_level.
    Returns full text and a list of (page_num, page_text).
    """
    try:
        from pdfminer.high_level import extract_pages
        from pdfminer.layout import LTTextContainer
        pages_content = []
        full_text_list = []
        for page_idx, page_layout in enumerate(extract_pages(file_path)):
            page_str = ""
            for element in page_layout:
                if isinstance(element, LTTextContainer):
                    page_str += element.get_text() + "\n"
            cleaned = clean_text(page_str)
            if cleaned:
                pages_content.append((page_idx + 1, cleaned))
                full_text_list.append(cleaned)
        return "\n\n".join(full_text_list), pages_content
    except Exception as e:
        logger.warning(f"PDF extraction failed with pdfminer: {e}")
        # Fallback to plain binary read with text decode
        try:
            with open(file_path, "rb") as f:
                raw = f.read().decode("utf-8", errors="ignore")
                return clean_text(raw), [(1, clean_text(raw))]
        except Exception:
            return "", []

def extract_text_from_docx(file_path: str) -> str:
    """Extracts text from DOCX files without third-party dependencies using built-in zipfile."""
    try:
        import zipfile
        import xml.etree.ElementTree as ET
        with zipfile.ZipFile(file_path) as docx:
            xml_content = docx.read('word/document.xml')
            tree = ET.fromstring(xml_content)
            paragraphs = []
            for p in tree.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p'):
                texts = [node.text for node in p.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t') if node.text]
                if texts:
                    paragraphs.append("".join(texts))
            return clean_text("\n\n".join(paragraphs))
    except Exception as e:
        logger.warning(f"DOCX extraction failed: {e}")
        return ""

class RegulatoryIngestionPipeline:
    def __init__(self, storage_dir: str, registry_file: Optional[str] = None):
        self.storage_dir = storage_dir
        self.registry_file = registry_file or os.path.join(storage_dir, "registry.json")
        self.registry: Dict[str, Any] = self._load_registry()

    def _load_registry(self) -> Dict[str, Any]:
        if os.path.exists(self.registry_file):
            try:
                with open(self.registry_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading ingestion registry: {e}")
        return {"documents": {}, "last_updated": None}

    def _save_registry(self):
        try:
            self.registry["last_updated"] = datetime.utcnow().isoformat()
            with open(self.registry_file, "w", encoding="utf-8") as f:
                json.dump(self.registry, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving ingestion registry: {e}")

    def chunk_document(
        self,
        doc_metadata: DocumentMetadata,
        content: str,
        chunk_size: int = 600,
        chunk_overlap: int = 100
    ) -> List[KnowledgeChunk]:
        """
        Splits regulatory document content into chunks while preserving clauses,
        headings, and section boundaries wherever detectable.
        """
        chunks: List[KnowledgeChunk] = []
        cleaned = clean_text(content)
        if not cleaned:
            return chunks

        # Section-based splitting by Markdown headings or Clause patterns
        section_pattern = re.compile(
            r'(?m)^(#{1,3}\s+(?:Clause|Section|Schedule)?\s*[\d\w\.\s\-—:]+|^Clause\s+\d+[\d\.\s\-—:]*)'
        )
        splits = section_pattern.split(cleaned)

        if len(splits) > 1:
            current_heading = "General"
            for part in splits:
                part = part.strip()
                if not part:
                    continue
                if section_pattern.match(part):
                    current_heading = part.replace("#", "").strip()
                    continue

                # Now split text within this section if it exceeds chunk_size
                text_len = len(part)
                if text_len <= chunk_size:
                    chunk_id = KnowledgeChunk.generate_chunk_id(
                        doc_metadata.document_id, current_heading, len(chunks), part
                    )
                    chunks.append(KnowledgeChunk(
                        chunk_id=chunk_id,
                        document_id=doc_metadata.document_id,
                        standard_code=doc_metadata.standard_code,
                        standard_title=doc_metadata.standard_title,
                        clause=current_heading,
                        page=doc_metadata.page_number if hasattr(doc_metadata, 'page_number') else None,
                        content=part,
                        category=doc_metadata.category,
                        authority=doc_metadata.authority,
                        verification_status=doc_metadata.verification_status,
                        source_url=doc_metadata.source_url,
                        publication_date=doc_metadata.publication_date
                    ))
                else:
                    start = 0
                    while start < text_len:
                        end = min(start + chunk_size, text_len)
                        # Try to break on sentence end
                        if end < text_len:
                            next_period = part.rfind(". ", start, end)
                            if next_period > start + (chunk_size // 2):
                                end = next_period + 1
                        sub_text = part[start:end].strip()
                        if sub_text:
                            chunk_id = KnowledgeChunk.generate_chunk_id(
                                doc_metadata.document_id, current_heading, len(chunks), sub_text
                            )
                            chunks.append(KnowledgeChunk(
                                chunk_id=chunk_id,
                                document_id=doc_metadata.document_id,
                                standard_code=doc_metadata.standard_code,
                                standard_title=doc_metadata.standard_title,
                                clause=current_heading,
                                page=None,
                                content=sub_text,
                                category=doc_metadata.category,
                                authority=doc_metadata.authority,
                                verification_status=doc_metadata.verification_status,
                                source_url=doc_metadata.source_url,
                                publication_date=doc_metadata.publication_date
                            ))
                        start += max(chunk_size - chunk_overlap, 100)
        else:
            # Fallback window chunking
            start = 0
            text_len = len(cleaned)
            while start < text_len:
                end = min(start + chunk_size, text_len)
                if end < text_len:
                    next_period = cleaned.rfind(". ", start, end)
                    if next_period > start + (chunk_size // 2):
                        end = next_period + 1
                sub_text = cleaned[start:end].strip()
                if sub_text:
                    chunk_id = KnowledgeChunk.generate_chunk_id(
                        doc_metadata.document_id, "General", len(chunks), sub_text
                    )
                    chunks.append(KnowledgeChunk(
                        chunk_id=chunk_id,
                        document_id=doc_metadata.document_id,
                        standard_code=doc_metadata.standard_code,
                        standard_title=doc_metadata.standard_title,
                        clause="General Requirements",
                        page=None,
                        content=sub_text,
                        category=doc_metadata.category,
                        authority=doc_metadata.authority,
                        verification_status=doc_metadata.verification_status,
                        source_url=doc_metadata.source_url,
                        publication_date=doc_metadata.publication_date
                    ))
                start += max(chunk_size - chunk_overlap, 100)

        return chunks

    def ingest_file(
        self,
        filepath: str,
        force_reindex: bool = False
    ) -> Tuple[Optional[DocumentMetadata], List[KnowledgeChunk], Dict[str, Any]]:
        """
        Ingests a single file into the trusted regulatory corpus.
        Returns (metadata, chunks, status_dict).
        """
        if not os.path.exists(filepath):
            return None, [], {"status": "error", "message": f"File not found: {filepath}"}

        file_hash = compute_file_hash(filepath)
        filename = os.path.basename(filepath)
        ext = os.path.splitext(filename)[1].lower()

        # Check deduplication
        existing = self.registry["documents"].get(filename)
        if existing and existing.get("content_hash") == file_hash and not force_reindex:
            return None, [], {
                "status": "skipped",
                "message": f"File '{filename}' already ingested with identical hash ({file_hash[:8]})."
            }

        # Parse file based on extension
        raw_text = ""
        meta_dict = {}

        if ext in [".md", ".markdown"]:
            with open(filepath, "r", encoding="utf-8") as f:
                raw_text = f.read()
            meta_dict, raw_text = parse_markdown_with_frontmatter(raw_text)
        elif ext in [".txt"]:
            with open(filepath, "r", encoding="utf-8") as f:
                raw_text = f.read()
        elif ext in [".pdf"]:
            raw_text, _ = extract_text_from_pdf(filepath)
        elif ext in [".docx"]:
            raw_text = extract_text_from_docx(filepath)
        elif ext in [".json"]:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    meta_dict = data
                    raw_text = data.get("content", json.dumps(data))
                elif isinstance(data, list):
                    raw_text = json.dumps(data)
        else:
            return None, [], {"status": "error", "message": f"Unsupported file format: {ext}"}

        cleaned = clean_text(raw_text)
        if len(cleaned) < 50:
            return None, [], {
                "status": "error",
                "message": f"File '{filename}' has insufficient or no usable text ({len(cleaned)} chars)."
            }

        doc_id = meta_dict.get("document_id") or f"DOC-{os.path.splitext(filename)[0].upper()}"
        std_code = meta_dict.get("standard_code") or os.path.splitext(filename)[0].replace("_", " ")
        std_title = meta_dict.get("standard_title") or std_code
        authority = meta_dict.get("authority") or "Bureau of Indian Standards"
        scheme = meta_dict.get("scheme") or "BIS Conformity Assessment"
        category = meta_dict.get("category") or "General Regulatory Standard"
        pub_date = meta_dict.get("publication_date")
        source_url = meta_dict.get("source_url") or "https://www.services.bis.gov.in"
        verif_status = meta_dict.get("verification_status") or "verified_official_record"

        metadata = DocumentMetadata(
            document_id=doc_id,
            standard_code=std_code,
            standard_title=std_title,
            authority=authority,
            scheme=scheme,
            category=category,
            publication_date=pub_date,
            source_url=source_url,
            verification_status=verif_status,
            file_path=filepath,
            content_hash=file_hash,
            ingested_at=datetime.utcnow().isoformat()
        )

        chunks = self.chunk_document(metadata, cleaned)

        # Update registry
        self.registry["documents"][filename] = {
            "document_id": doc_id,
            "standard_code": std_code,
            "content_hash": file_hash,
            "chunk_count": len(chunks),
            "ingested_at": metadata.ingested_at,
            "verification_status": verif_status
        }
        self._save_registry()

        return metadata, chunks, {
            "status": "success",
            "document_id": doc_id,
            "chunk_count": len(chunks),
            "message": f"Successfully ingested {filename} with {len(chunks)} chunks."
        }

    def ingest_directory(
        self,
        directory: str,
        force_reindex: bool = False
    ) -> Tuple[List[DocumentMetadata], List[KnowledgeChunk], Dict[str, Any]]:
        """Ingests all valid regulatory documents in a folder."""
        all_metadata = []
        all_chunks = []
        report = {"total": 0, "ingested": 0, "skipped": 0, "failed": 0, "details": []}

        if not os.path.exists(directory):
            return [], [], {"error": f"Directory not found: {directory}"}

        for fname in sorted(os.listdir(directory)):
            ext = os.path.splitext(fname)[1].lower()
            if ext in [".md", ".markdown", ".txt", ".pdf", ".docx", ".json"]:
                fpath = os.path.join(directory, fname)
                report["total"] += 1
                meta, chunks, res = self.ingest_file(fpath, force_reindex=force_reindex)
                report["details"].append(res)
                if res["status"] == "success":
                    report["ingested"] += 1
                    if meta:
                        all_metadata.append(meta)
                    all_chunks.extend(chunks)
                elif res["status"] == "skipped":
                    report["skipped"] += 1
                else:
                    report["failed"] += 1

        return all_metadata, all_chunks, report

    def get_inventory(self) -> Dict[str, Any]:
        """Provides an auditable inventory of all indexed documents."""
        return self.registry
