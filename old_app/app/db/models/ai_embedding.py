from sqlalchemy import Text, Numeric, func, cast, literal
from sqlalchemy.dialects.postgresql import REGCONFIG

from uuid import UUID, uuid4
from sqlalchemy import Column, ForeignKey, Index, String, Integer, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from app.db.models.m_base import Base, BaseMixin
from pgvector.sqlalchemy import Vector

class Embedding384(Base):
    __tablename__ = "payroll_history_384"
    id: Mapped[UUID] = mapped_column(Uuid,primary_key=True,default=uuid4, index=True)

    source_id: Mapped[UUID] = mapped_column(Uuid, nullable=False, index=True,)
    chunk: Mapped[str] = mapped_column(Text, nullable=False)
    text_score: Mapped[float | None] = mapped_column(Numeric(10, 6), nullable=True)
    
    emb384: Mapped[list[float]] = mapped_column(Vector(384), nullable=False)

    __table_args__ = (
        Index(
            "ix_emb384_hnsw",
            emb384,
            postgresql_using="hnsw",
            postgresql_ops={"emb384": "vector_cosine_ops"}
        ),
        Index(
            "ix_emb384_chunk_tsv_gin",
            func.to_tsvector(cast(literal("english"), REGCONFIG), chunk),
            postgresql_using="gin",
        ),
    )
