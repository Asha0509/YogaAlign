from pydantic import BaseModel, constr, validator
import re

class UserModel(BaseModel):
    name: constr(min_length=2)
    email: str
    password: str
    confirm_password: str

    @validator("email")
    def validate_email_format(cls, v):
        if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', v):
            raise ValueError("Invalid email format.")
        return v

    @validator("password")
    def validate_password_strength(cls, v):
        if (len(v) < 6 or
            not re.search(r"[A-Z]", v) or
            not re.search(r"[a-z]", v) or
            not re.search(r"[0-9]", v) or
            not re.search(r"[!@#$%^&*]", v)):
            raise ValueError("Password must contain uppercase, lowercase, digit, and special character (!@#$%^&*)")
        return v

    @validator("confirm_password")
    def passwords_match(cls, v, values):
        if "password" in values and v != values["password"]:
            raise ValueError("Passwords do not match.")
        return v


class LoginModel(BaseModel):
    email: str
    password: str

    @validator("email")
    def validate_email_format(cls, v):
        if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', v):
            raise ValueError("Invalid email format.")
        return v


class VideoUploadModel(BaseModel):
    filename: str
    url: str
