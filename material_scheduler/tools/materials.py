from ..models import Material
from ..storage.repositories import Repository


class MaterialTool:
    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    def get_material(self, material_id: str) -> Material | None:
        return self.repository.get_material(material_id)
