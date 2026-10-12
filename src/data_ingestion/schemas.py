from datetime import date

from pydantic import BaseModel, Field


class LegalChunk(BaseModel):
    doc_id: str = Field(description="URL or case number")
    doc_type: str = Field(description="'Law' or 'Ruling'")
    text: str = Field(description="The extracted text block")
    rhetorical_role: str | None = Field(description="Who is speaking in this block")
    valid_from: date | None = Field(description="Start date of validity")
    valid_to: date | None = Field(description="Revocation date, if applicable")
