from collections.abc import Generator
from uuid import UUID
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from app.db import Base, get_db
from app.main import app
from app.models import FileAsset

@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    def override() -> Generator[Session, None, None]:
        with factory() as session:
            yield session
    app.dependency_overrides[get_db] = override
    app.state.test_session_factory = factory
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    del app.state.test_session_factory

def asset_id(client: TestClient) -> str:
    with client.app.state.test_session_factory() as session:
        asset = FileAsset(original_name='bag.svg', storage_key='bag.svg', content_type='image/svg+xml', size_bytes=10)
        session.add(asset); session.commit()
        return str(asset.id)

def setup_catalog(client: TestClient) -> tuple[str, str]:
    asset = asset_id(client)
    category = client.post('/api/pattern-categories', json={'name': '花植'}).json()
    pattern = client.post('/api/patterns', json={'category_id': category['id'], 'name': '花朵', 'production_code': 'FLOWER-1', 'status': 'published', 'image_asset_id': asset, 'width_mm': 42, 'height_mm': 42, 'price_cents': 1200}).json()
    version = client.get(f"/api/patterns/{pattern['id']}/versions").json()[0]
    return asset, version['id']

def setup_bag(client: TestClient, asset: str) -> str:
    bag = client.post('/api/bags', json={'name': '托特包', 'image_asset_id': asset, 'width_mm': 280, 'height_mm': 220, 'base_price_cents': 15900, 'status': 'published'}).json()
    response = client.post(f"/api/bags/{bag['id']}/embroidery-area", json={'relative_x': .2, 'relative_y': .2, 'relative_width': .6, 'relative_height': .5, 'width_mm': 180, 'height_mm': 120})
    assert response.status_code == 200
    return bag['id']

def test_create_bag(client: TestClient) -> None:
    bag_id = setup_bag(client, asset_id(client))
    assert UUID(bag_id)

def test_create_pattern_generates_version(client: TestClient) -> None:
    _, version_id = setup_catalog(client)
    assert UUID(version_id)

def test_save_design_and_server_calculates_price(client: TestClient) -> None:
    asset, version = setup_catalog(client); bag = setup_bag(client, asset)
    response = client.post('/api/designs', json={'bag_id': bag, 'items': [{'pattern_version_id': version, 'center_x_ratio': .5, 'center_y_ratio': .5}]})
    assert response.status_code == 200
    assert response.json()['total_price_cents'] == 17100

def test_rejects_out_of_bounds_and_client_size_tampering(client: TestClient) -> None:
    asset, version = setup_catalog(client); bag = setup_bag(client, asset)
    invalid = client.post('/api/designs', json={'bag_id': bag, 'items': [{'pattern_version_id': version, 'center_x_ratio': 0, 'center_y_ratio': .5}]})
    assert invalid.status_code == 422
    tampered = client.post('/api/designs', json={'bag_id': bag, 'items': [{'pattern_version_id': version, 'center_x_ratio': .5, 'center_y_ratio': .5, 'width_mm': 999}]})
    assert tampered.status_code == 422
