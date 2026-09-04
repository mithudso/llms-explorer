# api/tests/test_settings.py
import pytest
from explorer_api.settings import MissingSettings, Settings

REQUIRED = ("DATABASE_URL", "SESSION_SECRET", "STRIPE_SECRET_KEY", "STRIPE_WEBHOOK_SECRET")


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    """No test inherits a real operator environment."""
    for var in (*REQUIRED, "ENVIRONMENT", "HUB_MCP_URL", "STORES_ROOT",
                "OAUTH_GITHUB_ID", "OAUTH_GITHUB_SECRET",
                "OAUTH_GOOGLE_ID", "OAUTH_GOOGLE_SECRET"):
        monkeypatch.delenv(var, raising=False)


def _minimal(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@localhost/x")
    monkeypatch.setenv("SESSION_SECRET", "s" * 32)
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_x")
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_x")


def test_missing_settings_are_named_all_at_once(monkeypatch):
    for var in ("DATABASE_URL", "SESSION_SECRET", "STRIPE_SECRET_KEY"):
        monkeypatch.delenv(var, raising=False)
    with pytest.raises(MissingSettings) as e:
        Settings.load()
    msg = str(e.value)
    assert "DATABASE_URL" in msg and "SESSION_SECRET" in msg and "STRIPE_SECRET_KEY" in msg


def test_loads_from_the_environment(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@localhost/x")
    monkeypatch.setenv("SESSION_SECRET", "s" * 32)
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_x")
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_x")
    s = Settings.load()
    assert s.hub_mcp_url == "http://127.0.0.1:8787"     # localhost by default, never public
    assert s.environment in ("dev", "prod")


def test_no_secret_is_ever_repr_ed(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:hunter2@localhost/x")
    monkeypatch.setenv("SESSION_SECRET", "s" * 32)
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_supersecret")
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_x")
    s = Settings.load()
    assert "hunter2" not in repr(s) and "supersecret" not in repr(s)


def test_every_missing_variable_is_named_not_just_the_first(monkeypatch):
    with pytest.raises(MissingSettings) as e:
        Settings.load()
    msg = str(e.value)
    for var in REQUIRED:
        assert var in msg


def test_a_repo_env_file_is_never_read(monkeypatch, tmp_path):
    """Secrets come from the environment only — a .env sitting next to the app is ignored."""
    (tmp_path / ".env").write_text("DATABASE_URL=postgresql+asyncpg://u:p@localhost/x\n")
    monkeypatch.chdir(tmp_path)
    with pytest.raises(MissingSettings) as e:
        Settings.load()
    assert "DATABASE_URL" in str(e.value)


def test_the_hub_mcp_url_must_stay_on_loopback(monkeypatch):
    _minimal(monkeypatch)
    monkeypatch.setenv("HUB_MCP_URL", "http://10.0.0.5:8787")
    with pytest.raises(ValueError, match="loopback"):
        Settings.load()


def test_the_session_secret_must_be_long_enough(monkeypatch):
    _minimal(monkeypatch)
    monkeypatch.setenv("SESSION_SECRET", "tooshort")
    with pytest.raises(ValueError):
        Settings.load()


def test_an_unknown_environment_is_rejected(monkeypatch):
    _minimal(monkeypatch)
    monkeypatch.setenv("ENVIRONMENT", "staging")
    with pytest.raises(ValueError):
        Settings.load()


def test_oauth_credentials_are_optional_until_a_provider_is_used(monkeypatch):
    _minimal(monkeypatch)
    s = Settings.load()
    assert s.oauth_github_id is None and s.oauth_google_id is None


def test_secrets_are_readable_through_get_secret_value(monkeypatch):
    _minimal(monkeypatch)
    s = Settings.load()
    assert s.stripe_secret_key.get_secret_value() == "sk_test_x"
    assert s.database_url.get_secret_value().endswith("/x")


def test_database_url_is_normalized_to_asyncpg(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost/x")
    monkeypatch.setenv("SESSION_SECRET", "s" * 32)
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_x")
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_x")
    s = Settings.load()
    assert s.database_url.get_secret_value().startswith("postgresql+asyncpg://")


def test_asyncpg_ignores_psycopg_specific_ssl_keywords(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://user:pass@host/db?sslmode=require&channel_binding=require",
    )
    monkeypatch.setenv("SESSION_SECRET", "s" * 32)
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_x")
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_x")
    s = Settings.load()
    value = s.database_url.get_secret_value()
    assert value.startswith("postgresql+asyncpg://")
    assert "ssl=require" in value
    assert "sslmode" not in value
    assert "channel_binding" not in value


def test_a_tilde_in_stores_root_is_expanded(monkeypatch):
    _minimal(monkeypatch)
    monkeypatch.setenv("STORES_ROOT", "~/.llms-explorer/stores")
    s = Settings.load()
    assert s.stores_root.is_absolute() and "~" not in str(s.stores_root)


def test_origin_and_host_lists_parse_as_csv_from_the_environment(monkeypatch):
    """`_split_csv` exists to accept CSV, and for three fields it never ran.

    pydantic-settings json-decodes complex fields inside `EnvSettingsSource`,
    before any `mode="before"` validator. So `SITE_ORIGINS=https://a,https://b`
    raised `SettingsError: error parsing value for field "site_origins"`, and a
    JSON array instead reached `_split_csv` as a raw string and failed the
    absolute-origin check — leaving these three unsettable from the environment
    in either format, which is the only way this app is configured. `NoDecode`
    on the annotations is what hands the raw string to the validator.
    """
    _minimal(monkeypatch)
    monkeypatch.setenv("SITE_ORIGINS", "http://localhost:4321,https://llms-explorer.com")
    monkeypatch.setenv("ALLOWED_HOSTS", "localhost,127.0.0.1")
    monkeypatch.setenv("WEBAUTHN_ORIGINS", "https://llms-explorer.com")

    s = Settings.load()

    assert s.site_origins == ("http://localhost:4321", "https://llms-explorer.com")
    assert s.allowed_hosts == ("localhost", "127.0.0.1")
    assert s.webauthn_origins == ("https://llms-explorer.com",)


def test_a_single_origin_still_parses(monkeypatch):
    """The one-element case has no comma, so it exercises the other branch."""
    _minimal(monkeypatch)
    monkeypatch.setenv("SITE_ORIGINS", "http://localhost:4321")
    assert Settings.load().site_origins == ("http://localhost:4321",)
