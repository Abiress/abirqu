"""
Phase 19: Documentation & Ecosystem.

Task 19.1 — Interactive Documentation System
Task 19.2 — API Reference Generator
Task 19.3 — Tutorial & Example Generator
Task 19.4 — Community Portal Backend
Task 19.5 — Ecosystem Integration Layer
"""

from .interactive_docs import (
    InteractiveDocs, DocPage, DocSection,
    DocSearchResult, DocFormat
)
from .api_reference import (
    APIReferenceGenerator, APIEndpoint, APISchema,
    APIReferenceResult, APIFormat
)
from .tutorial_generator import (
    TutorialGenerator, Tutorial, TutorialStep,
    TutorialResult, SkillLevel, TutorialType
)
from .community_portal import (
    CommunityPortal, ForumPost, UserProfile,
    CommunityResult, PostType, UserRole
)
from .ecosystem_integration import (
    EcosystemIntegration, Plugin, Extension,
    IntegrationResult, IntegrationType, PluginStatus
)

__all__ = [
    # Task 19.1
    'InteractiveDocs', 'DocPage', 'DocSection',
    'DocSearchResult', 'DocFormat',
    # Task 19.2
    'APIReferenceGenerator', 'APIEndpoint', 'APISchema',
    'APIReferenceResult', 'APIFormat',
    # Task 19.3
    'TutorialGenerator', 'Tutorial', 'TutorialStep',
    'TutorialResult', 'SkillLevel', 'TutorialType',
    # Task 19.4
    'CommunityPortal', 'ForumPost', 'UserProfile',
    'CommunityResult', 'PostType', 'UserRole',
    # Task 19.5
    'EcosystemIntegration', 'Plugin', 'Extension',
    'IntegrationResult', 'IntegrationType', 'PluginStatus',
]
