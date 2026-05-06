"""
Task 19.4 — Community Portal Backend.

Build community portal with forums, user profiles, and content sharing.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import time
import hashlib


class PostType(Enum):
    """Types of forum posts."""
    QUESTION = "question"
    ANSWER = "answer"
    DISCUSSION = "discussion"
    TUTORIAL = "tutorial"
    SHOWCASE = "showcase"
    ANNOUNCEMENT = "announcement"


class UserRole(Enum):
    """Community user roles."""
    BEGINNER = "beginner"
    CONTRIBUTOR = "contributor"
    EXPERT = "expert"
    MODERATOR = "moderator"
    ADMIN = "admin"


@dataclass
class UserProfile:
    """User profile in the community."""
    user_id: str
    username: str
    email: str
    role: UserRole = UserRole.BEGINNER
    bio: str = ""
    avatar_url: Optional[str] = None
    joined_at: float = field(default_factory=time.time)
    post_count: int = 0
    reputation: int = 0
    skills: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'user_id': self.user_id,
            'username': self.username,
            'role': self.role.value,
            'bio': self.bio,
            'avatar_url': self.avatar_url,
            'joined_at': self.joined_at,
            'post_count': self.post_count,
            'reputation': self.reputation,
            'skills': self.skills
        }
    
    def update_reputation(self, delta: int):
        """Update user reputation."""
        self.reputation = max(0, self.reputation + delta)
    
    def add_skill(self, skill: str):
        """Add a skill to user profile."""
        if skill not in self.skills:
            self.skills.append(skill)


@dataclass
class ForumPost:
    """A forum post."""
    post_id: str
    author_id: str
    type: PostType
    title: str
    content: str
    parent_id: Optional[str] = None  # For answers/replies.
    tags: List[str] = field(default_factory=list)
    upvotes: int = 0
    downvotes: int = 0
    views: int = 0
    is_solved: bool = False
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'post_id': self.post_id,
            'author_id': self.author_id,
            'type': self.type.value,
            'title': self.title,
            'content': self.content[:200] + "..." if len(self.content) > 200 else self.content,
            'parent_id': self.parent_id,
            'tags': self.tags,
            'upvotes': self.upvotes,
            'downvotes': self.downvotes,
            'views': self.views,
            'is_solved': self.is_solved,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    def vote(self, is_upvote: bool):
        """Vote on the post."""
        if is_upvote:
            self.upvotes += 1
        else:
            self.downvotes += 1
    
    def increment_views(self):
        """Increment view count."""
        self.views += 1
    
    def score(self) -> int:
        """Calculate post score."""
        return self.upvotes - self.downvotes


@dataclass
class CommunityResult:
    """Result of a community operation."""
    success: bool
    message: str = ""
    data: Optional[Any] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'success': self.success,
            'message': self.message,
            'metadata': self.metadata
        }


class SearchEngine:
    """Simple search engine for community content."""
    
    def __init__(self):
        self.index: Dict[str, List[str]] = {}  # word -> post_ids
        self.posts: Dict[str, ForumPost] = {}
    
    def index_post(self, post: ForumPost):
        """Index a post for search."""
        self.posts[post.post_id] = post
        
        # Tokenize title and content.
        text = f"{post.title} {post.content}".lower()
        words = self._tokenize(text)
        
        for word in words:
            if word not in self.index:
                self.index[word] = []
            if post.post_id not in self.index[word]:
                self.index[word].append(post.post_id)
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization."""
        import re
        words = re.findall(r'\w+', text.lower())
        return [w for w in words if len(w) > 2]  # Skip very short words.
    
    def search(self, query: str, 
               post_type: Optional[PostType] = None,
               tags: Optional[List[str]] = None,
               author_id: Optional[str] = None) -> List[ForumPost]:
        """Search posts."""
        query_words = self._tokenize(query)
        if not query_words:
            return []
        
        # Find candidate posts.
        candidate_ids = set()
        for word in query_words:
            if word in self.index:
                if not candidate_ids:
                    candidate_ids = set(self.index[word])
                else:
                    candidate_ids &= set(self.index[word])
        
        # Filter and rank results.
        results = []
        for post_id in candidate_ids:
            post = self.posts.get(post_id)
            if post is None:
                continue
            
            # Filter by type.
            if post_type and post.type != post_type:
                continue
            
            # Filter by tags.
            if tags and not any(tag in post.tags for tag in tags):
                continue
            
            # Filter by author.
            if author_id and post.author_id != author_id:
                continue
            
            results.append(post)
        
        # Sort by score (upvotes - downvotes).
        results.sort(key=lambda p: p.score(), reverse=True)
        return results


class CommunityPortal:
    """Main community portal backend."""
    
    def __init__(self):
        self.users: Dict[str, UserProfile] = {}
        self.posts: Dict[str, ForumPost] = {}
        self.search_engine = SearchEngine()
        self.user_counter = 0
        self.post_counter = 0
    
    def register_user(self, username: str, email: str,
                      bio: str = "") -> CommunityResult:
        """Register a new user."""
        # Check if username already exists.
        for user in self.users.values():
            if user.username == username:
                return CommunityResult(
                    success=False,
                    message="Username already exists"
                )
        
        self.user_counter += 1
        user_id = f"user_{self.user_counter}"
        
        profile = UserProfile(
            user_id=user_id,
            username=username,
            email=email,
            bio=bio
        )
        
        self.users[user_id] = profile
        
        return CommunityResult(
            success=True,
            message=f"User {username} registered",
            data=profile.to_dict()
        )
    
    def get_user(self, user_id: str) -> Optional[UserProfile]:
        """Get user by ID."""
        return self.users.get(user_id)
    
    def update_user(self, user_id: str,
                    bio: Optional[str] = None,
                    skills: Optional[List[str]] = None) -> CommunityResult:
        """Update user profile."""
        if user_id not in self.users:
            return CommunityResult(success=False, message="User not found")
        
        user = self.users[user_id]
        
        if bio is not None:
            user.bio = bio
        if skills is not None:
            user.skills = skills
        
        user.metadata['updated_at'] = time.time()
        
        return CommunityResult(
            success=True,
            message="Profile updated",
            data=user.to_dict()
        )
    
    def create_post(self, author_id: str,
                    type: PostType,
                    title: str,
                    content: str,
                    tags: Optional[List[str]] = None,
                    parent_id: Optional[str] = None) -> CommunityResult:
        """Create a new forum post."""
        if author_id not in self.users:
            return CommunityResult(success=False, message="Author not found")
        
        self.post_counter += 1
        post_id = f"post_{self.post_counter}"
        
        post = ForumPost(
            post_id=post_id,
            author_id=author_id,
            type=type,
            title=title,
            content=content,
            parent_id=parent_id,
            tags=tags or []
        )
        
        self.posts[post_id] = post
        self.search_engine.index_post(post)
        
        # Update user post count.
        self.users[author_id].post_count += 1
        
        return CommunityResult(
            success=True,
            message=f"Post '{title}' created",
            data=post.to_dict()
        )
    
    def get_post(self, post_id: str) -> Optional[ForumPost]:
        """Get a post by ID."""
        post = self.posts.get(post_id)
        if post:
            post.increment_views()
        return post
    
    def vote_post(self, post_id: str, user_id: str, 
                  is_upvote: bool) -> CommunityResult:
        """Vote on a post."""
        if post_id not in self.posts:
            return CommunityResult(success=False, message="Post not found")
        
        post = self.posts[post_id]
        post.vote(is_upvote)
        
        # Update author reputation.
        if post.author_id in self.users:
            delta = 10 if is_upvote else -2
            self.users[post.author_id].update_reputation(delta)
        
        return CommunityResult(
            success=True,
            message="Vote recorded",
            data={'score': post.score()}
        )
    
    def mark_solved(self, post_id: str) -> CommunityResult:
        """Mark a question as solved."""
        if post_id not in self.posts:
            return CommunityResult(success=False, message="Post not found")
        
        post = self.posts[post_id]
        if post.type != PostType.QUESTION:
            return CommunityResult(success=False, message="Not a question")
        
        post.is_solved = True
        
        return CommunityResult(
            success=True,
            message="Question marked as solved"
        )
    
    def search_posts(self, query: str,
                    post_type: Optional[PostType] = None,
                    tags: Optional[List[str]] = None,
                    author_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search forum posts."""
        results = self.search_engine.search(query, post_type, tags, author_id)
        return [p.to_dict() for p in results]
    
    def list_posts(self, post_type: Optional[PostType] = None,
                   tags: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """List posts with optional filtering."""
        results = []
        for post in self.posts.values():
            if post_type and post.type != post_type:
                continue
            if tags and not any(tag in post.tags for tag in tags):
                continue
            results.append(post.to_dict())
        
        # Sort by creation time (newest first).
        results.sort(key=lambda p: p['created_at'], reverse=True)
        return results
    
    def get_user_posts(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all posts by a user."""
        results = []
        for post in self.posts.values():
            if post.author_id == user_id:
                results.append(post.to_dict())
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get community statistics."""
        type_counts = {}
        for post in self.posts.values():
            type_name = post.type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1
        
        return {
            'total_users': len(self.users),
            'total_posts': len(self.posts),
            'by_type': type_counts,
            'total_views': sum(p.views for p in self.posts.values()),
            'total_votes': sum(p.upvotes + p.downvotes for p in self.posts.values())
        }
