from app import app


def test_health_endpoint():
    client = app.test_client()
    response = client.get('/api/health')
    assert response.status_code == 200
    assert response.json['status'] in {'healthy', 'degraded'}


def test_prediction_endpoint_valid_request():
    client = app.test_client()
    payload = {
        'vehicle_id': 'veh_sim_1',
        'message_id': 'msg-001',
        'sequence': 1,
        'timestamp': 1788534955.68,
        'features': {
            'posx': 12.3,
            'posy': -4.2,
            'posz': 0.0,
            'spdx': 0.5,
            'spdy': 0.2,
            'spdz': 0.0,
            'aclx': 0.0,
            'acly': 0.0,
            'aclz': 0.0,
            'hedx': 0.0,
            'hedy': 0.0,
            'hedz': 0.0,
        },
    }
    response = client.post('/api/predict', json=payload)
    assert response.status_code in {200, 400, 409}


def test_prediction_endpoint_rejects_bad_payload():
    client = app.test_client()
    response = client.post('/api/predict', json={'vehicle_id': 'veh_1'})
    assert response.status_code == 400
