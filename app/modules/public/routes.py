import logging

from flask import render_template, request

from app.modules.dataset.services import DataSetService
from app.modules.featuremodel.services import FeatureModelService
from app.modules.public import public_bp
from app.modules.community.models import CommunityUser

logger = logging.getLogger(__name__)


@public_bp.route("/")
def index():
    logger.info("Access index")
    dataset_service = DataSetService()
    feature_model_service = FeatureModelService()

    # Statistics: total datasets and feature models
    datasets_counter = dataset_service.count_synchronized_datasets()
    feature_models_counter = feature_model_service.count_feature_models()

    # Statistics: total downloads
    total_dataset_downloads = dataset_service.total_dataset_downloads()
    total_feature_model_downloads = feature_model_service.total_feature_model_downloads()

    # Statistics: total views
    total_dataset_views = dataset_service.total_dataset_views()
    total_feature_model_views = feature_model_service.total_feature_model_views()

    # Trending datasets (trending=week|month)
    selected_trending = request.args.get("trending", "week")
    # Fetch top 3 for week and month
    trending_week = dataset_service.get_trending_datasets_for_api(period="week", limit=3, metric="downloads")
    trending_month = dataset_service.get_trending_datasets_for_api(period="month", limit=3, metric="downloads")

    datasets_list = dataset_service.latest_synchronized()

    # Build a mapping dataset_id -> community name (if uploader belongs to a community)
    dataset_communities = {}
    try:
        for ds in datasets_list:
            cu = CommunityUser.query.filter_by(user_id=ds.user_id).first()
            if cu and getattr(cu, "community", None):
                dataset_communities[ds.id] = cu.community.name
            else:
                dataset_communities[ds.id] = None
    except Exception:
        dataset_communities = {}

    return render_template(
        "public/index.html",
        datasets=datasets_list,
        datasets_counter=datasets_counter,
        feature_models_counter=feature_models_counter,
        total_dataset_downloads=total_dataset_downloads,
        total_feature_model_downloads=total_feature_model_downloads,
        total_dataset_views=total_dataset_views,
        total_feature_model_views=total_feature_model_views,
        trending_week=trending_week,
        trending_month=trending_month,
        selected_trending=selected_trending,
        dataset_communities=dataset_communities,
    )
