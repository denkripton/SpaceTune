from pydantic import BaseModel, Field

class UserUpdateSchema(BaseModel):
    username: str = Field(max_length=20)
    password: str = Field(min_length=8, max_length=64)