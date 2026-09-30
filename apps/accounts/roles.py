"""Staff and student roles. Each role is a Django Group; permissions are added per module."""


class Role:
    STUDENT = "Student"
    COUNSELLOR = "Counsellor"
    APPLICATION_OFFICER = "Application Officer"
    TEACHER = "Teacher"
    FINANCE = "Finance Staff"
    CONTENT_MANAGER = "Content Manager"
    SUPPORT = "Support Staff"

    ALL = (
        STUDENT,
        COUNSELLOR,
        APPLICATION_OFFICER,
        TEACHER,
        FINANCE,
        CONTENT_MANAGER,
        SUPPORT,
    )
