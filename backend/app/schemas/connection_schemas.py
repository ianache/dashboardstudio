from typing import Literal, Union, Annotated, Optional, Any
from pydantic import BaseModel, Field

class SmtpConfig(BaseModel):
    type: Literal['smtp']
    host: str
    port: int
    use_ssl: bool = True
    email: str
    password: str

class DbConfig(BaseModel):
    type: Literal['database']
    host: str
    port: int
    username: str
    password: str
    database: str
    schema: Optional[str] = "public"
    options: dict = {}

class FtpConfig(BaseModel):
    type: Literal['ftp']
    host: str
    port: int
    username: str
    password: str
    protocol: Literal['ftp', 'sftp'] = 'ftp'
    schema: Optional[str] = None
    options: dict = {}

class HttpConfig(BaseModel):
    type: Literal['http']
    url: str
    username: Optional[str] = None
    password: Optional[str] = None
    options: dict = {}

class JwtConfig(BaseModel):
    type: Literal['jwt']
    token_url: str
    username: Optional[str] = None
    password: Optional[str] = None
    client_id: str
    client_secret: str
    grant_type: str = "password"
    options: dict = {}

ConnectionConfig = Annotated[
    Union[SmtpConfig, DbConfig, FtpConfig, HttpConfig, JwtConfig], 
    Field(discriminator='type')
]
