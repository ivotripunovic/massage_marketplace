from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

PREF_GROUPS_CACHE_KEY = "pref_groups_tree"


def _invalidate_pref_groups_cache(**kwargs):
    cache.delete(PREF_GROUPS_CACHE_KEY)


def register_preference_signals():
    """
    Connect invalidation signals for all models that make up the
    PreferenceGroup tree.  Called from ProvidersConfig.ready().
    """
    from providers.models import PreferenceGroup, PreferenceSubgroup, PreferenceSubgroupOption

    for model in (PreferenceGroup, PreferenceSubgroup, PreferenceSubgroupOption):
        post_save.connect(_invalidate_pref_groups_cache, sender=model, weak=False)
        post_delete.connect(_invalidate_pref_groups_cache, sender=model, weak=False)
