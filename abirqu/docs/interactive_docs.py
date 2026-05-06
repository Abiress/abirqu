"""
Task 19.1 — Interactive Documentation System.

Build interactive documentation with search, versioning, and live examples.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import time
import json
import re


class DocFormat(Enum):
    """Documentation formats."""
    MARKDOWN = "markdown"
    RESTRUCTURED_TEXT = "rst"
    JUPYTER = "jupyter"
    HTML = "html"


class DocSection(Enum):
    """Documentation sections."""
    GETTING_STARTED = "getting_started"
    CORE_CONCEPTS = "core_concepts"
    API_REFERENCE = "api_reference"
    TUTORIALS = "tutorials"
    EXAMPLES = "examples"
    ADVANCED = "advanced"


@dataclass
class DocPage:
    """A documentation page."""
    page_id: str
    title: str
    content: str
    format: DocFormat
    section: DocSection
    version: str = "1.0"
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    tags: List[str] = field(default_factory=list)
    author: str = "Abir Maheshwari"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'page_id': self.page_id,
            'title': self.title,
            'format': self.format.value,
            'section': self.section.value,
            'version': self.version,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'tags': self.tags,
            'author': self.author
        }
    
    def search(self, query: str) -> float:
        """Search within page content. Returns relevance score 0-1."""
        query_lower = query.lower()
        content_lower = self.content.lower()
        
        # Simple relevance: count occurrences.
        count = content_lower.count(query_lower)
        if count == 0:
            return 0.0
        
        # Normalize by content length.
        score = min(1.0, count / max(1, len(content_lower.split()) * 0.1))
        return score


@dataclass
class DocSearchResult:
    """Result of a documentation search."""
    page_id: str
    title: str
    section: DocSection
    relevance: float
    snippet: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'page_id': self.page_id,
            'title': self.title,
            'section': self.section.value,
            'relevance': self.relevance,
            'snippet': self.snippet
        }


class DocVersionManager:
    """Manages documentation versions."""
    
    def __init__(self):
        self.versions: Dict[str, List[DocPage]] = {}  # page_id -> versions
        self.current_versions: Dict[str, str] = {}  # page_id -> current version
    
    def add_version(self, page: DocPage) -> DocPage:
        """Add a new version of a page."""
        if page.page_id not in self.versions:
            self.versions[page.page_id] = []
        
        # Update timestamp.
        page.updated_at = time.time()
        
        self.versions[page.page_id].append(page)
        self.current_versions[page.page_id] = page.version
        
        return page
    
    def get_version(self, page_id: str, version: str) -> Optional[DocPage]:
        """Get specific version of a page."""
        if page_id not in self.versions:
            return None
        
        for page in self.versions[page_id]:
            if page.version == version:
                return page
        return None
    
    def get_latest(self, page_id: str) -> Optional[DocPage]:
        """Get latest version of a page."""
        if page_id not in self.versions or not self.versions[page_id]:
            return None
        return self.versions[page_id][-1]
    
    def list_versions(self, page_id: str) -> List[str]:
        """List all versions of a page."""
        if page_id not in self.versions:
            return []
        return [p.version for p in self.versions[page_id]]


class DocSearchEngine:
    """Search engine for documentation."""
    
    def __init__(self):
        self.index: Dict[str, List[str]] = {}  # word -> page_ids
        self.pages: Dict[str, DocPage] = {}
    
    def index_page(self, page: DocPage):
        """Index a page for search."""
        self.pages[page.page_id] = page
        
        # Tokenize content.
        words = re.findall(r'\w+', page.content.lower())
        
        for word in words:
            if word not in self.index:
                self.index[word] = []
            if page.page_id not in self.index[word]:
                self.index[word].append(page.page_id)
    
    def search(self, query: str, 
               section: Optional[DocSection] = None,
               tags: Optional[List[str]] = None) -> List[DocSearchResult]:
        """Search documentation."""
        query_words = re.findall(r'\w+', query.lower())
        
        if not query_words:
            return []
        
        # Find pages containing any query word.
        candidate_pages = set()
        for word in query_words:
            if word in self.index:
                candidate_pages.update(self.index[word])
        
        # Score and filter results.
        results = []
        for page_id in candidate_pages:
            page = self.pages.get(page_id)
            if page is None:
                continue
            
            # Filter by section.
            if section and page.section != section:
                continue
            
            # Filter by tags.
            if tags and not any(tag in page.tags for tag in tags):
                continue
            
            # Calculate relevance.
            relevance = page.search(query)
            if relevance > 0:
                # Create snippet.
                snippet = self._create_snippet(page.content, query)
                
                results.append(DocSearchResult(
                    page_id=page.page_id,
                    title=page.title,
                    section=page.section,
                    relevance=relevance,
                    snippet=snippet
                ))
        
        # Sort by relevance.
        results.sort(key=lambda r: r.relevance, reverse=True)
        return results
    
    def _create_snippet(self, content: str, query: str, 
                        context_chars: int = 50) -> str:
        """Create a text snippet around the first match."""
        content_lower = content.lower()
        query_lower = query.lower()
        
        idx = content_lower.find(query_lower)
        if idx == -1:
            return content[:100]
        
        start = max(0, idx - context_chars)
        end = min(len(content), idx + len(query) + context_chars)
        
        snippet = content[start:end]
        if start > 0:
            snippet = "..." + snippet
        if end < len(content):
            snippet = snippet + "..."
        
        return snippet


class InteractiveDocs:
    """Main interactive documentation system."""
    
    def __init__(self):
        self.pages: Dict[str, DocPage] = {}
        self.version_manager = DocVersionManager()
        self.search_engine = DocSearchEngine()
        self.page_counter = 0
    
    def create_page(self, title: str, content: str,
                    format: DocFormat,
                    section: DocSection,
                    tags: Optional[List[str]] = None) -> DocPage:
        """Create a new documentation page."""
        self.page_counter += 1
        page_id = f"doc_{self.page_counter}"
        
        page = DocPage(
            page_id=page_id,
            title=title,
            content=content,
            format=format,
            section=section,
            tags=tags or []
        )
        
        self.pages[page_id] = page
        self.version_manager.add_version(page)
        self.search_engine.index_page(page)
        
        return page
    
    def update_page(self, page_id: str, 
                    content: Optional[str] = None,
                    title: Optional[str] = None,
                    tags: Optional[List[str]] = None,
                    new_version: bool = True) -> Optional[DocPage]:
        """Update a documentation page."""
        if page_id not in self.pages:
            return None
        
        old_page = self.pages[page_id]
        
        if new_version:
            # Create new version.
            new_page = DocPage(
                page_id=page_id,
                title=title or old_page.title,
                content=content or old_page.content,
                format=old_page.format,
                section=old_page.section,
                version=self._increment_version(old_page.version),
                tags=tags or old_page.tags
            )
            self.pages[page_id] = new_page
            self.version_manager.add_version(new_page)
            self.search_engine.index_page(new_page)
            return new_page
        else:
            # Update in place.
            if content:
                old_page.content = content
            if title:
                old_page.title = title
            if tags:
                old_page.tags = tags
            old_page.updated_at = time.time()
            self.search_engine.index_page(old_page)
            return old_page
    
    def _increment_version(self, version: str) -> str:
        """Increment version number."""
        parts = version.split('.')
        if len(parts) == 1:
            return f"{int(parts[0]) + 1}"
        try:
            parts[-1] = str(int(parts[-1]) + 1)
        except ValueError:
            return "1.0"
        return '.'.join(parts)
    
    def get_page(self, page_id: str, 
                 version: Optional[str] = None) -> Optional[DocPage]:
        """Get a documentation page."""
        if version:
            return self.version_manager.get_version(page_id, version)
        return self.pages.get(page_id)
    
    def delete_page(self, page_id: str) -> bool:
        """Delete a documentation page."""
        if page_id not in self.pages:
            return False
        
        del self.pages[page_id]
        # Note: versions are kept in version_manager.
        return True
    
    def search(self, query: str, 
               section: Optional[DocSection] = None,
               tags: Optional[List[str]] = None) -> List[DocSearchResult]:
        """Search documentation."""
        return self.search_engine.search(query, section, tags)
    
    def list_pages(self, section: Optional[DocSection] = None) -> List[Dict[str, Any]]:
        """List documentation pages."""
        result = []
        for page in self.pages.values():
            if section and page.section != section:
                continue
            result.append(page.to_dict())
        return result
    
    def get_related_pages(self, page_id: str) -> List[DocSearchResult]:
        """Get pages related to a given page."""
        page = self.pages.get(page_id)
        if page is None:
            return []
        
        # Search using page tags and title words.
        query = f"{page.title} {' '.join(page.tags)}"
        return self.search(query)
    
    def export_page(self, page_id: str, 
                    format: DocFormat = DocFormat.MARKDOWN) -> Optional[str]:
        """Export a page to specified format."""
        page = self.pages.get(page_id)
        if page is None:
            return None
        
        if format == DocFormat.MARKDOWN:
            return f"# {page.title}\n\n{page.content}"
        elif format == DocFormat.HTML:
            # Very simple HTML conversion.
            html = f"<html><head><title>{page.title}</title></head>"
            html += f"<body><h1>{page.title}</h1>"
            html += f"<pre>{page.content}</pre></body></html>"
            return html
        
        return page.content
    
    def get_stats(self) -> Dict[str, Any]:
        """Get documentation statistics."""
        section_counts = {}
        for page in self.pages.values():
            section = page.section.value
            section_counts[section] = section_counts.get(section, 0) + 1
        
        return {
            'total_pages': len(self.pages),
            'by_section': section_counts,
            'total_versions': sum(
                len(v) for v in self.version_manager.versions.values()
            )
        }
