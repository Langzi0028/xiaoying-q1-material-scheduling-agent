from ..models import Material
from ..storage.repositories import Repository


M01_REQUESTED_TIME = "2026-10-28T18:00:00+08:00"
M01_ALTERNATIVE_TIME = "2026-10-28T19:00:00+08:00"


def seed_demo_data(repository: Repository) -> None:
    repository.add_material(
        Material(
            material_id="M01",
            title="新品预告短片",
            material_type="video",
            copyright_status="cleared",
            schedule_scope="main",
        )
    )
    repository.add_material(
        Material(
            material_id="M02",
            title="品牌花絮",
            material_type="video",
            copyright_status="cleared",
            schedule_scope="main",
        )
    )
    repository.add_material(
        Material(
            material_id="M03",
            title="版权待补充素材",
            material_type="image",
            copyright_status=None,
            schedule_scope="main",
        )
    )
    repository.add_material(
        Material(
            material_id="M04",
            title="敏感内容素材",
            material_type="video",
            copyright_status="cleared",
            content_risk="sensitive_content",
            schedule_scope="main",
        )
    )
    repository.add_occupied_slot("main", M01_REQUESTED_TIME, "18:00 已被既有排期占用")
