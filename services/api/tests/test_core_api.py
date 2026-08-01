from collections.abc import Generator
from io import BytesIO
from uuid import UUID
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from app.db import Base, get_db
from app.main import app
from app.models import FileAsset
from app.services.storage import StorageService

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

def setup_catalog(client: TestClient, asset: str | None = None) -> tuple[str, str]:
    asset = asset or asset_id(client)
    category = client.post('/api/pattern-categories', json={'name': '花植'}).json()
    pattern = client.post('/api/patterns', json={'category_id': category['id'], 'name': '花朵', 'production_code': 'FLOWER-1', 'status': 'published', 'image_asset_id': asset, 'width_mm': 42, 'height_mm': 42, 'price_cents': 1200}).json()
    version = client.get(f"/api/patterns/{pattern['id']}/versions").json()[0]
    return asset, version['id']

def image_asset_id(client: TestClient) -> str:
    from PIL import Image
    image = Image.new('RGBA', (400, 400), (245, 235, 220, 255))
    content = BytesIO(); image.save(content, 'PNG')
    key, size = StorageService().save_bytes(content.getvalue())
    with client.app.state.test_session_factory() as session:
        asset = FileAsset(original_name='source.png', storage_key=key, content_type='image/png', size_bytes=size)
        session.add(asset); session.commit()
        return str(asset.id)

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

def test_delete_design_for_own_client(client: TestClient) -> None:
    asset, version = setup_catalog(client); bag = setup_bag(client, asset)
    created = client.post('/api/designs', json={'bag_id': bag, 'client_key': 'test-client-key', 'items': [{'pattern_version_id': version, 'center_x_ratio': .5, 'center_y_ratio': .5}]}).json()
    deleted = client.delete(f"/api/designs/{created['id']}?client_key=test-client-key")
    assert deleted.status_code == 204

def test_lists_saved_designs_for_its_client_only(client: TestClient) -> None:
    asset, version = setup_catalog(client); bag = setup_bag(client, asset)
    client.post('/api/designs', json={'bag_id': bag, 'client_key': 'client-allowed', 'items': [{'pattern_version_id': version, 'center_x_ratio': .5, 'center_y_ratio': .5, 'z_index': 3}]})
    client.post('/api/designs', json={'bag_id': bag, 'client_key': 'client-private', 'items': [{'pattern_version_id': version, 'center_x_ratio': .5, 'center_y_ratio': .5}]})
    designs = client.get('/api/designs?client_key=client-allowed')
    assert designs.status_code == 200
    assert len(designs.json()) == 1
    assert designs.json()[0]['items'][0]['z_index'] == 3

def test_cart_keeps_each_design_as_a_separate_item(client: TestClient) -> None:
    asset, version = setup_catalog(client); bag = setup_bag(client, asset)
    created = client.post('/api/designs', json={'bag_id': bag, 'client_key': 'cart-client', 'items': [{'pattern_version_id': version, 'center_x_ratio': .5, 'center_y_ratio': .5}]}).json()
    first = client.post('/api/cart-items', json={'design_id': created['id'], 'client_key': 'cart-client'}).json()
    second = client.post('/api/cart-items', json={'design_id': created['id'], 'client_key': 'cart-client'}).json()
    listed = client.get('/api/cart-items?client_key=cart-client')
    assert listed.status_code == 200 and len(listed.json()) == 2
    assert first['id'] != second['id']
    assert client.delete(f"/api/cart-items/{first['id']}?client_key=cart-client").status_code == 204
    assert len(client.get('/api/cart-items?client_key=cart-client').json()) == 1
    assert client.delete(f"/api/designs/{created['id']}?client_key=cart-client").status_code == 409

def test_order_uses_immutable_snapshot_recalculated_price_and_mock_payment(client: TestClient) -> None:
    asset, version = setup_catalog(client); bag = setup_bag(client, asset)
    design = client.post('/api/designs', json={
        'bag_id': bag, 'client_key': 'test-client-key',
        'items': [{'pattern_version_id': version, 'center_x_ratio': .5, 'center_y_ratio': .5, 'rotation_degrees': 15, 'z_index': 2}],
    }).json()
    order_response = client.post('/api/orders', json={'design_id': design['id'], 'client_key': 'test-client-key'})
    assert order_response.status_code == 200
    order = order_response.json()
    assert order['status'] == 'PENDING_PAYMENT'
    assert order['total_price_cents'] == 17100
    with client.app.state.test_session_factory() as session:
        from app.models import Bag, Order
        saved_order = session.get(Order, UUID(order['id']))
        assert saved_order.snapshot['bag']['price_cents'] == 15900
        session.get(Bag, UUID(bag)).base_price_cents = 99999
        session.commit()
        assert saved_order.snapshot['items'][0]['rotation_degrees'] == 15
    paid = client.post(f"/api/orders/{order['id']}/mock-pay?client_key=test-client-key")
    assert paid.status_code == 200
    assert paid.json()['status'] == 'PAID'
    assert client.post(f"/api/orders/{order['id']}/mock-pay?client_key=test-client-key").status_code == 409
    assert client.post(f"/api/admin/orders/{order['id']}/status", json={'status': 'TO_PRODUCE'}).json()['status'] == 'TO_PRODUCE'
    assert client.post(f"/api/admin/orders/{order['id']}/status", json={'status': 'PRODUCING'}).json()['status'] == 'PRODUCING'
    assert client.post(f"/api/admin/orders/{order['id']}/status", json={'status': 'SHIPPED'}).status_code == 422
    shipped = client.post(f"/api/admin/orders/{order['id']}/status", json={'status': 'SHIPPED', 'tracking_no': 'SF123'})
    assert shipped.json()['tracking_no'] == 'SF123'
    assert client.post(f"/api/admin/orders/{order['id']}/status", json={'status': 'COMPLETED'}).json()['status'] == 'COMPLETED'

def test_preview_and_paid_production_image_are_rendered_with_correct_visibility(client: TestClient) -> None:
    asset, version = setup_catalog(client, image_asset_id(client)); bag = setup_bag(client, asset)
    design = client.post('/api/designs', json={'bag_id': bag, 'client_key': 'render-client', 'items': [{'pattern_version_id': version, 'center_x_ratio': .5, 'center_y_ratio': .5}]}).json()
    preview = client.post(f"/api/designs/{design['id']}/preview?client_key=render-client")
    assert preview.status_code == 200
    assert client.get(preview.json()['url']).status_code == 200
    order = client.post('/api/orders', json={'design_id': design['id'], 'client_key': 'render-client'}).json()
    assert client.get(f"/api/admin/orders/{order['id']}/production-image").status_code == 409
    assert client.post(f"/api/orders/{order['id']}/mock-pay?client_key=render-client").status_code == 200
    production = client.get(f"/api/admin/orders/{order['id']}/production-image")
    assert production.status_code == 200
    with client.app.state.test_session_factory() as session:
        from app.models import Order
        production_asset_id = session.get(Order, UUID(order['id'])).snapshot['production_asset_id']
        asset_record = session.get(FileAsset, UUID(production_asset_id))
        assert asset_record.visibility == 'private'
        assert client.get(f'/api/files/{asset_record.storage_key}').status_code == 404
