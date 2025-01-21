"""Models for features and advantages."""
from typing import Dict, List, TYPE_CHECKING
from pydantic import (
    BaseModel,
    Field,
    ConfigDict,
    StrictStr,
    field_validator
)

from backend.src.app.models.pdf import SectionData

if TYPE_CHECKING:
    import pandas as pd


class FeatureAdvantage(BaseModel):
    """Model representing a single feature or advantage."""
    model_config = ConfigDict(frozen=True)

    category: str = Field(
        ...,
        description="Category of the feature/advantage",
        pattern="^(features|advantages)$"
    )
    value: str = Field(
        ...,
        description="The actual feature or advantage description",
        min_length=1
    )
    model: str = Field(
        ...,
        description="The model this feature/advantage belongs to",
        min_length=1
    )


class ModelFeatureAdvantages(BaseModel):
    """Collection of features and advantages for models."""
    model_config = ConfigDict(frozen=True)

    features: List[FeatureAdvantage] = Field(
        default_factory=list,
        description="List of features for each model"
    )
    advantages: List[FeatureAdvantage] = Field(
        default_factory=list,
        description="List of advantages for each model"
    )

    def to_presentation_dict(self) -> Dict[str, Dict[str, str]]:
        """Convert to a format suitable for presentation."""
        return {
            "Features": {fa.model: fa.value for fa in self.features},
            "Advantages": {fa.model: fa.value for fa in self.advantages}
        }

    @classmethod
    def from_specs_df(
        cls,
        df: "pd.DataFrame",
        models: List[str]
    ) -> "ModelFeatureAdvantages":
        """Create from a specifications DataFrame."""
        features = []
        advantages = []

        for model in models:
            model_data = df[df["Model"] == model]
            for _, row in model_data.iterrows():
                fa = FeatureAdvantage(
                    category=row["Category"].lower(),
                    value=row["Value"].replace("\n", " ").strip(),
                    model=model
                )
                if fa.category == "features":
                    features.append(fa)
                elif fa.category == "advantages":
                    advantages.append(fa)

        return cls(features=features, advantages=advantages)


class ModelSpecs(BaseModel):
    """Specifications for a single model."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    model_name: str = Field(
        min_length=1,
        description="Name of the model"
    )
    features_advantages: Dict[StrictStr, List[StrictStr]] = Field(
        default_factory=dict,
        description="Features and advantages"
    )
    sections: Dict[StrictStr, SectionData] = Field(
        default_factory=dict,
        description="Sections containing specifications"
    )

    @field_validator("features_advantages")
    @classmethod
    def validate_features_advantages(
        cls, v: Dict[str, List[str]]
    ) -> Dict[str, List[str]]:
        """Validate features and advantages structure."""
        valid_keys = {"features", "advantages"}
        invalid_keys = set(v.keys()) - valid_keys
        if invalid_keys:
            raise ValueError(
                f"Invalid keys in features_advantages: {invalid_keys}. "
                f"Must be one of: {valid_keys}"
            )
        return v
