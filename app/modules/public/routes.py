import logging

from flask import render_template, request

from app.modules.dataset.services import DataSetService
from app.modules.compmodel.services import CompModelService
from app.modules.public import public_bp

logger = logging.getLogger(__name__)


@public_bp.route("/")
def index():
    logger.info("Access index")
    dataset_service = DataSetService()
    comp_model_service = CompModelService()

    # Statistics: total datasets and comp models
    datasets_counter = dataset_service.count_synchronized_datasets()
    comp_models_counter = comp_model_service.count_comp_models()

    # Statistics: total downloads
    total_dataset_downloads = dataset_service.total_dataset_downloads()
    total_comp_model_downloads = comp_model_service.total_comp_model_downloads()

    # Statistics: total views
    total_dataset_views = dataset_service.total_dataset_views()
    total_comp_model_views = comp_model_service.total_comp_model_views()

    # Trending datasets (trending=week|month)
    selected_trending = request.args.get("trending", "week")
    # Fetch top 3 for week and month
    trending_week = dataset_service.get_trending_datasets_for_api(period="week", limit=3, metric="downloads")
    trending_month = dataset_service.get_trending_datasets_for_api(period="month", limit=3, metric="downloads")

    return render_template(
        "public/index.html",
        datasets=dataset_service.latest_synchronized(),
        datasets_counter=datasets_counter,
        comp_models_counter=comp_models_counter,
        total_dataset_downloads=total_dataset_downloads,
        total_comp_model_downloads=total_comp_model_downloads,
        total_dataset_views=total_dataset_views,
        total_comp_model_views=total_comp_model_views,
        trending_week=trending_week,
        trending_month=trending_month,
        selected_trending=selected_trending,
    )
