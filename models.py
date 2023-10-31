from pydantic import BaseModel
from typing import List,Optional

class Voters(BaseModel):
    name : str

class Poll(BaseModel):
    title : str
    options : List[str]
    slug: Optional[str]

class Votes(BaseModel):
    voter_id : int 
    option_indices: List[int]
