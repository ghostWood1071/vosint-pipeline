from models.dtos import BaseDto


class PipelineForListDto(BaseDto):
    def __init__(self, record: dict):
        super().__init__(record)
        self.name = record["name"]
        self.enabled = record["enabled"]
        self.actived = record["actived"]

    def to_dict(self) -> dict:
        return {
            **super().to_dict(),
            "name": self.name,
            "enabled": self.enabled,
            "actived": self.actived,
        }
