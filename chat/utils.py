import enum


class ChatRoomType(enum.Enum):
    ANNOUNCEMENT = "ANNOUNCEMENT"
    APPLICATION = "APPLICATION"

    @classmethod
    def choices(cls):
        return [(choice.name, choice.value) for choice in cls]
