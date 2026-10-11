from pydantic import BaseModel, Field
from typing import Optional
from datetime import date

class LegalChunk(BaseModel):
  doc_id: str = Field(description="URL or case number")
  doc_type: str = Field(description="'Law' or 'Ruling'")
  text: str = Field(description="The extracted text block")
  rhetorical_role: Optional[str] = Field(description="Who is speaking in this block")
  valid_from: Optional[date] = Field(description="Start date of validity")
  valid_to: Optional[date] = Field(description="Revocation date, if applicable")