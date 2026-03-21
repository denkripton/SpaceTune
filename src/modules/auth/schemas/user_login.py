from pydantic import BaseModel, EmailStr, Field

class UserLoginSchema(BaseModel):
    email: EmailStr = Field(max_length=50, examples=["user@gmail.com"])
    password: str = Field(min_length=8, max_length=64)
