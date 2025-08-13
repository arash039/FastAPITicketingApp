def test_client_not_found_specific_ticet(test_client):
	request = test_client.get("/ticket/1")
	assert request.status_code == 404
	assert request.json() == {
        "detail": "ticket not found"
    }

def test_client_create_ticket(test_client):
	request = test_client.post(
		"/ticket",
		json={
			"price": 100.0,
			"show": "test show",
			"user": "test user"
		}
	)

	assert request.status_code == 200
	assert request.json() == {"ticket_id": 1}

def test_client_get_ticket(test_client, add_single_ticket):
	request = test_client.get("/ticket/1234")

	assert request.status_code == 200
	assert request.json() == {
        "id": 1234,
		"show": "another show",
		"user": "test user",
		"price": 1000
    }

def test_client_update_ticket_price(test_client, add_single_ticket):
	request = test_client.put("/ticket/1234/price/250")

	assert request.status_code == 200
	assert request.json() == {"detail": "ticket price updated"}

def test_client_delete_ticket(test_client, add_single_ticket):
	request = test_client.delete("/ticket/1234")

	assert request.status_code == 200
	assert request.json() == {"detail": "ticket removed"}

	request = test_client.delete("/ticket/1234")
	assert request.status_code == 404
	assert request.json() == {"detail": "ticket not found"}