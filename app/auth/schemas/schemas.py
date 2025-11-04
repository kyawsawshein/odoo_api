# """Database schemas for authentication"""

# from app.core.schemas import BaseSchema
# from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text


# class User(BaseSchema):
#     """User database model"""

#     __tablename__ = "users"

#     id = Column(Integer, primary_key=True, index=True)
#     username = Column(String(50), unique=True, index=True, nullable=False)
#     email = Column(String(255), unique=True, index=True, nullable=False)
#     full_name = Column(String(255), nullable=True)
#     hashed_password = Column(String(255), nullable=False)
#     is_active = Column(Boolean, default=True)

#     # Odoo credentials (encrypted in production)
#     odoo_url = Column(String(255), nullable=True)
#     odoo_database = Column(String(255), nullable=True)
#     odoo_username = Column(String(255), nullable=True)
#     odoo_password = Column(String(255), nullable=True)

#     def __repr__(self):
#         return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"


# class OdooSession(BaseSchema):
#     """Odoo session storage for user authentication"""

#     __tablename__ = "odoo_sessions"

#     id = Column(Integer, primary_key=True, index=True)
#     user_id = Column(Integer, nullable=False)
#     odoo_uid = Column(Integer, nullable=False)
#     odoo_session_id = Column(String(255), nullable=False)
#     odoo_database = Column(String(255), nullable=False)
#     is_active = Column(Boolean, default=True)

#     def __repr__(self):
#         return f"<OdooSession(user_id={self.user_id}, odoo_uid={self.odoo_uid})>"


# class APIToken(BaseSchema):
#     """API token for external integrations"""

#     __tablename__ = "api_tokens"

#     id = Column(Integer, primary_key=True, index=True)
#     name = Column(String(100), nullable=False)
#     token = Column(String(255), unique=True, nullable=False)
#     user_id = Column(Integer, nullable=False)
#     scopes = Column(Text, nullable=False)  # JSON string of allowed scopes
#     is_active = Column(Boolean, default=True)

#     def __repr__(self):
#         return f"<APIToken(name='{self.name}', user_id={self.user_id})>"

