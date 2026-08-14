"""
Database Router — directs queries to correct database.

Rule:
  - Models with app_label='external_source' → external_db (read only)
  - Everything else → default (local SQLite)
"""


class ExternalDbRouter:
    EXTERNAL_APP_LABEL = 'external_source'

    def db_for_read(self, model, **hints):
        if model._meta.app_label == self.EXTERNAL_APP_LABEL:
            return 'external_db'
        return 'default'

    def db_for_write(self, model, **hints):
        # Never write to external DB
        if model._meta.app_label == self.EXTERNAL_APP_LABEL:
            return None
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        # Allow relations within the same database
        db_set = {'default', 'external_db'}
        if obj1._state.db in db_set and obj2._state.db in db_set:
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        # Only migrate local models to default DB
        if app_label == self.EXTERNAL_APP_LABEL:
            return False
        return db == 'default'
