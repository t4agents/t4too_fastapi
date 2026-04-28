from sqlalchemy import DateTime, Text, Numeric, func, cast, literal
from sqlalchemy.dialects.postgresql import REGCONFIG
from datetime import datetime

from uuid import UUID, uuid4
from sqlalchemy import Column, ForeignKey, Index, String, Integer, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from app.db.models.too.z_base import Base, BaseMixin
from app.db.schemas.schemas import SCHEMA_TOO_AI
from pgvector.sqlalchemy import Vector

class Embedding384DB(Base, BaseMixin):
    __tablename__ = "payroll_history_384"


    source_id: Mapped[UUID] = mapped_column(Uuid, nullable=False, index=True,)
    chunk_id: Mapped[int] = mapped_column(Integer, default=1,nullable=True)
    chunk: Mapped[str] = mapped_column(Text, nullable=False)
    text_score: Mapped[float | None] = mapped_column(Numeric(10, 6), nullable=True)
    
    emb384: Mapped[list[float]] = mapped_column(Vector(384), nullable=False)

    __table_args__ = (
        Index("ix_emb384_hnsw",emb384,postgresql_using="hnsw",postgresql_ops={"emb384": "vector_cosine_ops"}),
        Index("ix_emb384_chunk_tsv_gin",func.to_tsvector(cast(literal("english"), REGCONFIG), chunk),postgresql_using="gin",),
        {"schema": SCHEMA_TOO_AI}
    )



class Embedding1024DB(Base, BaseMixin):
    __tablename__ = "inv_1024"

    source_id: Mapped[UUID] = mapped_column(Uuid, nullable=False, index=True,)
    chunk_id: Mapped[int] = mapped_column(Integer, default=1,nullable=True)
    chunk: Mapped[str] = mapped_column(Text, nullable=False)
    text_score: Mapped[float | None] = mapped_column(Numeric(10, 6), nullable=True)
    
    emb1024: Mapped[list[float]] = mapped_column(Vector(1024), nullable=False)

    __table_args__ = (
        Index("ix_emb1024_hnsw",emb1024,postgresql_using="hnsw",postgresql_ops={"emb1024": "vector_cosine_ops"}),
        Index("ix_emb1024_chunk_tsv_gin",func.to_tsvector(cast(literal("english"), REGCONFIG), chunk),postgresql_using="gin",),
        {"schema": SCHEMA_TOO_AI}
    )
