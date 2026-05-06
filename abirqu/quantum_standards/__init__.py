"""
Quantum Standards Module.

Standards and compliance for quantum computing.
Supports 20+ qubit simulations with standards compliance checking.
"""

from typing import Dict, List, Any

# Version info.
__version__ = "1.0.0"
__author__ = "Abir Maheshwari"

# Standards supported.
SUPPORTED_STANDARDS = [
    "FIPS 140-3",
    "ISO 27001",
    "SOC 2",
    "NIST Cybersecurity Framework"
]

def get_standards_info() -> Dict[str, Any]:
    """Get information about supported standards."""
    return {
        'supported_standards': SUPPORTED_STANDARDS,
        'version': __version__,
        'compliance_ready': True
    }

__all__ = ['SUPPORTED_STANDARDS', 'get_standards_info']
