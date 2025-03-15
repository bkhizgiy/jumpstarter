from jumpstarter.config.client import ClientConfigV1Alpha1
from jumpstarter.config.user import UserConfigV1Alpha1


def set_next_client(name: str):
    user_config = UserConfigV1Alpha1.load() if UserConfigV1Alpha1.exists() else None
    if (
        user_config is not None
        and user_config.config.current_client is not None
        and user_config.config.current_client.alias == name
    ):
        for c in ClientConfigV1Alpha1.list():
            if c.alias != name:
                # Use the next available client config
                user_config.use_client(c.alias)
                return
        # Otherwise, set client to none
        user_config.use_client(None)
