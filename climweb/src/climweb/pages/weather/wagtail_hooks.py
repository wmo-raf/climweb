from wagtail import hooks
from wagtailcache.cache import clear_cache


@hooks.register("after_generate_forecast")
def after_generate_forecast(created_forecast_pks):
    clear_cache()


@hooks.register("after_clear_old_forecasts")
def after_clear_old_forecasts():
    clear_cache()


@hooks.register("after_forecast_add_from_form")
def after_forecast_add_from_form():
    clear_cache()
