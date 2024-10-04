from pydantic import BaseModel


class OurBaseModel(BaseModel):
    class Config:
        orm_mode = True


class UserCreate(OurBaseModel):
    username: str
    email: str
    password: str


class UserResponse(OurBaseModel):
    id: int
    username: str
    email: str
    is_active: bool
