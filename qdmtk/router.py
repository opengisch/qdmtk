class QDMTKRouter:

    registry = {}

    def __init__(self):
        print("INIT QDMTKROUTER")

    def db_for_read(self, model, **hints):
        raise Exception("abc")
        print("db_for_read")
        print(f"model: {model}")
        print(f"hints: {hints}")
        return "demo"

    def db_for_write(self, model, **hints):
        raise Exception("abc")
        print("db_for_write")
        print(f"model: {model}")
        print(f"hints: {hints}")
        return self.db_for_read(model, **hints)

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        raise Exception("abc")
        print("allow_migrate")
        print(f"db: {db}")
        print(f"app_label: {app_label}")
        print(f"model_name: {model_name}")
        print(f"hints: {hints}")
        return False
