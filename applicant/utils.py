import enum


class LoanAmountChoices(enum.Enum):
    OPTION_1 = "under $10,000"
    OPTION_2 = "$10,000 - $25,000"
    OPTION_3 = "$25,001 - $75,000"
    OPTION_4 = "$75,001 - $250,000"
    OPTION_5 = "$250,001 - $500,000"
    OPTION_6 = "$500,001 - $750,000"
    OPTION_7 = "$750,001 - $1,000,000"
    OPTION_8 = "over $1,000,000"

    @classmethod
    def choices(cls):
        return [(choice.name, choice.value) for choice in cls]


class LoanTypeChoices(enum.Enum):
    TYPE_1 = "Business Loans"
    TYPE_2 = "Debt Consolidation Loans"
    TYPE_3 = "Business Lines of Credit"
    TYPE_4 = "Equipment Financing"
    TYPE_5 = "Working Capital Loans"
    TYPE_6 = "Merchant Cash Advance"

    @classmethod
    def choices(cls):
        return [(choice.name, choice.value) for choice in cls]


class LoanTermChoices(enum.Enum):
    TERM_1 = "3 months"
    TERM_2 = "6 months"
    TERM_3 = "12 months"
    TERM_4 = "18 months"
    TERM_5 = "24 months"
    TERM_6 = "More than 24 months"

    @classmethod
    def choices(cls):
        return [(choice.name, choice.value) for choice in cls]


class BusinessLocationChoices(enum.Enum):
    USA = "USA"
    CANADA = "CANADA"

    @classmethod
    def choices(cls):
        return [(choice.name, choice.value) for choice in cls]


class YearsInBusinessChoices(enum.Enum):
    TERM_1 = "Less than 6 months"
    TERM_2 = "6 months to 12 months"
    TERM_3 = "1 year"
    TERM_4 = "2-3 years"
    TERM_5 = "3-5 years"
    TERM_6 = "More than 5 years"

    @classmethod
    def choices(cls):
        return [(choice.name, choice.value) for choice in cls]


class UserRoleChoices(enum.Enum):
    ADMIN = "ADMIN"
    APPLICANT = "APPLICANT"
    AGENT = "AGENT"
    PARTNER = "PARTNER"

    @classmethod
    def choices(cls):
        return [(choice.name, choice.value) for choice in cls]

    @classmethod
    def invitable_roles(cls):
        return [(choice.name, choice.value) for choice in [cls.ADMIN, cls.AGENT, cls.PARTNER]]
