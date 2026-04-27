from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.db.models.ai.ai_embedding import Embedding1024DB
from app.db.models.inv import InvoiceDB
from app.util.div2content import div_to_content


class InvChunkService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def rebuild_chunks(self) -> dict:
        # 1️⃣ Clean chunks
        await self.db.execute(delete(Embedding1024DB))
        await self.db.commit()

        # 2️⃣ Load invoices
        result = await self.db.execute(select(InvoiceDB))
        invoices = result.scalars().all()

        # 3️⃣ Build chunks
        chunks: list[Embedding1024DB] = []
        for invoice in invoices:
            chunk = Embedding1024DB(
                invoice_id=invoice.id,
                chunk_index=0,
                content=div_to_content(invoice),
                embedding=None,
            )
            chunks.append(chunk)

        self.db.add_all(chunks)
        await self.db.commit()

        return {
            "invoices_processed": len(invoices),
            "chunks_created": len(chunks),
        }
