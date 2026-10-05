"""Database table models.

Import every table model here so ``SQLModel.metadata.create_all`` sees them.
"""

from app.models.user import User
from app.models.submission import Submission
from app.models.review import Review
from app.models.presentation import Presentation

__all__ = ["User", "Submission", "Review", "Presentation"]
