from django.db import models

from base.utils import dict_to_choices

CHECKPOINTS = {
    "init": "Initializing",
    "build": "Build",
    "env_update": "Env File Update",
    "recreate": "Restart",
}


class VersionUpgradeStatus(models.Model):
    previous_version = models.CharField(max_length=100)
    new_version = models.CharField(max_length=100)
    checkpoint = models.CharField(max_length=100, choices=dict_to_choices(CHECKPOINTS))
    success = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Version Upgrade Status"

    def __str__(self):
        return f"From {self.previous_version} > {self.new_version}"
