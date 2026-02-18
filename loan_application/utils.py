import enum


class LoanApplicationStatus(enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]


class LoanApplicationStep(enum.Enum):
    BUSINESS_INFORMATION = "business_information"
    FUNDING_INFORMATION = "funding_information"
    BUSINESS_OWNERSHIP_INFORMATION = "business_ownership_information"
    TERMS_AND_CONDITIONS = "terms_and_conditions"
    DOCUMENT_UPLOAD = "document_upload"
    REVIEW_SUBMISSION = "review_submission"

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]


class DocumentType(enum.Enum):
    BUSINESS_REGISTRATION = "business_registration"
    TAX_RETURN = "tax_return"
    BANK_STATEMENT = "bank_statement"
    PAY_STUBS = "pay_stubs"
    FINANCIAL_STATEMENTS = "financial_statements"
    OTHER = "other"
    PROOF_OF_OWNERSHIP = "proof_of_ownership"

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]
