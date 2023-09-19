import pynecone as pc

class KakaochatbotConfig(pc.Config):
    pass

config = KakaochatbotConfig(
    app_name="kakaoChatbot",
    db_url="sqlite:///pynecone.db",
    env=pc.Env.DEV,
)