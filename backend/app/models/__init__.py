"""Import all database models."""

from app.models.user import (
    User,
    Role,
    UserRole,
)

from app.models.learning import (
    Course,
    LearningModule,
    ModuleProgress,
    LearningRecommendation,
)

from app.models.assessment import (
    Assessment,
    Question,
    QuestionOption,
    AssessmentAttempt,
    QuestionAnswer,
)

from app.models.quantum import (
    QuantumGate,
    Circuit,
    CircuitGate,
    CircuitVersion,
)

from app.models.simulation import (
    SimulationRun,
    SimulationResult,
)

from app.models.ai import (
    AIConversation,
    AIMessage,
)

from app.models.course import (
    CourseEnrollment,
    CourseAssignment,
)

from app.models.challenge import (
    CodingChallenge,
    CodeSubmission,
)

from app.models.gamification import (
    UserGamification,
    Badge,
    UserBadge,
)

from app.models.collaboration import (
    Project,
    ProjectMember,
    Contribution,
    ContributionMember,
    SharedResource,
)


__all__ = [
    "User",
    "Role",
    "UserRole",

    "Course",
    "LearningModule",
    "ModuleProgress",
    "LearningRecommendation",

    "Assessment",
    "Question",
    "QuestionOption",
    "AssessmentAttempt",
    "QuestionAnswer",

    "QuantumGate",
    "Circuit",
    "CircuitGate",
    "CircuitVersion",

    "SimulationRun",
    "SimulationResult",

    "AIConversation",
    "AIMessage",

    "CourseEnrollment",
    "CourseAssignment",

    "CodingChallenge",
    "CodeSubmission",

    "UserGamification",
    "Badge",
    "UserBadge",

    "Project",
    "ProjectMember",
    "Contribution",
    "ContributionMember",
    "SharedResource",
]