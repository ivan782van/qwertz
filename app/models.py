from pydantic import BaseModel


class Deployment(BaseModel):

    instance: str

    file: str
