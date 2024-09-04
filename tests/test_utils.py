from pydantic import BaseModel

from nfl_commish.utils import get_valid_team_names, read_config


def test_read_config(tmp_path):
    class TestConfig(BaseModel):
        test_key: str

    example_yaml = "test_key: test_value"
    config_path = tmp_path / "test_config.yaml"
    config_path.write_text(example_yaml)

    config = read_config(config_path=config_path, config_class=TestConfig)
    assert config.test_key == "test_value"


def test_get_valid_team_names():
    team_names = get_valid_team_names()
    assert len(team_names) == 32
    assert "new-orleans-saints" in team_names
    assert "New Orleans Saints" not in team_names
