from dana.studio.api.core.schemas import DocumentRead


class DocumentReadV2(DocumentRead):
    file_path: str | None = None
