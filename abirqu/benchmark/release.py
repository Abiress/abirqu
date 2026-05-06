"""
Task 20.5 — Release Engineering.

Manage software releases, versioning, and deployment artifacts.
Support CI/CD integration and release notes generation.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import time
import json


class ReleaseStatus(Enum):
    """Status of a release."""
    DRAFT = "draft"
    TESTING = "testing"
    RC = "release_candidate"
    STABLE = "stable"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class ReleaseType(Enum):
    """Type of release."""
    MAJOR = "major"
    MINOR = "minor"
    PATCH = "patch"
    PRE = "pre-release"


@dataclass
class ReleaseArtifact:
    """An artifact produced by a release."""
    name: str
    type: str  # 'wheel', 'sdist', 'docker', etc.
    path: str
    size_bytes: int
    checksum: str
    created_at: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'type': self.type,
            'path': self.path,
            'size_bytes': self.size_bytes,
            'checksum': self.checksum,
            'created_at': self.created_at
        }


@dataclass
class ReleaseCandidate:
    """A release candidate for testing."""
    rc_id: str
    version: str
    build_number: int
    artifacts: List[ReleaseArtifact] = field(default_factory=list)
    test_results: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"
    created_at: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'rc_id': self.rc_id,
            'version': self.version,
            'build_number': self.build_number,
            'artifact_count': len(self.artifacts),
            'artifacts': [a.to_dict() for a in self.artifacts],
            'test_results': self.test_results,
            'status': self.status,
            'created_at': self.created_at
        }
    
    def add_artifact(self, artifact: ReleaseArtifact):
        """Add an artifact."""
        self.artifacts.append(artifact)
    
    def update_test_results(self, results: Dict[str, Any]):
        """Update test results."""
        self.test_results = results
        # Auto-update status based on results.
        if 'passed' in results and 'total' in results:
            if results['passed'] == results['total']:
                self.status = "all_tests_passed"
            else:
                self.status = "tests_failed"


@dataclass
class Release:
    """A software release."""
    version: str
    type: ReleaseType
    status: ReleaseStatus = ReleaseStatus.DRAFT
    previous_version: Optional[str] = None
    codename: str = ""
    release_notes: str = ""
    artifacts: List[ReleaseArtifact] = field(default_factory=list)
    candidates: List[ReleaseCandidate] = field(default_factory=list)
    published_at: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'version': self.version,
            'type': self.type.value,
            'status': self.status.value,
            'previous_version': self.previous_version,
            'codename': self.codename,
            'release_notes': self.release_notes,
            'artifact_count': len(self.artifacts),
            'artifacts': [a.to_dict() for a in self.artifacts],
            'candidate_count': len(self.candidates),
            'published_at': self.published_at,
            'metadata': self.metadata
        }
    
    def add_artifact(self, artifact: ReleaseArtifact):
        """Add a release artifact."""
        self.artifacts.append(artifact)
    
    def add_candidate(self, candidate: ReleaseCandidate):
        """Add a release candidate."""
        self.candidates.append(candidate)
    
    def publish(self) -> bool:
        """Publish the release."""
        if self.status != ReleaseStatus.DRAFT:
            return False
        self.status = ReleaseStatus.STABLE
        self.published_at = time.time()
        return True
    
    def generate_notes(self) -> str:
        """Generate release notes from commits (simplified)."""
        notes = f"# Release {self.version}\n\n"
        if self.codename:
            notes += f"**Codename:** {self.codename}\n\n"
        notes += "## Changes\n\n"
        notes += "- [Add changes here]\n\n"
        notes += f"## Artifacts\n\n"
        for artifact in self.artifacts:
            notes += f"- {artifact.name} ({artifact.type})\n"
        return notes


class VersionManager:
    """Manage version numbers."""
    
    def __init__(self):
        self.versions: List[str] = []
        self.current_version: Optional[str] = None
    
    def parse_version(self, version: str) -> Tuple[int, int, int]:
        """Parse a version string."""
        parts = version.split('.')
        if len(parts) != 3:
            raise ValueError(f"Invalid version format: {version}")
        return (int(parts[0]), int(parts[1]), int(parts[2]))
    
    def increment_version(self, current: str, 
                         type: ReleaseType) -> str:
        """Increment version based on release type."""
        major, minor, patch = self.parse_version(current)
        
        if type == ReleaseType.MAJOR:
            return f"{major + 1}.0.0"
        elif type == ReleaseType.MINOR:
            return f"{major}.{minor + 1}.0"
        elif type == ReleaseType.PATCH:
            return f"{major}.{minor}.{patch + 1}"
        else:  # PRE
            return f"{major}.{minor}.{patch + 1}-pre"
    
    def is_newer(self, v1: str, v2: str) -> bool:
        """Check if v1 is newer than v2."""
        try:
            mj1, mn1, p1 = self.parse_version(v1)
            mj2, mn2, p2 = self.parse_version(v2)
            
            if mj1 != mj2:
                return mj1 > mj2
            if mn1 != mn2:
                return mn1 > mn2
            return p1 > p2
        except ValueError:
            return False
    
    def add_version(self, version: str):
        """Register a version."""
        if version not in self.versions:
            self.versions.append(version)
            if self.current_version is None or self.is_newer(version, self.current_version):
                self.current_version = version


class ReleaseManager:
    """Main release engineering system."""
    
    def __init__(self):
        self.releases: Dict[str, Release] = {}
        self.version_manager = VersionManager()
        self.candidate_counter = 0
        self.artifact_counter = 0
    
    def create_release(self, version: str,
                      type: ReleaseType,
                      previous_version: Optional[str] = None,
                      codename: str = "") -> Release:
        """Create a new release."""
        release = Release(
            version=version,
            type=type,
            previous_version=previous_version,
            codename=codename
        )
        
        self.releases[version] = release
        self.version_manager.add_version(version)
        
        return release
    
    def get_release(self, version: str) -> Optional[Release]:
        """Get a release by version string."""
        return self.releases.get(version)
    
    def update_status(self, version: str, 
                      status: ReleaseStatus) -> bool:
        """Update release status."""
        if version not in self.releases:
            return False
        
        self.releases[version].status = status
        return True
    
    def create_candidate(self, version: str,
                          build_number: int = None) -> Optional[ReleaseCandidate]:
        """Create a release candidate."""
        if version not in self.releases:
            return None
        
        release = self.releases[version]
        self.candidate_counter += 1
        
        rc_id = f"rc_{self.candidate_counter}"
        candidate = ReleaseCandidate(
            rc_id=rc_id,
            version=version,
            build_number=build_number or len(release.candidates) + 1
        )
        
        release.add_candidate(candidate)
        return candidate
    
    def add_artifact(self, version: str,
                     name: str,
                     type: str,
                     path: str,
                     size_bytes: int,
                     checksum: str = "") -> bool:
        """Add an artifact to a release."""
        release = self.get_release(version)
        if release is None:
            return False
        
        self.artifact_counter += 1
        artifact = ReleaseArtifact(
            name=name,
            type=type,
            path=path,
            size_bytes=size_bytes,
            checksum=checksum or f"checksum_{self.artifact_counter}"
        )
        
        release.add_artifact(artifact)
        return True
    
    def publish_release(self, version: str) -> bool:
        """Publish a release."""
        release = self.get_release(version)
        if release is None:
            return False
        
        return release.publish()
    
    def generate_release_notes(self, version: str) -> str:
        """Generate release notes."""
        release = self.get_release(version)
        if release is None:
            return ""
        
        if release.release_notes:
            return release.release_notes
        
        return release.generate_notes()
    
    def list_releases(self, 
                      status: Optional[ReleaseStatus] = None,
                      type: Optional[ReleaseType] = None) -> List[Dict[str, Any]]:
        """List releases with optional filtering."""
        result = []
        
        for release in self.releases.values():
            if status and release.status != status:
                continue
            if type and release.type != type:
                continue
            result.append(release.to_dict())
        
        # Sort by version (newest first).
        result.sort(key=lambda r: r['version'], reverse=True)
        return result
    
    def get_latest(self) -> Optional[Release]:
        """Get the latest release."""
        if not self.version_manager.current_version:
            return None
        return self.releases.get(self.version_manager.current_version)
    
    def delete_release(self, version: str) -> bool:
        """Delete a release."""
        if version not in self.releases:
            return False
        
        del self.releases[version]
        return True
    
    def export_release(self, version: str, 
                     format: str = "json") -> Optional[str]:
        """Export a release in specified format."""
        release = self.get_release(version)
        if release is None:
            return None
        
        if format == "json":
            return json.dumps(release.to_dict(), indent=2)
        
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get release statistics."""
        by_status = {}
        by_type = {}
        total_artifacts = 0
        
        for release in self.releases.values():
            # By status.
            status = release.status.value
            by_status[status] = by_status.get(status, 0) + 1
            
            # By type.
            rtype = release.type.value
            by_type[rtype] = by_type.get(rtype, 0) + 1
            
            # Total artifacts.
            total_artifacts += len(release.artifacts)
        
        return {
            'total_releases': len(self.releases),
            'by_status': by_status,
            'by_type': by_type,
            'total_artifacts': total_artifacts,
            'current_version': self.version_manager.current_version,
            'total_candidates': sum(len(r.candidates) for r in self.releases.values())
        }
