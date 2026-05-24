import pytest
import pandas as pd
from unittest.mock import patch
from orchestration.tools import damage_cost_estimator

@pytest.fixture
def mock_costs_df():
    data = {
        "damage_type": ["water damage", "fire damage"],
        "property_category": ["detached", "semi-detached"],
        "min_cost": [1000, 5000],
        "max_cost": [5000, 15000],
        "currency": ["USD", "USD"]
    }
    return pd.DataFrame(data)

@patch("orchestration.tools._repair_costs_df")
def test_damage_cost_estimator_valid(mock_df, mock_costs_df):
    mock_df.side_effect = None
    with patch("orchestration.tools._repair_costs_df", new=mock_costs_df):
        # Test valid lookup
        result = damage_cost_estimator.invoke({"damage_type": "water damage", "property_category": "detached"})
        assert isinstance(result, str)
        assert "1000" in result

@patch("orchestration.tools._repair_costs_df")
def test_damage_cost_estimator_invalid_type(mock_df, mock_costs_df):
    with patch("orchestration.tools._repair_costs_df", new=mock_costs_df):
        # Test invalid damage type
        result = damage_cost_estimator.invoke({"damage_type": "alien invasion", "property_category": "detached"})
        assert "No cost estimate found" in result

@patch("orchestration.tools._repair_costs_df")
def test_damage_cost_estimator_invalid_property(mock_df, mock_costs_df):
    with patch("orchestration.tools._repair_costs_df", new=mock_costs_df):
        # Test invalid property
        result = damage_cost_estimator.invoke({"damage_type": "fire damage", "property_category": "spaceship"})
        assert "No cost estimate found" in result
